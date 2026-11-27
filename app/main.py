"""Galpu voice-finder prototype — FastAPI service.

One core flow, end to end:
mic audio -> transcription (faster-whisper, local CPU) -> match top 3
opportunities from the seeded sample list -> template reply the browser speaks.

No external keys, no database, no network calls at runtime.
"""
import os

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.matcher import OPPORTUNITIES, top_matches

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")

app = FastAPI(title="Galpu voice finder (prototype)")
_model = None

# Short fixed opener per language so the reply starts in the user's language.
# Everything after it names only real items from the sample list.
OPENERS = {
    "hi": "आपके लिए ये अवसर मिले।",
    "or": "ଆପଣଙ୍କ ପାଇଁ ଏହି ସୁଯୋଗଗୁଡ଼ିକ ମିଳିଲା।",
    "te": "మీ కోసం ఈ అవకాశాలు దొరికాయి.",
    "ta": "உங்களுக்காக இந்த வாய்ப்புகள் கிடைத்தன.",
    "ml": "നിങ്ങൾക്കായി ഈ അവസരങ്ങൾ ലഭിച്ചു.",
    "kn": "ನಿಮ್ಮಗಾಗಿ ಈ ಅವಕಾಶಗಳು ಸಿಕ್ಕಿವೆ.",
    "ur": "آپ کے لیے یہ مواقع ملے ہیں۔",
    "en": "Here are the best matches for you.",
}


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model


def build_reply(text, lang):
    q, matches = top_matches(text)
    opener = OPENERS.get((lang or "en")[:2], OPENERS["en"])
    if not matches:
        return {
            "reply": "I could not find a match for that in the sample list, so I will not guess. "
                     "Try telling me your state, your sector such as education or health, or whether you want a grant or a fellowship.",
            "understood": {"location": q["location"], "sectors": sorted(q["sectors"]), "types": sorted(q["types"])},
            "matches": [],
        }
    parts = [opener]
    for i, m in enumerate(matches, 1):
        who = m.get("who_can_apply")
        who_part = f" Who can apply: {who}." if who and who != "None" else ""
        parts.append(f"{i}. {m['title']}, by {m['organiser']}.{who_part} Deadline: {m['deadline']}.")
    parts.append("Tap a card to open the official link, or ask me another way.")
    first = matches[0]
    who1 = first.get("who_can_apply")
    spoken = f"{opener} Top match: {first['title']}, by {first['organiser']}."
    if who1 and who1 != "None":
        spoken += f" Who can apply: {who1}."
    spoken += " The other matches are on the cards."
    return {
        "reply": " ".join(parts),
        "spoken": spoken,
        "understood": {
            "location": q["location"],
            "sectors": sorted(q["sectors"]),
            "types": sorted(q["types"]),
        },
        "matches": matches,
    }


@app.get("/api/opportunities")
def opportunities():
    return {"count": len(OPPORTUNITIES), "opportunities": OPPORTUNITIES}


class TextAsk(BaseModel):
    text: str
    lang: str | None = None


@app.post("/ask-text")
def ask_text(body: TextAsk):
    """Typed fallback: same matching as the voice flow."""
    return JSONResponse({"transcript": body.text, "lang": body.lang or "en", **build_reply(body.text, body.lang)})


@app.post("/ask")
async def ask(audio: UploadFile = File(...)):
    """Voice flow: webm/opus from MediaRecorder -> transcript -> match -> reply."""
    raw = await audio.read()
    tmp = "/tmp/_galpu_ask.webm"
    with open(tmp, "wb") as f:
        f.write(raw)
    model = get_model()
    # A small CPU model sometimes stops early on accented or noisy speech.
    # Try two decoding settings and keep the fuller transcript.
    transcript, lang = "", "en"
    for opts in ({}, {"beam_size": 5, "vad_filter": True}):
        segments, info = model.transcribe(tmp, **opts)
        text = " ".join(seg.text for seg in segments).strip()
        if len(text) > len(transcript):
            transcript, lang = text, getattr(info, "language", "en") or "en"
    if not transcript:
        return JSONResponse({
            "transcript": "",
            "lang": lang,
            "reply": "I could not hear that clearly. Please say it once more, a little closer to the phone.",
            "understood": {"location": None, "sectors": [], "types": []},
            "matches": [],
        })
    return JSONResponse({"transcript": transcript, "lang": lang, **build_reply(transcript, lang)})


@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
