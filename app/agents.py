from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import json
import os
import urllib.request


@dataclass
class AgentResult:
    agent: str
    status: str
    output: dict[str, Any]
    evidence: list[str]
    next_action: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


AGENT_CATALOG = [
    ("Scout", "Lead discovery and opportunity framing"),
    ("Qualifier", "Lead fit and evidence quality"),
    ("Evidence Auditor", "Website/brief evidence audit"),
    ("Offer Strategist", "Small paid offer design"),
    ("Proposal Writer", "Personalised proposal"),
    ("GIS Brief Agent", "Cartographic and spatial brief"),
    ("Production Planner", "Delivery plan and QA checklist"),
    ("QA Agent", "Scope and evidence quality control"),
    ("Outreach Agent", "One-to-one outreach draft"),
    ("Manager", "Decision gate and priorities"),
]


def _text(v: Any) -> str:
    return str(v or "").strip()


def deterministic_scout(lead: dict[str, Any]) -> AgentResult:
    evidence = []
    for k in ("company_name", "website", "industry", "city", "problem_signal"):
        if _text(lead.get(k)):
            evidence.append(f"{k} supplied")
    output = {
        "fit_hypothesis": "Potential buyer of a focused GIS/cartography or website-improvement task.",
        "buyer_type": lead.get("buyer_type", "unknown"),
        "problem_signal": lead.get("problem_signal", "No explicit problem signal supplied"),
        "source_quality": "user-supplied/public information only",
    }
    return AgentResult("Scout", "complete", output, evidence, "Run qualification against supplied evidence.")


def deterministic_qualifier(lead: dict[str, Any], scout: dict[str, Any]) -> AgentResult:
    required = ["company_name", "contact_email"]
    missing = [k for k in required if not _text(lead.get(k))]
    fit = "review" if missing else "candidate"
    output = {
        "fit": fit,
        "missing_fields": missing,
        "service_match": lead.get("service_match", "GIS/cartography / website improvement"),
        "risk_flags": ["Do not claim outcomes not supported by evidence"],
    }
    return AgentResult("Qualifier", "complete", output, ["Lead fields checked"], "Audit the supplied evidence and keep claims conservative.")


def deterministic_auditor(lead: dict[str, Any]) -> AgentResult:
    signal = _text(lead.get("problem_signal"))
    evidence = []
    if signal:
        evidence.append(f"Observed/problem signal supplied by user: {signal}")
    else:
        evidence.append("No detailed signal supplied; opportunity remains unverified.")
    output = {
        "verified_signals": [signal] if signal else [],
        "not_verified": ["revenue impact", "conversion uplift", "competitor ranking", "customer satisfaction"],
        "evidence_quality": "medium" if signal else "low",
        "recommended_action": "Request or inspect one concrete artifact before making a specific claim.",
    }
    return AgentResult("Evidence Auditor", "complete", output, evidence, "Convert only verified evidence into the offer.")


def deterministic_offer(lead: dict[str, Any], audit: dict[str, Any]) -> AgentResult:
    industry = _text(lead.get("industry")) or "research/technical"
    service = _text(lead.get("service_match")) or "GIS/cartography"
    offer = "Publication-ready GIS map" if "GIS" in service or "map" in service.lower() else "Small website improvement audit"
    price = 15 if "GIS" in service or "map" in service.lower() else 20
    output = {
        "offer_name": offer,
        "starter_price_usd": price,
        "scope": [
            "1 focused deliverable",
            "1 revision round",
            "high-resolution export",
            "brief handoff note",
        ],
        "positioning": f"A small, evidence-based {industry.lower()} deliverable rather than a large open-ended project.",
        "why_now": "The client already has a concrete artifact/problem signal; a small first task lowers commitment.",
    }
    return AgentResult("Offer Strategist", "complete", output, audit.get("verified_signals", []), "Draft a personalised proposal using the starter offer.")


def deterministic_gis_brief(lead: dict[str, Any], offer: dict[str, Any]) -> AgentResult:
    task = _text(lead.get("mapping_task")) or "Publication-ready thematic map"
    output = {
        "task": task,
        "inputs": ["study-area boundary", "source GIS/raster data", "requested map content", "journal/report requirements"],
        "cartographic_spec": ["title", "legend", "scale bar", "north arrow", "projection/CRS", "readable labels", "high-resolution export"],
        "analysis_options": ["digitisation", "classification", "change detection", "spatial overlay"],
        "deliverables": ["PNG/TIFF", "PDF", "source package when agreed"],
        "validation": ["check units", "check CRS", "check labels", "check area totals", "check legend consistency"],
    }
    return AgentResult("GIS Brief Agent", "complete", output, [task], "Create a production plan after the customer confirms inputs and scope.")


