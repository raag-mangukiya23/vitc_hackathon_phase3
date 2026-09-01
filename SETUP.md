# CivicSync v4 — setup

## 1. The four HTML files are self-contained

```
index.html        citizen app
authority.html    officer portal
dashboard.html    public transparency page
track.html        public ticket status page
```

The three `civic-*.js` files are kept in the folder for reference only. Nothing imports them any more — their contents are inlined into each page. You can ignore or delete them.

## 2. Paste a Gemini key

Get a free one at https://aistudio.google.com/app/apikey. Open **index.html**, search for `GEMINI_API_KEY`, and replace `PASTE_YOUR_GEMINI_API_KEY_HERE`. That is the only place the key is needed — the other three pages never call the model.

Without a key nothing breaks: the gauge falls back to the keyword rules and honestly labels itself "Offline rule engine."

## 3. Just open index.html

Double-clicking works. A local server also works if you prefer one:

```bash
python3 -m http.server 8000
```

If the buttons ever go dead, the login card now tells you why instead of failing silently — a watchdog prints the reason after five seconds.

## 4. Firestore rules

The public dashboard and the share page read tickets without a login, so reads must be open:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /complaints/{id} {
      allow read: if true;
      allow create: if request.auth != null;
      allow update: if true;   // tighten this after the hackathon
    }
  }
}
```

## 5. Browser notes

- **Voice input needs Chrome, Edge, or Safari.** In Firefox the mic button greys itself out and says so. Demo on Chrome.
- The mic needs microphone permission and an HTTPS origin — `localhost` counts as secure, so local demos are fine.
- Photos are still stored as base64 in the Firestore document, so the 900 KB cap stays.

---

# What changed

## The severity gauge is now a real model call

`civic-ai.js` sends the raw complaint text — and the photo, when there is one — to Gemini Flash and asks for structured JSON: category, department, severity 0–100, priority, SLA hours, reasoning, detected language, an English translation, a summary, and a spam score. The prompt pins severity to explicit anchors (90–100 = threat to life, 10–39 = cosmetic) so scores don't drift upward.

If the key is missing, the request times out, or the model returns unparseable text, it falls back to the widened keyword rules and says so on screen. The demo cannot die on stage.

The gauge now shows the reasoning sentence underneath. When a judge asks "how does the AI work?", open the network tab yourself — the request body is right there.

## Voice intake

Mic button beside the description field, using `SpeechRecognition`. Interim results stream into the textarea as you speak, and each pause re-triggers triage. The recognition language follows the picker in the header, so a Tamil speaker gets Tamil transcription.

## Vision on the photo

The uploaded image goes to the model as `inline_data` alongside the text. Two things come back:

- `photo_matches_complaint` — when false, severity is hard-capped at 20, the report is marked `flagged`, and the citizen gets a modal explaining the mismatch before they can file it anyway.
- `photo_findings` — one sentence describing what the image actually shows, which feeds the score and appears on the officer's card.

**Demo this:** submit "huge dangerous crater, cars are falling in" with a photo of a hairline crack. Watch the score fall instead of rise.

## Duplicate clustering

On submit, the app pulls the last 3 days of tickets, filters to unresolved reports within 50 m of the new pin in the same category, and merges. The oldest report becomes the cluster root; every member gets the same `clusterId` and an updated `reportCount`. Priority is boosted by `clusterBoost()` — +4 at two reports, then +8 per three more, capped at +25.

The officer sees one card reading "👥 14 citizens reported this" with the linked reports behind an expander. Resolving it closes every linked report at once and pushes the same proof photo to all of them.

There's also a live warning on the form before you submit, as soon as the pin lands near an existing cluster.

**Demo this:** file one report, then file a second from the same pin. The success modal says "Merged with 1 nearby report" and the priority jumps.

## SLA auto-escalation

Every ticket now stores `slaHours` and a concrete `slaDeadline` (4 h critical, 24 h high, 72 h medium, 168 h low). Cards on both sides render a live countdown chip that turns amber under 6 h and red past the deadline.

The authority portal runs `enforceSla()` on every snapshot and every 30 seconds. Any unresolved ticket past its deadline gets `overdue: true`, one priority bump, +10 severity, and an escalation note — guarded by `escalatedAt` so it only ever fires once. A toast announces each breach.

**Demo this:** in the Firestore console, edit a ticket's `slaDeadline` to a past date. Within 30 seconds the card goes red and escalates on its own.

## Public transparency dashboard — `dashboard.html`

No login. Resolution rate, average time to resolve, SLA compliance percentage, current overdue count, departments ranked by close rate, wards by volume, categories by frequency, a severity-weighted Leaflet heatmap with All / Unresolved / Critical filters, the citizen leaderboard, and a gallery of recently fixed issues with their proof photos.

This is the page to open when a judge asks whether a municipality could actually use this.

## Multilingual intake

Eight languages in the header picker: English, Hindi, Tamil, Kannada, Telugu, Malayalam, Marathi, Bengali. The choice sets the speech recognition locale and the UI language.

The citizen's words are stored verbatim in `originalText` with `originalLang`; the model's English translation goes into `text`, which is what the officer's queue displays — with the original quoted underneath. Status words, priority labels and chips on the citizen dashboard come from a static translation table, so they're instant and never mistranslated.

## Before/after slider

Once a ticket has both the citizen's photo and the officer's proof-of-fix photo, the card renders a drag-to-compare wipe. It appears on the citizen dashboard and on the public status page.

## Civic score and leaderboard

10 points per report, +15 once an officer verifies and closes it, +5 if the report drew corroboration, +3 for attaching a photo. Ranks run Newcomer → Contributor → Active Citizen → Ward Champion → City Guardian. Shown as a banner on the citizen dashboard and as a top-10 table on the public dashboard.

## Share ticket status — `track.html`

Every ticket has a public page at `track.html?id=TCK-2026-1234` showing the status timeline, the countdown, the before/after slider, and a mini map. The share button uses the native share sheet on mobile and falls back to copying the link. It has its own language picker, so a neighbour reads it in their language.

---

# Things worth knowing before you demo

**The Gemini key is visible in the browser.** Anyone who opens the network tab can read it. That's an acceptable hackathon trade-off, but restrict the key to your demo domain in Google AI Studio, and say out loud that production would proxy this through a Cloud Function. Judges respect knowing the gap more than pretending it isn't there. The Firebase `apiKey` is different — that one is public by design and is not a secret.

**The authority password is still hardcoded** in `civic-config.js`, unchanged from your build. Same disclosure applies.

**Cluster and SLA logic runs client-side.** It works and it demos well, but it only runs while a browser tab is open. If a judge asks how it scales, the honest answer is a Firestore scheduled Cloud Function doing the same work server-side — the escalation logic in `enforceSla()` ports over almost line for line.

**Ticket text is now HTML-escaped** everywhere it's rendered, via `esc()` in `civic-shared.js`. The previous version injected raw complaint text into `innerHTML`, so a complaint containing markup could run script in the officer's browser. Not a new feature, but worth mentioning if anyone asks about security.

**Nothing was removed.** Auth, the draggable Leaflet pin, GPS locate, two-way geocoding, the success modal, the copy-ID button, mandatory proof-of-fix photos, dispatch/hold/resolve, session-based officer login — all still there.
