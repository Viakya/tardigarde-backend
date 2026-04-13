def test_ai_ops_summary_valid(client, auth_headers, monkeypatch):
    def _fake_ops_summary(year=None, batch_id=None, focus=None):
        return {
            "headline": "All good",
            "summary": ["Attendance stable"],
            "risks": [],
            "actions": [],
            "inputs": {"year": year, "batch_id": batch_id, "focus": focus},
        }

    monkeypatch.setattr("app.controllers.ai_controller.get_operations_ai_summary", _fake_ops_summary)

    res = client.post(
        "/api/v1/ai/ops-summary",
        headers=auth_headers("director"),
        json={
            "year": 2026,
            "batch_id": 1,
            "focus": "cashflow and attendance",
        }
    )

    assert res.status_code == 200

    data = res.get_json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["headline"] == "All good"


def test_ai_ops_summary_invalid_year(client, auth_headers):
    res = client.post(
        "/api/v1/ai/ops-summary",
        headers=auth_headers("director"),
        json={"year": "not-an-int"}
    )

    assert res.status_code == 400

    data = res.get_json()
    assert data["success"] is False