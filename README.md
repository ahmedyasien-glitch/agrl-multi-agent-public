# AGRL Multi-Agent Research Business V2

A human-supervised multi-agent workflow for research-business support, including lead qualification, research/website audits, proposal drafting, GIS production planning, quality control, delivery tracking, and revenue logging.

## Workflow

Lead Discovery → Audit → Qualification → Offer → Proposal → Human Approval → Client → GIS Production → QA → Delivery → Revenue Tracking

## Privacy

External brand: **AGRL GIS Mapping Support**  
External signature: **A.Y.**

Do not place private academic identity details, credentials, database connection strings, API keys, or client data in source files or outreach templates.

## Secrets

Never hard-code `DATABASE_URL` or `LLM_API_KEY` into source code or Git. For deployment, provide secrets through the hosting platform's secret/environment-variable mechanism.

## Human control

The system does not autonomously send email, move money, or trade financial assets. External actions require human approval.

## Local run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deployment

The app can use PostgreSQL when `DATABASE_URL` is provided. Without it, local development can use the SQLite fallback where supported.
