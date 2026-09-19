import os
from pathlib import Path

os.environ.pop("DATABASE_URL", None)
os.environ["AGRL_DB_PATH"] = "/tmp/agrl_multi_agent_v2_test.sqlite3"

from app.db import db
from app.workflow import upsert_lead, create_run, save_results, sales_summary
from app.orchestrator import run_pipeline


def test_end_to_end_local_sqlite():
    p = Path("/tmp/agrl_multi_agent_v2_test.sqlite3")
    if p.exists():
        p.unlink()
    db.init_schema()
    lead = {
        "company_name": "Test Environmental Group",
        "website": "https://example.org",
        "contact_email": "test@example.org",
        "industry": "Environmental consulting",
        "service_match": "GIS/cartography",
        "problem_signal": "Needs a publication-ready map",
        "mapping_task": "Land-cover map",
        "city": "Dubai",
        "country": "UAE",
    }
    lead_id = upsert_lead(lead)
    run_id = create_run(lead_id)
    results = run_pipeline(lead)
    save_results(run_id, lead_id, results)
    assert any(r.agent == "Manager" for r in results)
    assert db.fetch_one("SELECT id FROM workflow_runs WHERE run_id=%s", (run_id,))
    assert len(db.fetch_all("SELECT * FROM agent_runs WHERE run_id=%s", (run_id,))) == len(results)
    assert sales_summary()["wins"] == 0
