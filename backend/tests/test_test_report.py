"""Tests for the Test Report Agent: analysis, service, and PDF export."""

from __future__ import annotations

from app.modules.test_report import analysis, pdf, service


def test_statistics_computed(sample_csv_bytes):
    df = analysis.load_dataframe(".csv", sample_csv_bytes)
    stats = analysis.compute_statistics(df)
    names = {s.name for s in stats}
    assert {"voltage", "current", "temperature"}.issubset(names)
    voltage = next(s for s in stats if s.name == "voltage")
    assert voltage.mean is not None


def test_anomaly_detection_flags_injected_outlier(sample_csv_bytes):
    df = analysis.load_dataframe(".csv", sample_csv_bytes)
    anomalies = analysis.detect_anomalies(df)
    flagged = {a.column for a in anomalies}
    # We injected extreme voltage and temperature values at row 25.
    assert "voltage" in flagged or "temperature" in flagged


def test_charts_render_base64(sample_csv_bytes):
    df = analysis.load_dataframe(".csv", sample_csv_bytes)
    charts = analysis.render_charts(df)
    assert charts
    assert all(c.image_base64 for c in charts)


def test_generate_report_endtoend_with_mock(sample_csv_bytes, mock_provider):
    report = service.generate_report(
        title="Battery Bench Run",
        extension=".csv",
        data=sample_csv_bytes,
        provider=mock_provider,
    )
    assert report.row_count == 50
    assert report.column_count == 4
    assert report.executive_summary
    assert report.conclusions
    assert report.recommendations
    assert report.generated_by == "mock"


def test_pdf_export_produces_pdf_bytes(sample_csv_bytes, mock_provider):
    report = service.generate_report(
        title="Battery Bench Run",
        extension=".csv",
        data=sample_csv_bytes,
        provider=mock_provider,
    )
    pdf_bytes = pdf.build_pdf(report)
    assert pdf_bytes.startswith(b"%PDF")
