from app.workers.transparency import run_monthly_report


async def test_run_monthly_report_executes_against_empty_db(db_session, worker_db, capsys):
    await run_monthly_report({})

    printed = capsys.readouterr().out
    assert "Ил тод байдлын тайлан" in printed
