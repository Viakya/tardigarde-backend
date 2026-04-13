import json
from datetime import date
from typing import Any

import requests
from flask import current_app
from sqlalchemy import func

from app.core.exceptions import ValidationError
from app.extensions import db
from app.models import FeePayment, Student
from app.services.parent_service import get_child_attendance, get_child_fees, get_child_test_results
from app.services.reporting_service import (
    get_batch_strength_report,
    get_monthly_attendance_percentage,
    get_revenue_by_month,
    get_salary_expense_by_month,
)
from app.services.teacher_dashboard_service import get_batch_students


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
OPENAI_CHAT_COMPLETIONS_PATH = "/chat/completions"


def _resolve_gemini_keys() -> list[str]:
    keys: list[str] = []
    configured = current_app.config.get("GEMINI_API_KEYS") or []
    if isinstance(configured, list):
        keys.extend(str(item).strip() for item in configured if str(item).strip())

    primary = current_app.config.get("GEMINI_API_KEY")
    if primary and primary.strip():
        keys.insert(0, primary.strip())

    # Deduplicate while preserving order.
    return list(dict.fromkeys(keys))


def _extract_gemini_error_detail(response: requests.Response) -> str:
    detail = None
    try:
        error_body = response.json()
        error_obj = error_body.get("error") if isinstance(error_body, dict) else None
        if isinstance(error_obj, dict):
            status = error_obj.get("status")
            message = error_obj.get("message")
            if status and message:
                detail = f"{status}: {message}"
            elif message:
                detail = str(message)
    except ValueError:
        detail = None

    if not detail:
        detail = f"HTTP {response.status_code}"
    return detail


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _try_parse_json(text: str) -> dict[str, Any] | None:
    cleaned = _strip_code_fences(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _coerce_operations_schema(payload: dict[str, Any], fallback_title: str) -> dict[str, Any]:
    headline = payload.get("headline") if isinstance(payload.get("headline"), str) else fallback_title
    summary = payload.get("summary") if isinstance(payload.get("summary"), list) else []
    risks = payload.get("risks") if isinstance(payload.get("risks"), list) else []
    actions = payload.get("actions") if isinstance(payload.get("actions"), list) else []

    normalized_summary = [str(item) for item in summary[:4] if isinstance(item, (str, int, float))]

    normalized_risks: list[dict[str, Any]] = []
    for item in risks:
        if isinstance(item, dict):
            normalized_risks.append(
                {
                    "label": str(item.get("label", "")),
                    "severity": str(item.get("severity", "medium")),
                    "reason": str(item.get("reason", "")),
                }
            )

    normalized_actions: list[dict[str, Any]] = []
    for item in actions:
        if isinstance(item, dict):
            normalized_actions.append(
                {
                    "priority": str(item.get("priority", "P2")),
                    "action": str(item.get("action", "")),
                    "owner": str(item.get("owner", "operations")),
                    "timeframe": str(item.get("timeframe", "this week")),
                }
            )

    return {
        "headline": headline,
        "summary": normalized_summary,
        "risks": normalized_risks,
        "actions": normalized_actions,
    }


def generate_quiz_structure(topic: str, instructions: str | None, difficulty: str, question_count: int) -> dict[str, Any]:
    difficulty = (difficulty or "medium").strip().lower()
    instructions_text = instructions or ""
    prompt = (
        "You are an assessment generator. Return ONLY valid JSON. "
        "Schema: {\"title\": str, \"difficulty\": str, \"questions\": [" 
        "{\"question\": str, \"options\": [str,str,str,str], \"correct_index\": int, \"explanation\": str}]}. "
        f"Generate {question_count} MCQ questions. Each question must have exactly 4 options. "
        "correct_index must be 0-3. Provide concise explanations. "
        f"Difficulty: {difficulty}. Topic: {topic}. "
        f"Teacher instructions: {instructions_text}"
    )

    def _extract_json_object(text: str) -> dict[str, Any] | None:
        parsed_obj = _try_parse_json(text)
        if parsed_obj is not None:
            return parsed_obj
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            sliced = text[start : end + 1]
            return _try_parse_json(sliced)
        return None

    raw_text = _llm_generate(prompt, expect_json=True)
    parsed = _extract_json_object(raw_text)

    if parsed is None:
        repair_prompt = (
            "Return ONLY JSON. Required schema: {\"title\": str, \"difficulty\": str, \"questions\": [" 
            "{\"question\": str, \"options\": [str,str,str,str], \"correct_index\": int, \"explanation\": str}]}. "
            "No markdown, no commentary.\n"
            f"Input:\n{raw_text}"
        )
        repaired_text = _llm_generate(repair_prompt, expect_json=True)
        parsed = _extract_json_object(repaired_text)

    if parsed is None:
        fallback_prompt = (
            "Return ONLY JSON with keys: title, difficulty, questions. "
            f"Generate exactly {question_count} questions on: {topic}. "
            f"Difficulty: {difficulty}."
        )
        retry_text = _llm_generate(fallback_prompt, expect_json=True)
        parsed = _extract_json_object(retry_text)

    if not parsed:
        raise ValidationError("AI response could not be parsed into JSON", 502)

    if isinstance(parsed, list):
        parsed = {"title": topic, "difficulty": difficulty, "questions": parsed}

    if not isinstance(parsed.get("questions"), list):
        raise ValidationError("AI response missing questions array", 502)

    return parsed


def _attempt_json_repair(raw_text: str, fallback_title: str) -> dict[str, Any] | None:
    repair_prompt = (
        "Convert the following text into valid JSON only. "
        "Return ONLY JSON object with keys: headline, summary, risks, actions. "
        "summary must be array of short strings. risks/actions must be arrays.\n"
        f"Fallback headline: {fallback_title}\n"
        f"Input text:\n{raw_text}"
    )
    repaired_text = _llm_generate(repair_prompt, expect_json=True)
    repaired = _try_parse_json(repaired_text)
    if repaired is None:
        return None
    return _coerce_operations_schema(repaired, fallback_title)


def _gemini_generate(prompt: str) -> str:
    provider = (current_app.config.get("AI_PROVIDER") or "").strip().lower()
    if provider != "gemini":
        raise ValidationError("Only gemini provider is configured right now", 500)

    api_keys = _resolve_gemini_keys()
    if not api_keys:
        raise ValidationError("GEMINI_API_KEY or GEMINI_API_KEYS is missing in backend configuration", 500)

    model = current_app.config.get("AI_MODEL", "gemini-1.5-flash")
    timeout = current_app.config.get("AI_TIMEOUT_SECONDS", 30)
    max_tokens = current_app.config.get("AI_MAX_TOKENS", 1200)
    temperature = current_app.config.get("AI_TEMPERATURE", 0.2)

    url = GEMINI_API_URL.format(model=model)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",
        },
    }

    last_error_detail = "Unknown Gemini API error"
    response = None
    for api_key in api_keys:
        try:
            response = requests.post(url, params={"key": api_key}, json=payload, timeout=timeout)
        except requests.RequestException:
            last_error_detail = "Failed to reach Gemini API"
            continue

        if response.status_code < 400:
            break

        last_error_detail = _extract_gemini_error_detail(response)

    if response is None or response.status_code >= 400:
        raise ValidationError(f"Gemini API error: {last_error_detail}", 502)

    try:
        body = response.json()
    except ValueError as exc:
        raise ValidationError("Gemini API returned invalid JSON response", 502) from exc

    candidates = body.get("candidates") or []
    if not candidates:
        raise ValidationError("Gemini API returned no candidates", 502)

    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "\n".join(str(part.get("text", "")) for part in parts).strip()
    if not text:
        raise ValidationError("Gemini API returned empty content", 502)

    return text


