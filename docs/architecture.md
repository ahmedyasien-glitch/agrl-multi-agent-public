# AGRL Multi-Agent Research Business V2

## Production data path

Neon PostgreSQL (`DATABASE_URL`) is the production database. SQLite is used only as a local fallback when `DATABASE_URL` is absent.

## Workflow

Lead Discovery → Website/Research Audit → Qualification → Offer → Proposal → Human Approval → Client → GIS Production → QA → Delivery → Revenue Tracking

## Agent path

Scout → Qualifier → Evidence Auditor → Offer Strategist → {GIS Brief + Proposal + Outreach} → Production Planner → QA → Manager → Human Gate

## Side-effect policy

Agents produce recommendations and drafts. They do not send email, move money, place trades, or publish deliverables automatically.
