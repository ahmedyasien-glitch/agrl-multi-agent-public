from app.db import db
from app.workflow import upsert_lead, create_run, save_results
from app.orchestrator import run_pipeline


def main():
    db.init_schema()
    lead = {
        "company_name": "Demo Environmental Consultancy",
        "website": "https://example.org",
        "contact_email": "demo@example.org",
        "industry": "Environmental consulting",
        "service_match": "GIS/cartography",
        "problem_signal": "Need a publication-ready environmental map",
        "mapping_task": "One land-cover change map",
        "city": "Abu Dhabi",
        "country": "UAE",
        "source": "demo",
    }
    lead_id = upsert_lead(lead)
    run_id = create_run(lead_id)
    results = run_pipeline(lead)
    save_results(run_id, lead_id, results)
    for r in results:
        print(r.agent, r.status)
        if r.agent == "Manager":
            print(r.output)


if __name__ == "__main__":
    main()