def _openai_generate(prompt: str, expect_json: bool = False) -> str:
    api_key = current_app.config.get("OPENAI_API_KEY")
    if not api_key:
        raise ValidationError("OPENAI_API_KEY is missing in backend configuration", 500)

    base_url = (current_app.config.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = current_app.config.get("AI_MODEL", "gpt-4.1-mini")
    timeout = current_app.config.get("AI_TIMEOUT_SECONDS", 30)
    max_tokens = current_app.config.get("AI_MAX_TOKENS", 1200)
    temperature = current_app.config.get("AI_TEMPERATURE", 0.2)

    url = f"{base_url}{OPENAI_CHAT_COMPLETIONS_PATH}"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict JSON assistant. Always return valid JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if expect_json:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise ValidationError("Failed to reach OpenAI API", 502) from exc

    if response.status_code >= 400:
        detail = None
        try:
            error_body = response.json()
            error_obj = error_body.get("error") if isinstance(error_body, dict) else None
            if isinstance(error_obj, dict):
                message = error_obj.get("message")
                code = error_obj.get("code")
                if code and message:
                    detail = f"{code}: {message}"
                elif message:
                    detail = str(message)
        except ValueError:
            detail = None

        if not detail:
            detail = f"HTTP {response.status_code}"

        raise ValidationError(f"OpenAI API error: {detail}", 502)

    try:
        body = response.json()
    except ValueError as exc:
        raise ValidationError("OpenAI API returned invalid JSON response", 502) from exc

    choices = body.get("choices") or []
    if not choices:
        raise ValidationError("OpenAI API returned no choices", 502)

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    text = (message or {}).get("content") if isinstance(message, dict) else None
    if not isinstance(text, str) or not text.strip():
        raise ValidationError("OpenAI API returned empty content", 502)

    return text.strip()


def _llm_generate(prompt: str, expect_json: bool = False) -> str:
    provider = (current_app.config.get("AI_PROVIDER") or "").strip().lower()
    if provider == "gemini":
        return _gemini_generate(prompt)
    if provider == "openai":
        return _openai_generate(prompt, expect_json=expect_json)
    raise ValidationError("Unsupported AI_PROVIDER. Use gemini or openai", 500)


def _generate_structured_json(prompt: str, fallback_title: str) -> dict[str, Any]:
    raw_text = _llm_generate(prompt, expect_json=True)
    parsed = _try_parse_json(raw_text)
    if parsed is not None:
        return _coerce_operations_schema(parsed, fallback_title)

    # Try extracting a JSON object slice if extra text/noise exists.
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        sliced = raw_text[start : end + 1]
        sliced_parsed = _try_parse_json(sliced)
        if sliced_parsed is not None:
            return _coerce_operations_schema(sliced_parsed, fallback_title)

    repaired = _attempt_json_repair(raw_text, fallback_title)
    if repaired is not None:
        return repaired

    return {
        "headline": fallback_title,
        "summary": ["AI response could not be parsed into structured format."],
        "risks": [],
        "actions": [],
    }


def _force_operations_risks_actions(context: dict[str, Any], insights: dict[str, Any]) -> dict[str, Any]:
    attendance_rows = ((context.get("attendance") or {}).get("monthly_attendance") or [])
    revenue_rows = ((context.get("revenue") or {}).get("monthly_revenue") or [])
    salary_rows = ((context.get("salary") or {}).get("monthly_salary_expense") or [])

    avg_attendance = 0.0
    if attendance_rows:
        avg_attendance = sum(float(row.get("attendance_percentage") or 0) for row in attendance_rows) / len(attendance_rows)

    total_revenue = sum(float(row.get("revenue") or 0) for row in revenue_rows)
    total_salary_paid = sum(float(row.get("total_paid") or 0) for row in salary_rows)

    risks = insights.get("risks") if isinstance(insights.get("risks"), list) else []
    actions = insights.get("actions") if isinstance(insights.get("actions"), list) else []

    if not risks:
        auto_risks: list[dict[str, Any]] = []
        if avg_attendance < 60:
            auto_risks.append(
                {
                    "label": "Low attendance trend",
                    "severity": "high",
                    "reason": f"Average attendance is {avg_attendance:.1f}% which is below acceptable threshold.",
                }
            )
        elif avg_attendance < 75:
            auto_risks.append(
                {
                    "label": "Attendance performance risk",
                    "severity": "medium",
                    "reason": f"Average attendance is {avg_attendance:.1f}% and may hurt academic outcomes.",
                }
            )

        if total_revenue <= 0:
            auto_risks.append(
                {
                    "label": "Revenue generation risk",
                    "severity": "high",
                    "reason": "No fee revenue recorded for the selected period.",
                }
            )

        if total_salary_paid > 0 and total_revenue < total_salary_paid:
            auto_risks.append(
                {
                    "label": "Cashflow pressure",
                    "severity": "high",
                    "reason": "Salary outflow exceeds fee inflow in the selected period.",
                }
            )

        if not auto_risks:
            auto_risks.append(
                {
                    "label": "Operational monitoring",
                    "severity": "low",
                    "reason": "No critical numerical risk detected, continue monitoring weekly.",
                }
            )

        insights["risks"] = auto_risks

    if not actions:
        top_risk = (insights.get("risks") or [{}])[0]
        risk_label = str(top_risk.get("label") or "Operational risk")
        insights["actions"] = [
            {
                "priority": "P1",
                "action": f"Start a 7-day intervention plan for: {risk_label}.",
                "owner": "operations",
                "timeframe": "within 48 hours",
            },
            {
                "priority": "P2",
                "action": "Review fee collections and follow up with pending accounts batch-wise.",
                "owner": "operations",
                "timeframe": "this week",
            },
            {
                "priority": "P2",
                "action": "Run attendance recovery actions with coaches for low-performing batches.",
                "owner": "operations",
                "timeframe": "next 7 days",
            },
        ]

    return insights


def _force_coach_groups_actions(context: dict[str, Any], insights: dict[str, Any]) -> dict[str, Any]:
    headline = str(insights.get("headline") or "Coach Batch Insights")
    summary = insights.get("summary") if isinstance(insights.get("summary"), list) else []
    summary = [str(item) for item in summary if isinstance(item, (str, int, float))][:4]

    groups = insights.get("groups") if isinstance(insights.get("groups"), list) else []
    actions = insights.get("actions") if isinstance(insights.get("actions"), list) else []

    at_risk_count = len(context.get("at_risk_students") or [])
    strong_count = len(context.get("strong_students") or [])
    total_students = int(context.get("total_students") or 0)

    if not summary:
        summary = [
            f"Batch has {total_students} students in scope.",
            f"At-risk students identified: {at_risk_count}.",
            f"Strong-performing students identified: {strong_count}.",
        ]

    if not groups:
        groups = [
            {
                "name": "At-risk learners",
                "criteria": "Attendance < 75 or average score < 55",
                "count": at_risk_count,
            },
            {
                "name": "Strong performers",
                "criteria": "Attendance >= 85 and average score >= 70",
                "count": strong_count,
            },
        ]

    if not actions:
        actions = [
            {
                "priority": "P1",
                "action": "Run focused remediation plan for at-risk students with daily tracking.",
                "owner": "coach",
                "timeframe": "next 7 days",
            },
            {
                "priority": "P2",
                "action": "Call guardians of low-attendance students and set attendance commitments.",
                "owner": "coach",
                "timeframe": "within 72 hours",
            },
            {
                "priority": "P2",
                "action": "Assign challenge sets to strong performers to sustain momentum.",
                "owner": "coach",
                "timeframe": "this week",
            },
        ]

    return {
        "headline": headline,
        "summary": summary,
        "groups": groups,
        "actions": actions,
    }


def _force_parent_alerts_next_steps(context: dict[str, Any], insights: dict[str, Any]) -> dict[str, Any]:
    headline = str(insights.get("headline") or "Parent Child Progress Summary")

    child_snapshot = insights.get("child_snapshot") if isinstance(insights.get("child_snapshot"), list) else []
    if not child_snapshot and isinstance(insights.get("summary"), list):
        child_snapshot = insights.get("summary") or []
    child_snapshot = [str(item) for item in child_snapshot if isinstance(item, (str, int, float))][:4]

    alerts = insights.get("alerts") if isinstance(insights.get("alerts"), list) else []
    if not alerts and isinstance(insights.get("risks"), list):
        alerts = insights.get("risks") or []

    next_steps = insights.get("next_steps") if isinstance(insights.get("next_steps"), list) else []
    if not next_steps and isinstance(insights.get("actions"), list):
        next_steps = insights.get("actions") or []

    attendance_rate = float(((context.get("attendance") or {}).get("attendance_rate") or 0))
    avg_score = float(((context.get("tests") or {}).get("average_percentage") or 0))
    remaining_fee = float(((context.get("fees") or {}).get("remaining") or 0))

    if not child_snapshot:
        child_snapshot = [
            f"Attendance rate is {attendance_rate:.1f}% in the selected window.",
            f"Average test percentage is {avg_score:.1f}%.",
            f"Pending fee amount is Rs {remaining_fee:.0f}.",
        ]

    if not alerts:
        alerts = []
        if attendance_rate < 70:
            alerts.append(
                {
                    "label": "Attendance concern",
                    "severity": "high",
                    "reason": f"Attendance is {attendance_rate:.1f}%, below healthy benchmark.",
                }
            )
        if avg_score < 60:
            alerts.append(
                {
                    "label": "Academic performance risk",
                    "severity": "medium",
                    "reason": f"Average score is {avg_score:.1f}%, improvement support is needed.",
                }
            )
        if remaining_fee > 0:
            alerts.append(
                {
                    "label": "Fee pending",
                    "severity": "medium",
                    "reason": f"Outstanding fee is Rs {remaining_fee:.0f}.",
                }
            )
        if not alerts:
            alerts.append(
                {
                    "label": "Stable progress",
                    "severity": "low",
                    "reason": "No immediate risk found; continue current routine.",
                }
            )

    if not next_steps:
        next_steps = [
            {
                "priority": "P1",
                "action": "Set weekly study and attendance target with your child and review every Sunday.",
                "owner": "parent",
                "timeframe": "this week",
            },
            {
                "priority": "P2",
                "action": "Coordinate with coach on weak topics and monitor daily revision completion.",
                "owner": "parent",
                "timeframe": "next 7 days",
            },
            {
                "priority": "P2",
                "action": "Clear pending fee as per plan to avoid disruptions.",
                "owner": "parent",
                "timeframe": "before due date",
            },
        ]

    return {
        "headline": headline,
        "child_snapshot": child_snapshot,
        "alerts": alerts,
        "next_steps": next_steps,
    }


def _force_fee_risk_output(context: dict[str, Any], insights: dict[str, Any]) -> dict[str, Any]:
    headline = str(insights.get("headline") or "Fee Risk Prediction")
    summary = insights.get("summary") if isinstance(insights.get("summary"), list) else []
    risks = insights.get("risks") if isinstance(insights.get("risks"), list) else []
    actions = insights.get("actions") if isinstance(insights.get("actions"), list) else []

    summary = [str(item) for item in summary if isinstance(item, (str, int, float))][:4]

    risky_students = context.get("risky_students") or []
    high_risk = len([row for row in risky_students if row.get("risk_level") == "high"])
    medium_risk = len([row for row in risky_students if row.get("risk_level") == "medium"])
    total_outstanding = float(context.get("total_outstanding") or 0)

    if not summary:
        summary = [
            f"High-risk students: {high_risk}.",
            f"Medium-risk students: {medium_risk}.",
            f"Total outstanding at risk: Rs {total_outstanding:.0f}.",
        ]

    if not risks:
        risks = [
            {
                "label": "Fee collection delay",
                "severity": "high" if high_risk > 0 else "medium",
                "reason": f"{high_risk + medium_risk} students currently need proactive collection follow-up.",
            }
        ]

    if not actions:
        actions = [
            {
                "priority": "P1",
                "action": "Call high-risk families within 48 hours and lock payment commitments.",
                "owner": "operations",
                "timeframe": "next 2 days",
            },
            {
                "priority": "P2",
                "action": "Share structured reminder schedule for medium-risk accounts.",
                "owner": "operations",
                "timeframe": "this week",
            },
            {
                "priority": "P2",
                "action": "Review discount and installment plans for repeat delayed payments.",
                "owner": "management",
                "timeframe": "next 7 days",
            },
        ]

    return {
        "headline": headline,
        "summary": summary,
        "risks": risks,
        "actions": actions,
        "risky_students": risky_students,
    }


def get_operations_ai_summary(year: int | None, batch_id: int | None, focus: str | None = None) -> dict[str, Any]:
    context = {
        "year": year,
        "batch_id": batch_id,
        "attendance": get_monthly_attendance_percentage(year=year, batch_id=batch_id),
        "revenue": get_revenue_by_month(year=year),
        "salary": get_salary_expense_by_month(year=year),
        "batch_strength": get_batch_strength_report(include_inactive_students=True),
    }

    prompt = (
        "You are an operations analyst for a coaching institute. "
        "Analyze the provided JSON context and produce concise, practical insights.\n"
        "Return ONLY valid JSON with this schema:\n"
        "{\n"
        '  "headline": "string",\n'
        '  "summary": ["string", "string"],\n'
        '  "risks": [{"label": "string", "severity": "low|medium|high", "reason": "string"}],\n'
        '  "actions": [{"priority": "P1|P2|P3", "action": "string", "owner": "operations", "timeframe": "string"}]\n'
        "}\n"
        "Keep summary and actions specific to coaching business outcomes.\n"
        f"Focus: {focus or 'overall performance, risk control, and cashflow quality'}\n"
        f"Context JSON:\n{json.dumps(context, default=str)}"
    )

    insights = _generate_structured_json(prompt, "Operations AI Summary")
    insights = _force_operations_risks_actions(context, insights)
    return {
        "meta": {"year": year, "batch_id": batch_id, "focus": focus},
        "insights": insights,
    }


def get_coach_batch_ai_insights(user_id: int, batch_id: int, focus: str | None = None) -> dict[str, Any]:
    batch_data = get_batch_students(user_id, batch_id)
    students = batch_data.get("students") or []

    at_risk = [
        {
            "student_id": s.get("id"),
            "name": s.get("full_name"),
            "attendance_rate": s.get("attendance_rate"),
            "avg_test_score": s.get("avg_test_score"),
        }
        for s in students
        if (s.get("attendance_rate") or 0) < 75 or (s.get("avg_test_score") or 0) < 55
    ]

    strong = [
        {
            "student_id": s.get("id"),
            "name": s.get("full_name"),
            "attendance_rate": s.get("attendance_rate"),
            "avg_test_score": s.get("avg_test_score"),
        }
        for s in students
        if (s.get("attendance_rate") or 0) >= 85 and (s.get("avg_test_score") or 0) >= 70
    ]

    context = {
        "batch": batch_data.get("batch") or {},
        "total_students": batch_data.get("total_students", len(students)),
        "at_risk_students": at_risk[:25],
        "strong_students": strong[:25],
    }

    prompt = (
        "You are an academic coach copilot. Use the batch context to create targeted intervention guidance.\n"
        "Return ONLY valid JSON with schema:\n"
        "{\n"
        '  "headline": "string",\n'
        '  "summary": ["string", "string"],\n'
        '  "groups": [{"name": "string", "criteria": "string", "count": 0}],\n'
        '  "actions": [{"priority": "P1|P2|P3", "action": "string", "owner": "coach", "timeframe": "string"}]\n'
        "}\n"
        "Make actions realistic for next 7-14 days.\n"
        f"Focus: {focus or 'attendance recovery and marks improvement'}\n"
        f"Context JSON:\n{json.dumps(context, default=str)}"
    )

    insights = _generate_structured_json(prompt, "Coach Batch Insights")
    insights = _force_coach_groups_actions(context, insights)
    return {
        "meta": {"batch_id": batch_id, "focus": focus},
        "insights": insights,
    }


def get_parent_child_ai_summary(
    parent_user_id: int,
    student_id: int,
    focus: str | None = None,
    attendance_days: int = 45,
) -> dict[str, Any]:
    attendance = get_child_attendance(parent_user_id, student_id, days=attendance_days)
    tests = get_child_test_results(parent_user_id, student_id)
    fees = get_child_fees(parent_user_id, student_id)

    context = {
        "student_id": student_id,
        "student_name": attendance.get("student_name"),
        "attendance": {
            "period_days": attendance.get("period_days"),
            "attendance_rate": attendance.get("attendance_rate"),
            "present": attendance.get("present"),
            "absent": attendance.get("absent"),
            "total_classes": attendance.get("total_classes"),
        },
        "tests": {
            "total_tests": tests.get("total_tests"),
            "average_percentage": tests.get("average_percentage"),
        },
        "fees": {
            "total_fee": fees.get("total_fee"),
            "total_paid": fees.get("total_paid"),
            "remaining": fees.get("remaining"),
            "is_fully_paid": fees.get("is_fully_paid"),
        },
    }

    prompt = (
        "You are a parent engagement assistant for a coaching institute. "
        "Generate clear, supportive, non-technical guidance.\n"
        "Return ONLY valid JSON with schema:\n"
        "{\n"
        '  "headline": "string",\n'
        '  "child_snapshot": ["string", "string"],\n'
        '  "alerts": [{"label": "string", "severity": "low|medium|high", "reason": "string"}],\n'
        '  "next_steps": [{"priority": "P1|P2|P3", "action": "string", "owner": "parent", "timeframe": "string"}]\n'
        "}\n"
        "Use encouraging tone and practical next steps.\n"
        f"Focus: {focus or 'balanced academic progress and routine discipline'}\n"
        f"Context JSON:\n{json.dumps(context, default=str)}"
    )

    insights = _generate_structured_json(prompt, "Parent Child Progress Summary")
    insights = _force_parent_alerts_next_steps(context, insights)
    return {
        "meta": {"student_id": student_id, "focus": focus, "attendance_days": attendance_days},
        "insights": insights,
    }


def get_parent_weekly_digest(parent_user_id: int, student_id: int, focus: str | None = None) -> dict[str, Any]:
    base = get_parent_child_ai_summary(
        parent_user_id=parent_user_id,
        student_id=student_id,
        focus=focus or "weekly progress digest and parent action plan",
        attendance_days=7,
    )

    insights = base.get("insights") or {}
    digest = {
        "headline": insights.get("headline") or "Weekly Parent Digest",
        "week_snapshot": insights.get("child_snapshot") or [],
        "alerts": insights.get("alerts") or [],
        "next_steps": insights.get("next_steps") or [],
    }
    return {
        "meta": {"student_id": student_id, "focus": focus, "period_days": 7},
        "digest": digest,
    }


def _force_quiz_analysis(payload: dict[str, Any], fallback: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    strengths = payload.get("strengths") if isinstance(payload.get("strengths"), list) else []
    weaknesses = payload.get("weaknesses") if isinstance(payload.get("weaknesses"), list) else []
    suggestions = payload.get("suggestions") if isinstance(payload.get("suggestions"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), str) else ""

    strengths = [str(item) for item in strengths[:4] if isinstance(item, (str, int, float))]
    weaknesses = [str(item) for item in weaknesses[:4] if isinstance(item, (str, int, float))]
    suggestions = [str(item) for item in suggestions[:5] if isinstance(item, (str, int, float))]

    if not summary:
        summary = (
            f"You scored {fallback.get('score', 0)} out of {fallback.get('total_marks', 100)} "
            f"with {fallback.get('correct', 0)} correct answers."
        )
    question_feedback = report.get("question_feedback") or []
    wrong_questions = [
        str(item.get("question"))
        for item in question_feedback
        if isinstance(item, dict) and not item.get("is_correct") and item.get("question")
    ]
    correct_answers = int(report.get("correct_answers") or 0)
    total_questions = len(question_feedback) or int(report.get("attempted_answers") or 0)

    if not strengths:
        strengths = []
        if total_questions:
            strengths.append(f"Accuracy snapshot: {correct_answers}/{total_questions} questions correct.")
        if (report.get("attempted_answers") or 0) == total_questions and total_questions:
            strengths.append("You attempted all questions in this test.")
        if not strengths:
            strengths = ["Submission completed successfully."]

    if not weaknesses:
        weaknesses = [f"Mistake area: {question}" for question in wrong_questions[:3]]
        if not weaknesses:
            weaknesses = ["No major weak areas detected in this attempt."]

    if not suggestions:
        suggestions = [
            "Review each incorrect question and write one-line concept notes.",
            "Retake a similar level quiz after revision to improve consistency.",
        ]
        if wrong_questions:
            suggestions.insert(0, "Start with the top incorrect questions listed in Weaknesses.")

    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
    }


def analyze_quiz_submission_report(report: dict[str, Any], focus: str | None = None) -> dict[str, Any]:
    wrong_questions = [
        str(item.get("question"))
        for item in (report.get("question_feedback") or [])
        if isinstance(item, dict) and not item.get("is_correct") and item.get("question")
    ]

    prompt = (
        "You are an academic performance coach. Analyze the quiz report and provide constructive feedback.\n"
        "Return ONLY valid JSON with this schema:\n"
        "{\n"
        '  "summary": "string",\n'
        '  "strengths": ["string"],\n'
        '  "weaknesses": ["string"],\n'
        '  "suggestions": ["string"]\n'
        "}\n"
        "Feedback must be concise, actionable, and student-friendly.\n"
        f"Incorrect question themes: {json.dumps(wrong_questions[:5], default=str)}\n"
        f"Focus: {focus or 'performance improvement and next practice plan'}\n"
        f"Quiz Report JSON:\n{json.dumps(report, default=str)}"
    )

    analysis = _generate_structured_json(prompt, "Quiz Performance Analysis")
    fallback = {
        "score": report.get("score"),
        "total_marks": report.get("total_marks"),
        "correct": report.get("correct_answers"),
    }
    return _force_quiz_analysis(analysis, fallback, report)


def get_fee_risk_prediction(year: int | None = None, focus: str | None = None) -> dict[str, Any]:
    payment_rows = db.session.query(
        FeePayment.student_id.label("student_id"),
        func.coalesce(func.sum(FeePayment.amount), 0).label("total_paid"),
        func.count(FeePayment.id).label("payment_count"),
        func.max(FeePayment.payment_date).label("last_payment_date"),
    ).group_by(FeePayment.student_id).all()

    payment_map = {int(row.student_id): row for row in payment_rows}
    students = Student.query.filter(Student.is_active.is_(True)).all()

    risky_students: list[dict[str, Any]] = []
    for student in students:
        if not student.batch:
            continue

        batch_cost = float(student.batch.batch_cost or 0)
        discount_pct = float(student.discount_percent or 0)
        expected_fee = max(0.0, batch_cost * (1 - discount_pct / 100))
        if expected_fee <= 0:
            continue

        agg = payment_map.get(int(student.id))
        total_paid = float(agg.total_paid) if agg else 0.0
        payment_count = int(agg.payment_count) if agg else 0
        last_payment_date = agg.last_payment_date if agg else None
        outstanding = max(0.0, expected_fee - total_paid)

        if outstanding <= 0:
            continue

        days_since_last_payment = (date.today() - last_payment_date).days if last_payment_date else 999
        outstanding_ratio = outstanding / expected_fee if expected_fee > 0 else 0

        risk_score = 0
        risk_reasons: list[str] = []

        risk_score += 40
        if outstanding_ratio > 0.5:
            risk_score += 25
            risk_reasons.append("More than 50% fee is still pending")
        elif outstanding_ratio > 0.2:
            risk_score += 15
            risk_reasons.append("Significant fee pending amount")

        if days_since_last_payment >= 45:
            risk_score += 20
            risk_reasons.append("No payment activity in last 45 days")
        elif days_since_last_payment >= 30:
            risk_score += 10
            risk_reasons.append("No payment activity in last 30 days")

        if payment_count <= 1:
            risk_score += 10
            risk_reasons.append("Very low payment frequency")

        if expected_fee >= 20000:
            risk_score += 5

        risk_score = min(100, risk_score)
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        risky_students.append(
            {
                "student_id": student.id,
                "student_name": student.user.full_name if student.user else f"Student {student.id}",
                "batch_name": student.batch.batch_name,
                "expected_fee": round(expected_fee, 2),
                "total_paid": round(total_paid, 2),
                "outstanding_amount": round(outstanding, 2),
                "last_payment_date": last_payment_date.isoformat() if last_payment_date else None,
                "payment_count": payment_count,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "reason": "; ".join(risk_reasons) or "Pending dues detected",
            }
        )

    risky_students.sort(key=lambda row: (row["risk_score"], row["outstanding_amount"]), reverse=True)
    risky_students = risky_students[:15]

    context = {
        "year": year,
        "focus": focus,
        "risky_students": risky_students,
        "total_outstanding": sum(float(row.get("outstanding_amount") or 0) for row in risky_students),
        "high_risk_count": len([row for row in risky_students if row.get("risk_level") == "high"]),
        "medium_risk_count": len([row for row in risky_students if row.get("risk_level") == "medium"]),
    }

    prompt = (
        "You are a finance risk analyst for a coaching institute. "
        "Use the context to produce practical fee collection risk insights.\n"
        "Return ONLY valid JSON with schema:\n"
        "{\n"
        '  "headline": "string",\n'
        '  "summary": ["string", "string"],\n'
        '  "risks": [{"label": "string", "severity": "low|medium|high", "reason": "string"}],\n'
        '  "actions": [{"priority": "P1|P2|P3", "action": "string", "owner": "operations", "timeframe": "string"}]\n'
        "}\n"
        f"Focus: {focus or 'high-risk dues and proactive collection plan'}\n"
        f"Context JSON:\n{json.dumps(context, default=str)}"
    )

    insights = _generate_structured_json(prompt, "Fee Risk Prediction")
    insights = _force_fee_risk_output(context, insights)
    return {
        "meta": {"year": year, "focus": focus},
        "insights": insights,
    }
