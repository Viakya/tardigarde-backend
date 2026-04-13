from __future__ import annotations

from datetime import datetime
from io import BytesIO

from flask import request, send_file

from app.services.export_service import (
    build_attendance_csv,
    build_results_excel,
    build_revenue_pdf,
    parse_optional_date,
)


def export_attendance_csv_controller():
    batch_id = request.args.get("batch_id", type=int)
    start_date = parse_optional_date(request.args.get("start_date"), "start_date")
    end_date = parse_optional_date(request.args.get("end_date"), "end_date")

    content = build_attendance_csv(batch_id=batch_id, start_date=start_date, end_date=end_date)
    file_name = f"attendance_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return send_file(
        BytesIO(content),
        as_attachment=True,
        download_name=file_name,
        mimetype="text/csv",
    )


def export_results_excel_controller():
    batch_id = request.args.get("batch_id", type=int)
    start_date = parse_optional_date(request.args.get("start_date"), "start_date")
    end_date = parse_optional_date(request.args.get("end_date"), "end_date")

    content = build_results_excel(batch_id=batch_id, start_date=start_date, end_date=end_date)
    file_name = f"results_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        BytesIO(content),
        as_attachment=True,
        download_name=file_name,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def export_revenue_pdf_controller():
    year = request.args.get("year", type=int)
    content = build_revenue_pdf(year=year)
    suffix = str(year) if year else datetime.utcnow().strftime("%Y")
    file_name = f"revenue_report_{suffix}.pdf"

    return send_file(
        BytesIO(content),
        as_attachment=True,
        download_name=file_name,
        mimetype="application/pdf",
    )
