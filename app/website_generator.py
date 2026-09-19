from __future__ import annotations
from typing import Any
import json
import urllib.request

def _ai_generate(lead: dict[str, Any], brief: str, base_url: str, model: str, api_key: str) -> dict[str, Any] | None:
    if not api_key.strip():
        return None
    payload = {
        "model": model,
        "messages": [
            {"role":"system","content":"Generate factual website copy only from supplied business facts. Never invent testimonials, awards, certifications, customers, prices, guarantees, revenue or outcomes. Return JSON with keys hero, intro, services, about."},
            {"role":"user","content":json.dumps({"business":lead,"brief":brief}, ensure_ascii=False)}
        ],
        "temperature":0.3,
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type":"application/json","Authorization":f"Bearer {api_key}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        return json.loads(raw["choices"][0]["message"]["content"])
    except Exception:
        return None

def generate_website_bundle(
    lead: dict[str, Any],
    brief: str,
    accent: str,
    ai_enabled: bool=False,
    base_url: str="",
    model: str="",
    api_key: str="",
    content_package: dict[str, Any] | None=None,
) -> dict[str,str]:
    company = str(lead.get("company_name","Business"))
    industry = str(lead.get("industry","Local service"))
    city = str(lead.get("city","local area"))
    rating = lead.get("rating","")
    reviews = lead.get("reviews","")

    ai = _ai_generate(lead, brief, base_url, model, api_key) if ai_enabled else None
    package = content_package if isinstance(content_package, dict) else {}
    hp = package.get("homepage", {}) if isinstance(package.get("homepage", {}), dict) else {}
    sp = package.get("service_page", {}) if isinstance(package.get("service_page", {}), dict) else {}
    ab = package.get("about", {}) if isinstance(package.get("about", {}), dict) else {}

    hero = hp.get("headline") or (ai or {}).get("hero") or f"Trusted {industry.lower()} services in {city}"
    intro = hp.get("subheadline") or (ai or {}).get("intro") or f"Clear, local-first {industry.lower()} support for customers in {city}."
    services = sp.get("intro") or sp.get("headline") or (ai or {}).get("services") or f"{industry} consultations, repairs, maintenance and project support."
    about = ab.get("body") or (ai or {}).get("about") or f"{company} serves customers in {city}. Use verified business history, service coverage and qualifications supplied by the business."

    faq_items = package.get("faq", [])
    faq_html = ""
    if isinstance(faq_items, list):
        for item in faq_items[:6]:
            if isinstance(item, dict):
                q = str(item.get("question","")).strip()
                a = str(item.get("answer","")).strip()
                if q and a:
                    faq_html += f'<div class="card"><h3>{q}</h3><p>{a}</p></div>'
    if not faq_html:
        faq_html = '<div class="card"><h3>What services do you provide?</h3><p>Contact the business for verified current service information.</p></div>'

    ctas = package.get("cta_variants", [])
    if not isinstance(ctas, list):
        ctas = []
    primary = hp.get("primary_cta") or (ctas[0] if ctas else "Request a quote")
    secondary = hp.get("secondary_cta") or (ctas[1] if len(ctas) > 1 else "View services")

    index = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{company} | {industry} in {city}</title>
<meta name="description" content="{hero[:155]}">
<style>
:root{{--accent:{accent};--ink:#172033;--muted:#5e6678;--bg:#f7f8fb}}
*{{box-sizing:border-box}}body{{margin:0;font-family:Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.55}}
nav{{display:flex;justify-content:space-between;align-items:center;padding:18px 7%;background:#fff;border-bottom:1px solid #e6e9ef}}
nav a{{color:var(--ink);text-decoration:none;margin-left:18px}}.brand{{font-weight:800}}
main{{max-width:1180px;margin:auto}}section{{padding:62px 7%;background:#fff;border-top:1px solid #eceff4}}
.hero{{display:grid;grid-template-columns:1.2fr .8fr;gap:40px;padding-top:90px}}
.badge{{color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.08em;font-size:12px}}
h1{{font-size:clamp(42px,6vw,74px);line-height:.98;margin:16px 0}}h2{{font-size:35px}}p{{color:var(--muted)}}
.btn{{display:inline-block;background:var(--accent);color:#fff;padding:13px 18px;border-radius:10px;text-decoration:none;font-weight:700;margin-right:8px}}
.secondary{{background:#fff;color:var(--ink);border:1px solid #dfe3eb}}
.panel{{background:var(--ink);color:#fff;border-radius:20px;padding:28px;align-self:center}}.panel p{{color:#d7ddea}}
.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.card{{border:1px solid #e5e8ef;border-radius:15px;padding:22px;background:#fff}}
footer{{padding:30px 7%;background:var(--ink);color:#fff}}footer p{{color:#cdd3df}}
@media(max-width:800px){{.hero{{grid-template-columns:1fr;padding-top:50px}}.cards{{grid-template-columns:1fr}}nav div:last-child{{display:none}}}}
</style></head>
<body>
<nav><div class="brand">{company}</div><div><a href="#services">Services</a><a href="#about">About</a><a href="#faq">FAQ</a><a class="btn" href="#contact">{primary}</a></div></nav>
<main>
<section class="hero"><div><div class="badge">{city}, {lead.get('country','')}</div><h1>{hero}</h1><p>{intro}</p>
<a class="btn" href="#contact">{primary}</a><a class="btn secondary" href="#services">{secondary}</a>
<p><strong>{rating}/5</strong> from {reviews} reviews in supplied lead data.</p></div>
<div class="panel"><div class="badge" style="color:#fff">Website concept</div><h2>Built to make local enquiries easier.</h2><p>Mobile-first layout · clear service pathways · verified trust content · enquiry-focused action.</p></div></section>
<section id="services"><div class="badge">Services</div><h2>What we can help with</h2><div class="cards">
<div class="card"><h3>Core services</h3><p>{services}</p></div>
<div class="card"><h3>Local support</h3><p>Clear information for customers in {city} and nearby areas.</p></div>
<div class="card"><h3>Next step</h3><p>Use the verified business contact channel to start an enquiry.</p></div>
</div></section>
<section id="about"><div class="badge">About</div><h2>A clearer customer journey</h2><p>{about}</p></section>
<section id="faq"><div class="badge">FAQ</div><h2>Frequently asked questions</h2><div class="cards">{faq_html}</div></section>
<section id="contact"><div class="badge">Contact</div><h2>Start an enquiry</h2><p>Use the business's verified contact channel for current information and availability.</p>
<a class="btn" href="mailto:{lead.get('contact_email','')}">{primary}</a></section>
</main>
<footer><strong>{company}</strong><p>{city} · {industry}</p></footer>
</body></html>"""

    return {
        "index.html": index,
        "styles.css": "/* Styles are embedded in index.html for standalone portability. */",
        "script.js": "document.querySelectorAll('a[href^=\"#\"]').forEach(a=>a.addEventListener('click',e=>{const t=document.querySelector(a.getAttribute('href'));if(t){e.preventDefault();t.scrollIntoView({behavior:'smooth'});}}));",
        "WEBSITE_BRIEF.md": brief,
    }
