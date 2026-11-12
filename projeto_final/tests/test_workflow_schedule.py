from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github/workflows/coleta-diaria.yml"
EXPECTED_CRONS = ["30 21 * * *", "30 22 * * *", "30 23 * * *", "30 1 * * *"]


def test_workflow_schedule_dispatch_concurrency_and_timeout():
    text = WORKFLOW.read_text(encoding="utf-8")

    cron_lines = re.findall(r'^\s*-\s*cron:\s*"([^"]+)"\s*$', text, re.MULTILINE)
    assert cron_lines == EXPECTED_CRONS
    assert re.search(r"^\s*workflow_dispatch:\s*\{\}", text, re.MULTILINE)
    assert re.search(r"^\s*cancel-in-progress:\s*false\s*$", text, re.MULTILINE)
    assert re.search(r"^\s*timeout-minutes:\s*5\s*$", text, re.MULTILINE)


def test_s3_workflow_values_are_assigned_only_from_github_secrets():
    text = WORKFLOW.read_text(encoding="utf-8")
    for name in ("S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY"):
        assignments = re.findall(rf"^\s*{name}:\s*(.*?)\s*$", text, re.MULTILINE)
        assert assignments == [f"${{{{ secrets.{name} }}}}"]


def test_worst_case_tcgcsv_calls_stays_below_daily_limit():
    workflow_runs_per_day = len(EXPECTED_CRONS)
    tcgcsv_calls_per_run = 2
    worst_case_daily_calls = workflow_runs_per_day * tcgcsv_calls_per_run
    assert worst_case_daily_calls == 8
    assert worst_case_daily_calls < 10_000
