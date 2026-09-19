from __future__ import annotations
from datetime import datetime, timezone
from html import escape

def build_audit_report_html(lead: dict, audit: dict, biz: dict) -> str:
    scores = audit.get("scores", {})
    priority = biz.get("priority_score", biz.get("opportunity", 0))
    improvement = biz.get("improvement_opportunity", max(0, 100 - int(biz.get("website_score", scores.get("overall", 0)))))
    rows = []
    for item in audit.get("checks", []):
        rows.append(
            "<tr>"
            f"<td>{escape(str(item.get('name','')))}</td>"
            f"<td>{'PASS' if item.get('pass') else 'REVIEW'}</td>"
            f"<td>{escape(str(item.get('severity','')))}</td>"
            f"<td>{int(item.get('confidence',0))}%</td>"
            f"<td>{escape(str(item.get('evidence','')))}</td>"
            f"<td>{escape(str(item.get('recommendation','')))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{escape(str(lead.get('company_name','Business')))} — Audit</title>
<style>
body{{font-family:Arial,sans-serif;color:#172033;margin:40px;line-height:1.5}}
.cards{{display:flex;gap:12px;flex-wrap:wrap}} .card{{border:1px solid #ddd;border-radius:12px;padding:14px;min-width:135px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #ddd;padding:8px;vertical-align:top;text-align:left}}
th{{background:#f4f5f8}} .small{{color:#666;font-size:12px}}
</style></head><body>
<h1>{escape(str(lead.get('company_name','Business')))} — Website Audit</h1>
<p class="small">Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · {escape(str(audit.get('final_url','')))}</p>
<div class="cards">
<div class="card"><b>Overall</b><h2>{scores.get('overall',0)}/100</h2></div>
<div class="card"><b>Technical</b><h2>{scores.get('technical',0)}/100</h2></div>
<div class="card"><b>Content</b><h2>{scores.get('content',0)}/100</h2></div>
<div class="card"><b>Conversion</b><h2>{scores.get('conversion',0)}/100</h2></div>
<div class="card"><b>Measurement</b><h2>{scores.get('measurement',0)}/100</h2></div>
<div class="card"><b>Lead quality</b><h2>{biz.get('lead_quality',0)}/100</h2></div>
<div class="card"><b>Improvement opportunity</b><h2>{improvement}/100</h2></div>
<div class="card"><b>Priority score</b><h2>{priority}/100</h2></div>
</div>
<h2>Evidence-based findings</h2>
<table><thead><tr><th>Check</th><th>Status</th><th>Severity</th><th>Confidence</th><th>Evidence</th><th>Recommendation</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p class="small">This is a page-level HTML audit. It is not a certification of SEO, accessibility, ownership, legal compliance, rankings, business quality, analytics presence, or JavaScript-rendered functionality.</p>
</body></html>"""
