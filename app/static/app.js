/* Galpu prototype front end: MediaRecorder mic -> POST /ask,
   typed fallback -> POST /ask-text, reply spoken with browser speech. */

const micBtn = document.getElementById("mic");
const statusEl = document.getElementById("status");
const chatEl = document.getElementById("chat");
const cardsEl = document.getElementById("cards");
const typedEl = document.getElementById("typed");
const sendBtn = document.getElementById("send");

let recorder = null;
let chunks = [];
let recording = false;

function addMsg(who, text) {
  const div = document.createElement("div");
  div.className = "msg " + who;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function speak(text, lang) {
  if (!("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  const tag = { hi: "hi-IN", or: "or-IN", te: "te-IN", ta: "ta-IN", ml: "ml-IN", kn: "kn-IN", ur: "ur-IN", en: "en-IN" }[(lang || "en").slice(0, 2)] || "en-IN";
  u.lang = tag;
  const voices = speechSynthesis.getVoices();
  const v = voices.find(v => v.lang === tag) || voices.find(v => v.lang.startsWith(tag.slice(0, 2))) || voices.find(v => v.lang.startsWith("hi")) || null;
  if (v) u.voice = v; // Odia and some languages fall back to a Hindi voice in most browsers
  speechSynthesis.speak(u);
}

function showCards(matches) {
  cardsEl.innerHTML = "";
  (matches || []).forEach(m => {
    const a = document.createElement("a");
    a.className = "card";
    a.href = m.official_link;
    a.target = "_blank";
    a.rel = "noopener";
    a.innerHTML = `<strong>${m.title}</strong><span>${m.organiser}</span>
      <span>Who can apply: ${m.who_can_apply}</span>
      <span>Deadline: ${m.deadline}</span>
      <button class="listen" type="button">🔊 Listen</button>`;
    a.querySelector(".listen").addEventListener("click", ev => {
      ev.preventDefault();
      speak(`${m.title}, by ${m.organiser}. Who can apply: ${m.who_can_apply}. Deadline: ${m.deadline}.`, "en");
    });
    cardsEl.appendChild(a);
  });
}

async function handleAnswer(res) {
  const data = await res.json();
  if (data.transcript) addMsg("you", data.transcript);
  addMsg("galpu", data.reply);
  speak(data.reply, data.lang);
  showCards(data.matches);
  statusEl.textContent = "Tap the mic and ask another, or open a card.";
}

async function sendAudio(blob) {
  statusEl.textContent = "Listening…";
  const fd = new FormData();
  fd.append("audio", blob, "ask.webm");
  try {
    const res = await fetch("/ask", { method: "POST", body: fd });
    await handleAnswer(res);
  } catch (e) {
    statusEl.textContent = "Something went wrong. Please try again.";
  }
}

async function startStop() {
  if (recording) { recorder.stop(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream);
    chunks = [];
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = () => {
      recording = false;
      micBtn.classList.remove("rec");
      stream.getTracks().forEach(t => t.stop());
      sendAudio(new Blob(chunks, { type: recorder.mimeType || "audio/webm" }));
    };
    recorder.start();
    recording = true;
    micBtn.classList.add("rec");
    statusEl.textContent = "Recording… tap again to send.";
  } catch (e) {
    statusEl.textContent = "Microphone is not available. Please type below instead.";
  }
}

micBtn.addEventListener("click", startStop);

async function sendTyped() {
  const text = typedEl.value.trim();
  if (!text) return;
  typedEl.value = "";
  statusEl.textContent = "Thinking…";
  try {
    const res = await fetch("/ask-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    await handleAnswer(res);
  } catch (e) {
    statusEl.textContent = "Something went wrong. Please try again.";
  }
}

sendBtn.addEventListener("click", sendTyped);
typedEl.addEventListener("keydown", e => { if (e.key === "Enter") sendTyped(); });
