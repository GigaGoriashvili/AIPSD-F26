"""Tiny FastAPI front for the pipeline: upload, decide, review.

Run:  uvicorn src.app:app --reload
Imports without a key; the key is only needed when /extract is called.
"""

import html
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from .checks import decide
from .extract import FIELDS, extract
from .review import ReviewQueue, event_from

app = FastAPI(title="CampusPulse poster extraction")
queue = ReviewQueue()
events: list[dict] = []

_rooms_file = Path(__file__).resolve().parent.parent / "rooms.json"
ROOMS: set[str] = set(json.loads(_rooms_file.read_text())) if _rooms_file.exists() else {"B204", "A101", "Library"}


@app.post("/extract")
async def extract_endpoint(image: UploadFile = File(...)):
    x = extract(await image.read())
    d = decide(x, today=date.today(), rooms=ROOMS)
    fields = {n: getattr(x, n).model_dump() for n in FIELDS}
    body = {"route": d.route, "reasons": d.reasons(), "fields": fields}
    if d.route == "accepted":
        ev = event_from(x, image.filename or "upload")
        events.append(asdict(ev))
        body["event"] = asdict(ev)
    elif d.route != "rejected":
        body["draft_id"] = queue.add(x, d, image.filename or "upload").id
    return body


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>CampusPulse review</title>
<style>
 body{{background:#050913;color:#e6e9f2;font-family:"DM Sans",system-ui,sans-serif;margin:0;padding:32px}}
 h1{{font-weight:500;font-size:22px}} .card{{background:#0d1426;border:1px solid #1e2a44;border-radius:12px;padding:20px;margin:16px 0;max-width:640px}}
 label{{display:block;font-size:12px;color:#9aa6c4;margin-top:12px}} input{{width:100%;box-sizing:border-box;background:#050913;color:#e6e9f2;border:1px solid #2b3a5c;border-radius:6px;padding:8px;font:inherit}}
 input.hard{{border-color:#ff6b6b}} input.soft{{border-color:#f5c451;background:#1a1708}}
 .reason{{font-size:13px;color:#f5c451}} .ev{{font-size:12px;color:#6f7b99}} button{{margin-top:16px;background:#3b82f6;color:#fff;border:0;border-radius:6px;padding:10px 16px;font:inherit}}
</style></head><body><h1>Review queue · {count} pending</h1>{cards}
<p class="ev">Red fields were blanked on purpose: the model had no readable text for them. Type what the poster says, or leave the draft.</p>
</body></html>"""

CARD = """<form class="card" method="post" action="/review/{id}"><strong>{image}</strong> · route: {route}
{reasons}{inputs}<button>Publish event</button></form>"""


def _card(d) -> str:
    reasons = "".join(f'<div class="reason">{html.escape(r)}</div>' for r in d.decision.reasons())
    soft = {n for k, n in d.decision.flags if n not in d.decision.hard}
    inputs = ""
    for n in FIELDS:
        cls = "hard" if n in d.decision.hard else "soft" if n in soft else ""
        val = html.escape(d.fields[n] or "")
        ev = html.escape(d.evidence[n] or "no readable text")
        inputs += (f'<label>{n}</label><input class="{cls}" name="{n}" value="{val}" '
                   f'placeholder="{"read from poster" if cls == "hard" else ""}">'
                   f'<div class="ev">evidence: {ev} · confidence {d.confidence[n]:.2f}</div>')
    return CARD.format(id=d.id, image=html.escape(d.image_name), route=d.decision.route,
                       reasons=reasons, inputs=inputs)


@app.get("/review", response_class=HTMLResponse)
def review_page():
    drafts = queue.pending()
    return PAGE.format(count=len(drafts), cards="".join(_card(d) for d in drafts))


@app.post("/review/{draft_id}")
async def resolve_endpoint(draft_id: str, request: Request):
    form = await request.form()
    corrections = {n: form.get(n) for n in FIELDS}
    ev = queue.resolve(draft_id, corrections)
    events.append(asdict(ev))
    return RedirectResponse("/review", status_code=303)


@app.get("/events")
def list_events():
    return events
