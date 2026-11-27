# Galpu — voice-first opportunity finder (prototype)

**Build for Bharat · Scaler × Wispr Flow hackathon, Round 2 submission.**
Theme: Livelihoods and small business / Everyday access for all.

A nonprofit worker in India taps one microphone button, asks in their own
language — *"I run a small education nonprofit in Odisha. What can I apply for
this month?"* — and hears the best matching opportunities spoken back: who can
apply, the deadline, and the next step. No typing, no English needed for the
core flow.

This repository is a **self-contained prototype**. It is not the Impact
Connect app, and no Impact Connect application code is included. The
opportunity list is a small, read-only sample of real records exported from
the Impact Connect knowledge base (`app/data/opportunities.json`, 15 items,
each with its official link and verification date).

## Run it

```bash
docker compose up --build
```

Then open http://localhost:8000 on a phone or desktop browser.

The app starts and shows its main screen with **no `.env` file and no keys**.
Speech-to-text runs locally on CPU (faster-whisper), matching is a transparent
keyword scorer, and replies are spoken by the browser's own voices. There is
nothing to sign up for and nothing to pay for.

Copy `.env.example` to `.env` only if you want to change the Whisper model
size (default `small`; `tiny` is faster on weak hardware).

## What it does

1. Tap the mic, speak in Hindi, Odia, Telugu, Tamil, Malayalam, Kannada, Urdu
   or English (Whisper auto-detects the language).
2. The app transcribes the audio locally — nothing leaves the machine.
3. It understands the sector (education, health, women, livelihood,
   environment…), the state you mention, and the kind of opportunity you want.
4. It replies by voice, starting in your language, and shows the top 3 matches
   as cards with the official link, eligibility and deadline.
5. You can refine by speaking again: for example "only grants" ranks grants
   first. Each question is matched on its own; there is no memory of the
   earlier question. You can also type instead of speaking; both paths use the
   same matcher.
6. If nothing in the question matches the sample list (no place, sector, type
   or NGO word), it says so and asks for a state, a sector, or grant/fellowship.
   If the audio is empty it asks you to say it once more. It never invents an
   answer. Every match comes only from the sample list.

## Layout

```
Dockerfile            one image, model pre-downloaded at build time
docker-compose.yml    one service, port 8000
.env.example          only optional settings, with placeholder comments
app/
  main.py             FastAPI: /ask (voice), /ask-text (typed), static page
  matcher.py          transparent keyword scoring over the sample list
  data/opportunities.json   15 real sample records (read-only)
  static/             the single page (mic button, chat, cards)
```

## Honest limits (prototype scope)

- The small CPU speech model is imperfect on accented or noisy Hindi. The
  matcher knows common Devanagari spellings, but misheard words can miss.
- Most sample records state no closing date, so the reply says so instead of
  guessing one.

- Spoken replies use the browser's voices; where a language voice is missing
  (for example Odia on some devices), the reply falls back to a Hindi voice.
- The opener line is spoken in the user's language; the opportunity details
  are read from the records, which are in English.
- The sample list is small and read-only on purpose. In the full product this
  list is the live Impact Connect opportunity database.
