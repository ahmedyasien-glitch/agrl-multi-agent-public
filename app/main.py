from __future__ import annotations

import os
import streamlit as st
import pandas as pd

from .agents import AGENT_CATALOG
from .db import db
from .workflow import (
    create_run, list_approvals, list_leads, log_activity, record_delivery,
    record_sale, request_human_approval, save_outreach, save_results,
    sales_summary, upsert_lead, decide_approval,
)
from .orchestrator import run_pipeline

try:
    from .web_audit import audit_website, normalize_public_url
except Exception:
    audit_website = None
    normalize_public_url = lambda u: u

st.set_page_config(page_title="AGRL Multi-Agent Research Business V2", page_icon="🧠", layout="wide")

db.init_schema()

st.title("🧠 AGRL Multi-Agent Research Business V2")
st.caption("Neon/PostgreSQL-backed, human-supervised workflow for GIS, research mapping, website audit, outreach and revenue tracking")

with st.sidebar:
    st.subheader("System")
    st.write(f"Database backend: **{db.backend}**")
    st.write("External brand: **AGRL GIS Mapping Support**")
    st.write("Internal identity: **A.Y.**")
    st.divider()
    st.subheader("10-agent team")
    for name, desc in AGENT_CATALOG:
        st.caption(f"**{name}** — {desc}")
    st.divider()
    st.warning("Human approval is required before external messages, delivery, or recording a real sale.")

summary = sales_summary()
c1, c2, c3 = st.columns(3)
c1.metric("Tracked revenue", f"${summary['revenue']:,.2f}")
c2.metric("Won deals", summary["wins"])
c3.metric("Leads", len(list_leads()))

pages = st.tabs(["1. Lead & Audit", "2. Agent Pipeline", "3. Approvals", "4. Revenue & Delivery", "5. Lead History"])

with pages[0]:
    st.subheader("Lead Discovery → Website/Research Audit")
    with st.form("lead_form"):
        company = st.text_input("Company / Researcher", placeholder="e.g. Environmental consultancy or research group")
        website = st.text_input("Public website", placeholder="https://...")
        contact_name = st.text_input("Contact name")
        contact_email = st.text_input("Public contact email")
        city = st.text_input("City", value="Dubai")
        country = st.text_input("Country", value="UAE")
        industry = st.text_input("Industry / research area", value="Environmental consulting")
        buyer_type = st.selectbox("Buyer type", ["Company", "Research group", "Academic researcher", "Engineering office", "Other"])
        source = st.text_input("Lead source", value="Direct research")
        service_match = st.selectbox("Primary service", ["GIS/cartography", "Remote sensing", "Website improvement", "GIS + remote sensing", "Mixed"])
        problem_signal = st.text_area("Observed problem / opportunity signal", placeholder="Describe one concrete issue observed from public information")
        mapping_task = st.text_input("Possible mapping / delivery task", value="One publication-ready map")
        run = st.form_submit_button("Save lead + run 10-agent pipeline", type="primary")

    if run:
        lead = {
            "company_name": company.strip(), "website": website.strip(), "contact_name": contact_name.strip(),
            "contact_email": contact_email.strip(), "city": city.strip(), "country": country.strip(),
            "industry": industry.strip(), "buyer_type": buyer_type, "source": source.strip(),
            "service_match": service_match, "problem_signal": problem_signal.strip(), "mapping_task": mapping_task.strip(),
            "owner": "A.Y.",
        }
        if not company.strip():
            st.error("Company / Researcher is required.")
            st.stop()
        lead_id = upsert_lead(lead)
        run_id = create_run(lead_id)
        try:
    with st.spinner("Running the agent team…"):
        results = run_pipeline(lead)
