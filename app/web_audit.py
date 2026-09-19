from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "AI-Business-Automation-V12-Audit/1.0"
TIMEOUT = 15


def normalize_public_url(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if not re.match(r"^https?://", value, flags=re.I):
        value = "https://" + value
    p = urlparse(value)
    kept = []
    for k, v in parse_qsl(p.query, keep_blank_values=True):
        kl = k.lower()
        if kl.startswith("utm_") or kl in {"fbclid", "gclid", "msclkid"}:
            continue
        kept.append((k, v))
    return urlunparse(p._replace(query=urlencode(kept), fragment=""))


def _is_public_host(host: str) -> bool:
    if not host:
        return False
    host = host.lower().strip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        addresses = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for item in addresses:
        ip = ipaddress.ip_address(item[4][0])
        if not ip.is_global:
            return False
    return True


def _signal(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, flags=re.I | re.S))


def audit_website(url: str) -> dict:
    clean = normalize_public_url(url)
    if not clean:
        raise ValueError("Please provide a public http(s) URL.")
    parsed = urlparse(clean)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are supported.")
    if not _is_public_host(parsed.hostname or ""):
        raise ValueError("Only public internet hosts are accepted.")

    response = requests.get(
        clean,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        timeout=TIMEOUT,
        allow_redirects=True,
    )
    final_url = normalize_public_url(response.url)
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        raise ValueError(f"Target returned content type '{content_type}', not HTML.")

    raw_html = response.text[:5_000_000]
    soup = BeautifulSoup(raw_html, "html.parser")
    visible_text = " ".join(soup.stripped_strings)
    scripts = " ".join(x.get_text(" ", strip=True) for x in soup.find_all("script"))
    combined = raw_html + "\n" + scripts

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    meta_desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    viewport = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
    h1s = [x.get_text(" ", strip=True) for x in soup.find_all("h1")]
    canonical = bool(soup.find("link", attrs={"rel": re.compile(r"canonical", re.I)}))
    og_title = bool(soup.find("meta", attrs={"property": re.compile(r"^og:title$", re.I)}))
    structured = bool(soup.find("script", attrs={"type": re.compile(r"ld\+json", re.I)}))
    faq = _signal(visible_text, r"\b(frequently asked questions|faq)\b")
    service = _signal(visible_text, r"\b(services?|roofing|repairs?|installation|book|quote|contact us)\b")
    cta = _signal(visible_text, r"\b(request (a )?quote|get (a )?quote|get started|book (now|online)|contact us|call now)\b")
    contact_link = any(_signal(a.get("href", ""), r"mailto:|tel:|/contact\b|#contact") for a in soup.find_all("a"))
    phone = _signal(visible_text, r"(?:\+?\d[\d\s().-]{7,}\d)")
    email = _signal(visible_text + " " + raw_html, r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
    forms = bool(soup.find("form"))

    images = soup.find_all("img")
    alt_count = sum(1 for img in images if (img.get("alt") or "").strip())
    alt_coverage = 100 if not images else round(100 * alt_count / len(images), 1)

    analytics = _signal(
        combined,
        r"(googletagmanager|google-analytics|gtag\s*\(|analytics\.js|plausible|matomo)"
    )
    useful_text = len(visible_text)

    checks = [
        {"name":"HTTPS","pass":parsed.scheme=="https","severity":"High","confidence":100,
         "evidence":f"Requested URL scheme: {parsed.scheme}.",
         "recommendation":"Serve the public website over HTTPS."},
        {"name":"Page title","pass":bool(title),"severity":"Medium","confidence":95,
         "evidence":f"<title>: {title!r}" if title else "No <title> element detected.",
         "recommendation":"Add a descriptive, page-specific title."},
        {"name":"Meta description","pass":bool(meta_desc and meta_desc.get("content","").strip()),"severity":"Medium","confidence":96,
         "evidence":f"Meta description length: {len(meta_desc.get('content','').strip())}" if meta_desc else "No meta description detected.",
         "recommendation":"Add a concise meta description aligned with search intent."},
        {"name":"Viewport meta","pass":bool(viewport),"severity":"High","confidence":98,
         "evidence":f"Viewport: {viewport.get('content','')!r}" if viewport else "No viewport meta detected.",
         "recommendation":"Add a responsive viewport meta tag."},
        {"name":"Clear H1","pass":len(h1s)==1,"severity":"Medium","confidence":95,
         "evidence":f"H1 count: {len(h1s)}; headings: {h1s[:3]!r}",
         "recommendation":"Use one clear primary H1 for the page topic/service."},
        {"name":"Service content","pass":service,"severity":"Medium","confidence":90,
         "evidence":"Service-related language detected." if service else "No strong service-related signal found.",
         "recommendation":"Clearly describe core services and customer problems solved."},
        {"name":"Conversion CTA","pass":cta,"severity":"High","confidence":92,
         "evidence":"Quote/booking/contact CTA language detected." if cta else "No strong conversion CTA phrase detected.",
         "recommendation":"Add a prominent customer action such as Request a Quote or Book Now."},
        {"name":"Contact link","pass":contact_link,"severity":"Medium","confidence":92,
         "evidence":"Phone/email/contact anchor detected." if contact_link else "No clear contact anchor detected.",
         "recommendation":"Provide a clear contact path."},
        {"name":"Contact phone signal","pass":phone,"severity":"Medium","confidence":90,
         "evidence":"Phone-like number detected in fetched page text." if phone else "No phone-like number detected.",
         "recommendation":"Show a verified business phone number where appropriate."},
        {"name":"Contact email signal","pass":email,"severity":"Medium","confidence":90,
         "evidence":"Email-like pattern detected." if email else "No email-like pattern detected.",
         "recommendation":"Show a verified business email or secure contact form."},
        {"name":"Contact form","pass":forms,"severity":"Medium","confidence":95,
         "evidence":"HTML <form> element detected." if forms else "No HTML <form> element detected.",
         "recommendation":"Provide a simple contact/quote form when suitable."},
        {"name":"Analytics detected","pass":analytics,"severity":"Low","confidence":85,
         "evidence":"Analytics-related script signal detected in fetched HTML." if analytics else "No analytics signal detected in fetched HTML.",
         "recommendation":"Verify analytics/tag-manager implementation; non-detection here does not prove tracking is absent."},
        {"name":"Canonical link","pass":canonical,"severity":"Low","confidence":95,
         "evidence":"Canonical link element detected." if canonical else "No canonical link detected.",
         "recommendation":"Add an appropriate canonical link where needed."},
        {"name":"Open Graph title","pass":og_title,"severity":"Low","confidence":95,
         "evidence":"og:title detected." if og_title else "No og:title detected.",
         "recommendation":"Add suitable Open Graph metadata where relevant."},
        {"name":"Structured data","pass":structured,"severity":"Low","confidence":95,
         "evidence":"JSON-LD script detected." if structured else "No JSON-LD script detected.",
         "recommendation":"Consider appropriate structured data for the page type."},
        {"name":"Image alt coverage","pass":alt_coverage>=90,"severity":"Medium","confidence":96,
         "evidence":f"{alt_count}/{len(images)} images have non-empty alt text ({alt_coverage}%).",
         "recommendation":"Use meaningful alt text for informative images and empty alt for decorative images."},
        {"name":"FAQ signal","pass":faq,"severity":"Low","confidence":82,
         "evidence":"FAQ-related language detected." if faq else "No FAQ-related language detected.",
         "recommendation":"Consider an FAQ section that answers real customer questions."},
        {"name":"Useful text volume","pass":useful_text>=500,"severity":"Low","confidence":90,
         "evidence":f"Approximate parsed visible text characters: {useful_text}.",
         "recommendation":"Ensure useful service, location, trust and action content is present."},
    ]

    weights = {"High":2.0, "Medium":1.2, "Low":0.7}
    total = sum(weights[x["severity"]] for x in checks)
    passed = sum(weights[x["severity"]] for x in checks if x["pass"])
    overall = round(100*passed/total) if total else 0

    def score(names: set[str]) -> int:
        subset = [x for x in checks if x["name"] in names]
        denom = sum(weights[x["severity"]] for x in subset)
        numer = sum(weights[x["severity"]] for x in subset if x["pass"])
        return round(100*numer/denom) if denom else 0

    scores = {
        "overall": overall,
        "technical": score({"HTTPS","Page title","Meta description","Viewport meta","Canonical link"}),
        "content": score({"Clear H1","Service content","Open Graph title","Structured data","Image alt coverage","FAQ signal","Useful text volume"}),
        "conversion": score({"Conversion CTA","Contact link","Contact phone signal","Contact email signal","Contact form"}),
        "measurement": score({"Analytics detected"}),
    }

    return {
        "requested_url": clean,
        "final_url": final_url,
        "status_code": response.status_code,
        "content_type": content_type,
        "scores": scores,
        "checks": checks,
        "stats": {
            "title": title,
            "h1_count": len(h1s),
            "image_count": len(images),
            "alt_coverage": alt_coverage,
            "visible_text_chars": useful_text,
        },
    }
