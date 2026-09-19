# Production checklist

- [ ] Rotate Neon password and issue a fresh DATABASE_URL.
- [ ] Add DATABASE_URL to Streamlit Cloud Secrets (not source code).
- [ ] Add LLM_API_KEY only as a secret if LLM mode is enabled.
- [ ] Deploy and confirm the database backend shows `postgres`.
- [ ] Confirm existing CRM leads are visible.
- [ ] Run one test lead and verify agent_runs/workflow_runs rows.
- [ ] Create one Human Approval request and approve/reject it.
- [ ] Record a small test sale only after a real client transaction exists.
- [ ] Record delivery after actual delivery.
- [ ] Keep external identity limited to AGRL GIS Mapping Support / A.Y.
