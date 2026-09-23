from unittest.mock import AsyncMock, patch

from app.workers.attendance import run_daily_import, startup


async def test_run_daily_import_delegates_to_import_attendance(worker_db):
    with patch(
        "app.workers.attendance.import_attendance", AsyncMock(return_value={"matched": 3, "unmatched": 1, "total": 4})
    ) as mock_import:
        await run_daily_import({})

    mock_import.assert_awaited_once()


async def test_startup_configures_sentry():
    with patch("app.workers.attendance.configure_sentry") as mock_configure:
        await startup({})

    mock_configure.assert_called_once()
