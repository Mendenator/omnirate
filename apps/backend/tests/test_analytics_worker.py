from datetime import UTC, datetime
from unittest.mock import patch

from app.analytics.export_pipeline import ExportResult
from app.analytics.worker import run_export_job


async def test_run_export_job_prints_each_table_result(capsys):
    results = [
        ExportResult(table="entities", rows_exported=10, watermark=datetime(2026, 9, 1, tzinfo=UTC)),
        ExportResult(table="reviews", rows_exported=25, watermark=datetime(2026, 9, 1, tzinfo=UTC)),
    ]
    with patch("app.analytics.worker.run_export", return_value=results) as mock_run_export:
        await run_export_job({})

    mock_run_export.assert_called_once()
    printed = capsys.readouterr().out
    assert "entities: 10 rows" in printed
    assert "reviews: 25 rows" in printed
