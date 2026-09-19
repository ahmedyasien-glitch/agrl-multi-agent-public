from __future__ import annotations

import uuid
from typing import Any

from .agents import AgentResult
from .db import db, now_iso


def upsert_lead(lead: dict[str, Any]) -> int:
    existing = db.fetch_one("SELECT id FROM leads WHERE company_name=%s", (lead["company_name"],))
    values = (
        lead.get("company_name", ""), lead.get("website", ""), lead.get("city", ""), lead.get("country", ""),
        lead.get("industry", ""), lead.get("contact_name", ""), lead.get("contact_email", ""), lead.get("source", ""),
        lead.get("owner", "A.Y."), lead.get("notes", ""), float(lead.get("deal_value", 0) or 0), float(lead.get("probability", 0) or 0)
    )
    if existing:
        lead_id = int(existing["id"])
        db.execute(
            "UPDATE leads SET website=%s,city=%s,country=%s,industry=%s,contact_name=%s,contact_email=%s,source=%s,owner=%s,notes=%s,deal_value=%s,probability=%s,updated_at=%s WHERE id=%s",
            values[1:] + (now_iso(), lead_id),
        )
        return lead_id
    if db.backend == "postgres":
        return db.insert_returning_id(
            "INSERT INTO leads(company_name,website,city,country,industry,contact_name,contact_email,source,owner,notes,deal_value,probability,created_at,updated_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW()) RETURNING id",
            values,
        )
    return db.insert_returning_id(
        "INSERT INTO leads(company_name,website,city,country,industry,contact_name,contact_email,source,owner,notes,deal_value,probability,created_at,updated_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
        values,
    )


def create_run(lead_id: int) -> str:
    run_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO workflow_runs(run_id,lead_id,current_stage,created_at,updated_at) VALUES(%s,%s,%s,%s,%s)",
        (run_id, lead_id, "Discovery", now_iso(), now_iso()),
    )
    return run_id


def save_results(run_id: str, lead_id: int, results: list[AgentResult]) -> None:
    for result in results:
        db.execute(
            "INSERT INTO agent_runs(run_id,lead_id,agent,status,output_json,evidence_json,next_action,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                run_id, lead_id, result.agent, result.status,
                db.json(result.output), db.json(result.evidence), result.next_action, now_iso()
            ),
        )

    mgr = next((r.output for r in results if r.agent == "Manager"), {})
    decision = mgr.get("decision", "UNKNOWN")
    reason = mgr.get("reason", "")
    stage = {
        "HOLD": "Discovery", "RESEARCH_MORE": "Audit", "READY_FOR_HUMAN_REVIEW": "Proposal Review"
    }.get(decision, "Discovery")
    db.execute(
        "UPDATE workflow_runs SET decision=%s,decision_reason=%s,current_stage=%s,updated_at=%s WHERE run_id=%s",
        (decision, reason, stage, now_iso(), run_id),
    )


def log_activity(lead_id: int, action: str, detail: str = "") -> None:
    db.execute("INSERT INTO activity_log(lead_id,action,detail,created_at) VALUES(%s,%s,%s,%s)", (lead_id, action, detail, now_iso()))


def save_outreach(lead_id: int, proposal: dict[str, Any], outreach: dict[str, Any]) -> None:
    db.execute(
        "INSERT INTO proposals(lead_id,created_at,proposal_text) VALUES(%s,%s,%s)",
        (lead_id, now_iso(), proposal.get("body", "")),
    )
    db.execute(
        "INSERT INTO outreach_runs(lead_id,created_at,channel,subject,body,status,source_json) VALUES(%s,%s,%s,%s,%s,%s,%s)",
        (lead_id, now_iso(), "email", outreach.get("subject", ""), outreach.get("body", ""), "Draft", db.json(outreach)),
    )


def request_human_approval(run_id: str, lead_id: int, action: str) -> int:
    return db.insert_returning_id(
        "INSERT INTO human_approvals(run_id,lead_id,action,status,created_at) VALUES(%s,%s,%s,%s,%s)" if db.backend == "postgres"
        else "INSERT INTO human_approvals(run_id,lead_id,action,status,created_at) VALUES(%s,%s,%s,%s,%s)",
        (run_id, lead_id, action, "Pending", now_iso()),
    )


def decide_approval(approval_id: int, status: str, approved_by: str, note: str = "") -> None:
    if status not in {"Approved", "Rejected", "Pending"}:
        raise ValueError("Unsupported approval status")
    db.execute(
        "UPDATE human_approvals SET status=%s,approved_by=%s,note=%s WHERE id=%s",
        (status, approved_by, note, approval_id),
    )


def record_sale(lead_id: int, deal_value: float, notes: str = "") -> None:
    db.execute(
        "INSERT INTO sales_events(lead_id,event_type,event_date,notes,deal_value) VALUES(%s,%s,%s,%s,%s)",
        (lead_id, "Won", now_iso(), notes, deal_value),
    )
    db.execute(
        "UPDATE leads SET status=%s,deal_value=%s,updated_at=%s WHERE id=%s",
        ("Won", deal_value, now_iso(), lead_id),
    )
    log_activity(lead_id, "sale_recorded", f"deal_value={deal_value}")


def record_delivery(lead_id: int, deliverable_type: str, file_name: str, revenue_amount: float = 0, status: str = "Delivered") -> None:
    db.execute(
        "INSERT INTO delivery_records(lead_id,deliverable_type,file_name,status,revenue_amount,delivered_at) VALUES(%s,%s,%s,%s,%s,%s)",
        (lead_id, deliverable_type, file_name, status, revenue_amount, now_iso() if status == "Delivered" else None),
    )
    log_activity(lead_id, "delivery_recorded", f"{deliverable_type}: {file_name}")


def list_leads() -> list[dict[str, Any]]:
    return db.fetch_all("SELECT id,company_name,city,country,industry,status,deal_value,probability,created_at,updated_at FROM leads ORDER BY id DESC")


def list_approvals() -> list[dict[str, Any]]:
    return db.fetch_all("SELECT id,run_id,lead_id,action,status,approved_by,note,created_at FROM human_approvals ORDER BY id DESC")


def sales_summary() -> dict[str, float]:
    row = db.fetch_one("SELECT COALESCE(SUM(deal_value),0) AS total, COUNT(*) AS wins FROM sales_events WHERE event_type='Won'") or {"total": 0, "wins": 0}
    return {"revenue": float(row.get("total", 0) or 0), "wins": int(row.get("wins", 0) or 0)}
