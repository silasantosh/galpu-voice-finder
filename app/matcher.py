"""Keyword matcher for the Galpu voice-finder prototype.

Scores the seeded opportunity list against what the user asked.
Deliberately simple and explainable: no model, no network, nothing invented.
"""
import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "opportunities.json")

with open(DATA_PATH, encoding="utf-8") as f:
    OPPORTUNITIES = json.load(f)

STATES = {
    "andhra": "Andhra Pradesh", "arunachal": "Arunachal Pradesh", "assam": "Assam",
    "bihar": "Bihar", "chhattisgarh": "Chhattisgarh", "goa": "Goa",
    "gujarat": "Gujarat", "haryana": "Haryana", "himachal": "Himachal Pradesh",
    "jharkhand": "Jharkhand", "karnataka": "Karnataka", "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh", "maharashtra": "Maharashtra",
    "manipur": "Manipur", "meghalaya": "Meghalaya", "mizoram": "Mizoram",
    "nagaland": "Nagaland", "odisha": "Odisha", "orissa": "Odisha", "ओडिशा": "Odisha", "ओडिसा": "Odisha", "उड़ीसा": "Odisha", "ଓଡ଼ିଶା": "Odisha",
    "punjab": "Punjab", "rajasthan": "Rajasthan", "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu", "tamilnadu": "Tamil Nadu", "telangana": "Telangana",
    "tripura": "Tripura", "uttar pradesh": "Uttar Pradesh", "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal", "bengal": "West Bengal", "delhi": "Delhi", "दिल्ली": "Delhi", "महाराष्ट्र": "Maharashtra", "कर्नाटक": "Karnataka", "तमिलनाडु": "Tamil Nadu", "बिहार": "Bihar",
}

SECTORS = {
    "education": ["education", "school", "student", "children", "child", "teacher", "learning", "scholarship", "shiksha", "padhai", "vidya", "शिक्षा", "एजुकेशन", "एजूकेशन", "एजू", "एजो", "स्कूल", "बच्चों", "पढ़ाई", "ଶିକ୍ଷା"],
    "health": ["health", "hospital", "medical", "clinic", "swasthya", "doctor", "patient", "स्वास्थ्य", "हेल्थ", "अस्पताल"],
    "women": ["women", "woman", "girl", "stree", "महिला", "महिलाओं", "लड़कियों"],
    "livelihood": ["livelihood", "skill", "skills", "job", "employment", "rozgar", "income", "artisan", "farmer", "agriculture", "kisan", "self help", "shg"],
    "environment": ["environment", "climate", "tree", "water", "forest", "clean"],
    "disability": ["disability", "disabled", "divyang"],
    "elderly": ["elderly", "old age", "senior"],
}

TYPES = {
    "grant": ["grant", "grants", "funding", "fund", "anudan", "ग्रांट", "ग्रान", "अनुदान", "फंड", "फ़ंड", "आर्थिक सहायता"],
    "fellowship": ["fellowship", "fellow", "फ़ेलोशिप", "फेलोशिप"],
    "award": ["award", "prize", "puraskar", "recognition", "अवॉर्ड", "पुरस्कार"],
    "csr": ["csr"],
}


ORG_WORDS = ["nonprofit", "non-profit", "ngo", "not-for-profit", "एनजीओ", "नॉनप्रॉफ़िट", "नॉन-प्रॉफ़िट", "नॉनप्रॉफिट", "प्रोफिट", "प्रोफ़िट", "प्रॉफ़िट", "प्रफिट", "गैर-सरकारी", "ग़ैर-सरकारी", "संस्था"]


def _hits(text, groups):
    found = set()
    for name, words in groups.items():
        for w in words:
            if w in text:
                found.add(name)
                break
    return found


def extract(text):
    """Pull location, sectors and opportunity types out of free text."""
    t = " " + text.lower() + " "
    location = None
    for key, proper in STATES.items():
        if re.search(r"\b" + re.escape(key) + r"\b", t):
            location = proper
            break
    return {
        "location": location,
        "sectors": _hits(t, SECTORS),
        "types": _hits(t, TYPES),
        "org": any(w in t for w in ORG_WORDS),
    }


def score(opp, q):
    s = 0
    blob = " ".join(str(opp.get(k, "")) for k in ("title", "organiser", "sector", "location", "who_can_apply", "type")).lower()
    if q["location"]:
        if q["location"].lower() in blob:
            s += 3
        elif "india" in blob or "all states" in blob or "pan india" in blob:
            s += 1
    for sec in q["sectors"]:
        if sec in blob:
            s += 3
    for typ in q["types"]:
        if typ in blob:
            s += 2
    who = str(opp.get("who_can_apply", "")).lower()
    if q.get("org") and any(w in who for w in ("nonprofit", "not-for-profit", "ngo darpan")):
        s += 3
    # Open or unstated deadlines stay eligible; nothing is filtered out.
    if s == 0:
        s = 1  # keep every real item reachable, weakest last
    return s


def has_signal(q):
    """True when the question named a place, a sector, an opportunity type or an NGO."""
    return bool(q["location"] or q["sectors"] or q["types"] or q.get("org"))


def top_matches(text, n=3):
    q = extract(text)
    if not has_signal(q):
        return q, []  # nothing recognised: say so, never invent a match
    ranked = sorted(OPPORTUNITIES, key=lambda o: score(o, q), reverse=True)
    return q, ranked[:n]