except Exception as exc:
    st.error("Pipeline failed.")
    st.exception(exc)
    raise
        save_results(run_id, lead_id, results)
        proposal = next(r.output for r in results if r.agent == "Proposal Writer")
        outreach = next(r.output for r in results if r.agent == "Outreach Agent")
        save_outreach(lead_id, proposal, outreach)
        log_activity(lead_id, "agent_pipeline_completed", run_id)
        st.session_state["lead_id"] = lead_id
        st.session_state["run_id"] = run_id
        st.session_state["results"] = [r.as_dict() for r in results]
        st.success(f"Pipeline complete. Lead ID={lead_id}; Run={run_id}")

    st.divider()
    st.subheader("Optional public website audit")
    if audit_website is None:
        st.info("Website audit module is unavailable in this build.")
    else:
        audit_url = st.text_input("Public URL to audit", key="audit_url")
        if st.button("Run website audit", key="audit_btn"):
            try:
                normalized = normalize_public_url(audit_url)
                if not normalized:
                    st.error("Provide a valid public URL.")
                else:
                    with st.spinner("Auditing public page…"):
                        result = audit_website(normalized)
                    st.json(result)
            except Exception as exc:
                st.error(f"Audit failed: {exc}")

with pages[1]:
    st.subheader("Agent Pipeline")
    results = st.session_state.get("results", [])
    if not results:
        st.info("Run a lead pipeline first.")
    else:
        mgr = next((r for r in results if r["agent"] == "Manager"), None)
        if mgr:
            st.metric("Manager decision", mgr["output"].get("decision", "UNKNOWN"))
            st.write(mgr["output"].get("reason", ""))
        tabs = st.tabs([r["agent"] for r in results])
        for tab, result in zip(tabs, results):
            with tab:
                st.write(f"Status: **{result['status']}**")
                st.json(result["output"])
                if result.get("evidence"):
                    st.caption("Evidence")
                    st.write(result["evidence"])
                st.caption("Next action")
                st.write(result.get("next_action", ""))

        if st.session_state.get("run_id") and st.session_state.get("lead_id"):
            action = st.selectbox("Human approval action", ["Approve outreach", "Approve production", "Approve delivery"])
            if st.button("Create approval request"):
                approval_id = request_human_approval(st.session_state["run_id"], st.session_state["lead_id"], action)
                st.success(f"Approval #{approval_id} created.")

with pages[2]:
    st.subheader("Human Approval Queue")
    approvals = list_approvals()
    if not approvals:
        st.info("No approval requests yet.")
    else:
        for a in approvals:
            with st.expander(f"#{a['id']} · {a['action']} · {a['status']}"):
                st.write(a)
                if a["status"] == "Pending":
                    approver = st.text_input("Approved by", value="A.Y.", key=f"approver_{a['id']}")
                    note = st.text_input("Note", key=f"note_{a['id']}")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("Approve", key=f"approve_{a['id']}"):
                        decide_approval(a["id"], "Approved", approver, note)
                        st.success("Approved.")
                        st.rerun()
                    if cc2.button("Reject", key=f"reject_{a['id']}"):
                        decide_approval(a["id"], "Rejected", approver, note)
                        st.warning("Rejected.")
                        st.rerun()

with pages[3]:
    st.subheader("Revenue Tracking → Delivery")
    leads = list_leads()
    if not leads:
        st.info("No leads yet.")
    else:
        labels = {f"{r['id']} · {r['company_name']}": r["id"] for r in leads}
        selected = st.selectbox("Lead", list(labels.keys()))
        lead_id = labels[selected]
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**Record a won deal**")
            value = st.number_input("Deal value (USD)", min_value=0.0, value=15.0, step=5.0, key="deal_value")
            notes = st.text_input("Sale notes", key="sale_notes")
            if st.button("Record sale", key="sale_btn"):
                record_sale(lead_id, value, notes)
                st.success("Sale recorded.")
                st.rerun()
        with cc2:
            st.markdown("**Record delivery**")
            dtype = st.text_input("Deliverable type", value="Publication-ready GIS map")
            fname = st.text_input("File name", value="final_map.png")
            revenue = st.number_input("Revenue attached (USD)", min_value=0.0, value=0.0, step=5.0, key="delivery_revenue")
            if st.button("Record delivery", key="delivery_btn"):
                record_delivery(lead_id, dtype, fname, revenue)
                st.success("Delivery recorded.")
                st.rerun()

with pages[4]:
    st.subheader("Lead History")
    rows = list_leads()
    if not rows:
        st.info("No leads stored yet.")
    else:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.caption("AGRL GIS Mapping Support · Internal identity: A.Y. · No automatic email sending, no automatic money movement, no autonomous trading.")
