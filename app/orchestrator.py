from __future__ import annotations


from typing import Any

try:
    from .agents import (
    AgentResult,
    LLMAdapter,
    deterministic_auditor,
    deterministic_gis_brief,
    deterministic_manager,
    deterministic_offer,
    deterministic_outreach,
    deterministic_production,
    deterministic_proposal,
    deterministic_qa,
    deterministic_qualifier,
    deterministic_scout,
    )
except ImportError:
    from agents import (
        AgentResult,
        LLMAdapter,
        deterministic_auditor,
        deterministic_gis_brief,
        deterministic_manager,
        deterministic_offer,
        deterministic_outreach,
        deterministic_production,
        deterministic_proposal,
        deterministic_qa,
        deterministic_qualifier,
        deterministic_scout,
    )


def _maybe_llm(adapter: LLMAdapter, agent_name: str, deterministic: AgentResult, payload: dict[str, Any]) -> AgentResult:
    system = (
        f"You are the {agent_name} in a human-supervised business workflow. "
        "Use only the supplied evidence. Never invent business facts, credentials, customer outcomes, revenue, prices, certifications, reviews, or legal claims. "
        "Return a JSON object suitable for a workflow dashboard."
    )
    out = adapter.complete_json(system, payload)
    if not out:
        return deterministic
    return AgentResult(agent_name, "complete", out, deterministic.evidence, deterministic.next_action)


def run_pipeline(lead: dict[str, Any]) -> list[AgentResult]:
    adapter = LLMAdapter()
    results: list[AgentResult] = []

    scout = deterministic_scout(lead)
    results.append(_maybe_llm(adapter, "Scout", scout, {"lead": lead}))

    qual = deterministic_qualifier(lead, scout.output)
    results.append(_maybe_llm(adapter, "Qualifier", qual, {"lead": lead, "scout": scout.output}))

    audit = deterministic_auditor(lead)
    results.append(_maybe_llm(adapter, "Evidence Auditor", audit, {"lead": lead, "qualification": results[-1].output}))

    offer = deterministic_offer(lead, audit.output)
    results.append(_maybe_llm(adapter, "Offer Strategist", offer, {"lead": lead, "audit": audit.output}))

    gis = deterministic_gis_brief(lead, offer.output)
proposal = deterministic_proposal(lead, offer.output, gis.output)
outreach = deterministic_outreach(lead, proposal.output)

results.extend([proposal, gis, outreach])

    gis = next(r for r in results if r.agent == "GIS Brief Agent")
    prod = deterministic_production(lead, offer.output, gis.output)
    results.append(_maybe_llm(adapter, "Production Planner", prod, {"lead": lead, "offer": offer.output, "gis": gis.output}))

    qa = deterministic_qa(lead, offer.output, prod.output)
    results.append(_maybe_llm(adapter, "QA Agent", qa, {"lead": lead, "offer": offer.output, "production": prod.output}))

    manager = deterministic_manager(results)
    results.append(_maybe_llm(adapter, "Manager", manager, {"lead": lead, "agents": [r.as_dict() for r in results]}))
    return results