def deterministic_proposal(lead: dict[str, Any], offer: dict[str, Any], gis: dict[str, Any]) -> AgentResult:
    contact = _text(lead.get("contact_name")) or "there"
    company = _text(lead.get("company_name")) or "your team"
    name = offer.get("offer_name", "focused GIS support")
    price = offer.get("starter_price_usd", 15)
    body = (
        f"Hello {contact},\n\n"
        f"I reviewed the information available for {company} and prepared a small starter offer: {name}.\n\n"
        f"The first deliverable would be focused on one clearly defined task, with a high-resolution final export and one revision round. "
        f"The introductory price is ${price}.\n\n"
        "The scope can be adjusted after I review the source data and your output requirements.\n\n"
        "Best regards,\nAGRL GIS Mapping Support\nA.Y."
    )
    output = {"subject": f"A focused {name} idea for {company}", "body": body, "price_usd": price}
    return AgentResult("Proposal Writer", "complete", output, ["Offer scope", "Lead identity"], "Send only after human review.")


def deterministic_production(lead: dict[str, Any], offer: dict[str, Any], gis: dict[str, Any]) -> AgentResult:
    output = {
        "stages": [
            "Input validation",
            "Data preparation",
            "Analysis / cartographic production",
            "Internal QA",
            "Client preview",
            "Revision",
            "Final delivery",
        ],
        "stop_conditions": ["missing required inputs", "scope ambiguity", "unverified client claim", "technical QA failure"],
        "estimated_complexity": "small" if offer.get("starter_price_usd", 15) <= 20 else "medium",
    }
    return AgentResult("Production Planner", "complete", output, gis.get("inputs", []), "Hold production until inputs are verified.")


def deterministic_qa(lead: dict[str, Any], offer: dict[str, Any], production: dict[str, Any]) -> AgentResult:
    checks = [
        "Scope matches paid offer",
        "No unsupported factual claims",
        "Source data provenance documented",
        "CRS/units checked",
        "Labels/legend readable",
        "Export opens correctly",
        "Revision count controlled",
    ]
    output = {"checks": checks, "pass_condition": "all critical checks pass", "critical": ["scope", "provenance", "CRS/units", "export"]}
    return AgentResult("QA Agent", "complete", output, checks, "Review all critical checks before delivery.")


def deterministic_outreach(lead: dict[str, Any], proposal: dict[str, Any]) -> AgentResult:
    company = _text(lead.get("company_name")) or "your organisation"
    email = _text(lead.get("contact_email"))
    subject = proposal.get("subject", f"GIS support for {company}")
    body = (
        "Dear Team,\n\n"
        f"I am reaching out regarding a focused GIS/cartographic support service for {company}. "
        "I can help with one-off publication-ready maps, thematic mapping, or small remote-sensing outputs.\n\n"
        "I have prepared a concise portfolio of research-based mapping examples.\n\n"
        "Portfolio: [PORTFOLIO LINK]\n\n"
        "Best regards,\nAGRL GIS Mapping Support\nA.Y."
    )
    output = {"channel": "email", "to": email, "subject": subject, "body": body, "send_mode": "human approval only"}
    return AgentResult("Outreach Agent", "complete", output, ["Public/contact field supplied" if email else "No recipient email supplied"], "Human reviews before any send.")


def deterministic_manager(results: list[AgentResult]) -> AgentResult:
    outputs = {r.agent: r.output for r in results}
    qualifier = outputs.get("Qualifier", {})
    audit = outputs.get("Evidence Auditor", {})
    fit = qualifier.get("fit")
    evidence = audit.get("evidence_quality")
    if fit != "candidate":
        decision = "HOLD"
        reason = "Missing required lead fields."
    elif evidence == "low":
        decision = "RESEARCH_MORE"
        reason = "The opportunity lacks enough verified evidence for a personalised claim."
    else:
        decision = "READY_FOR_HUMAN_REVIEW"
        reason = "The lead has enough supplied evidence for a small, bounded offer."
    output = {
        "decision": decision,
        "reason": reason,
        "priority": "medium" if decision == "READY_FOR_HUMAN_REVIEW" else "low",
        "human_gate": [
            "review recipient and factual claims",
            "review scope and price",
            "review portfolio link",
            "send manually or through an explicitly approved connector",
        ],
    }
    return AgentResult("Manager", "complete", output, [decision], "Do not perform external side effects automatically.")


class LLMAdapter:
    def __init__(self):
        self.enabled = os.getenv("LLM_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "").strip()

    def complete_json(self, system: str, user: dict[str, Any]) -> dict[str, Any] | None:
        if not (self.enabled and self.api_key and self.model):
            return None
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system + " Return JSON only."},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception:
            return None
