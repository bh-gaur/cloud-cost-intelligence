"""
Tests for Report Generators and Retention Service
"""

from datetime import date, timedelta
from pathlib import Path
import pytest
from app.reports.generators.csv_generator import CSVReportGenerator
from app.reports.generators.json_generator import JSONReportGenerator
from app.reports.generators.html_generator import HTMLReportGenerator
from app.reports.service import ReportService


@pytest.fixture
def sample_report_data():
    return {
        "generated_at": "2026-09-12 12:00:00 UTC",
        "start_date": "2026-08-12",
        "end_date": "2026-09-12",
        "account_id": "all",
        "total_cost": 45200.50,
        "previous_cost": 42000.00,
        "difference": 3200.50,
        "percentage_change": 7.62,
        "trend": "UP",
        "potential_monthly_savings": 4500.00,
        "services": [
            {"service": "EC2 - Compute", "category": "Compute", "current_cost": 15000.0, "percentage_of_total": 33.18, "trend": "UP"},
        ],
        "accounts": [
            {"account_name": "Production", "account_id": "123456789012", "monthly_cost": 30000.0, "percentage_of_total": 66.37},
        ],
        "recommendations": [
            {
                "rule_id": "OPT-001",
                "rule_name": "EC2 Idle Instances",
                "service": "EC2",
                "resource_id": "i-test",
                "estimated_monthly_savings": 140.0,
                "priority": "HIGH",
                "confidence": "Observed",
                "validation_status": "Requires validation",
                "action_required": "Terminate instance",
            }
        ],
        "anomalies": [],
    }


def test_csv_generator(sample_report_data):
    gen = CSVReportGenerator()
    csv_str = gen.generate(sample_report_data)
    assert "AWS COST INTELLIGENCE EXECUTIVE REPORT" in csv_str
    assert "EC2 - Compute" in csv_str
    assert "$45,200.50" in csv_str


def test_json_generator(sample_report_data):
    gen = JSONReportGenerator()
    json_str = gen.generate(sample_report_data)
    assert '"total_cost": 45200.5' in json_str
    assert '"rule_id": "OPT-001"' in json_str


def test_html_generator(sample_report_data):
    gen = HTMLReportGenerator()
    html_str = gen.generate(sample_report_data)
    assert "<!DOCTYPE html>" in html_str
    assert "AWS Cost Intelligence" in html_str
    assert "$45,200.50" in html_str
    assert "EC2 Idle Instances" in html_str


from app.reports.generators.pdf_generator import PDFReportGenerator


def test_pdf_generator(sample_report_data):
    gen = PDFReportGenerator()
    pdf_bytes = gen.generate(sample_report_data)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 5000


def test_report_service_generation(db_session):
    service = ReportService()
    today = date.today()
    rep = service.generate_report(
        db_session,
        fmt="html",
        start_date=today - timedelta(days=7),
        end_date=today,
    )
    assert rep.status == "COMPLETED"
    assert Path(rep.file_path).is_file()
    assert rep.file_size_bytes > 0


def test_pdf_report_service_generation(db_session):
    service = ReportService()
    today = date.today()
    rep = service.generate_report(
        db_session,
        fmt="pdf",
        start_date=today - timedelta(days=7),
        end_date=today,
    )
    assert rep.status == "COMPLETED"
    assert Path(rep.file_path).is_file()
    assert rep.file_path.endswith(".pdf")
    assert rep.file_size_bytes > 5000

