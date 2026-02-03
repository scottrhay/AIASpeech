# AIASpeech Bug Fix Changelog

**Date:** 2025-07-24  
**Fixed by:** Tov (subagent)  
**Test Report:** `TEST-REPORT-EMET.md`  
**Status:** Code fixed in repo — needs redeploy by Hur

---

## Critical Bugs (Clips Not Working)

### ✅ BUG-001: Nginx Not Serving Static Audio Files
**File:** `deploy/nginx/conf.d/aiaspeech.conf`, `nginx-aiaspeech.conf`  
**Change:** Added `location /static/audio/` block that proxies to the Flask backend container.  
Previously, nginx only proxied `/api/` routes — audio URLs at `/static/audio/*` returned 404.

### ✅ BUG-002: Audio Files Not Persisted Across Container Restarts  
**File:** `docker-compose.yml`  
**Change:** Added volume mount `./static/audio:/app/static/audio` to the `aiaspeech` service.  
Previously, audio files were only stored inside the container filesystem — gone on restart.

---

## Security Fixes

### ✅ SEC-001: OAuth Token Exposed in URL Query String
**Files:** `backend/app/routes/auth.py`, `frontend/src/App.js`  
**Change:** OAuth callback now redirects with token in URL **fragment** (`#token=...`) instead of query string (`?token=...`).  
Fragments are never sent to the server, so the JWT won't appear in server logs, browser history, or Referer headers.  
Frontend updated to read from fragment first, with backward-compatible fallback to query string.

### ✅ SEC-002: Unauthenticated Webhook Endpoint
**Files:** `backend/app/routes/webhooks.py`, `docker-compose.yml`  
**Change:** Added `_verify_webhook_secret()` check at top of `/api/v1/webhooks/azure-speech-callback`.  
When `WEBHOOK_SECRET` env var is set, the caller must include matching `X-Webhook-Secret` header.  
If not set, the endpoint still works (backward compatible) but logs a warning.  
**Action required:** Set `WEBHOOK_SECRET` in `.env` file on VPS before deploy.

### ✅ SEC-003: SSML Injection via User Lyrics
**Files:** `backend/app/routes/speech.py`, `backend/app/routes/songs.py`  
**Change:** User-provided text is now escaped with `html.escape()` before being inserted into SSML templates.  
Prevents malicious SSML tags from being injected through lyrics/text input.

---

## Edge Case Fixes

### ✅ EDGE-001: Empty String Audio URLs Treated as Truthy
**Files:** `frontend/src/components/SongCard.js`, `frontend/src/components/SongViewModal.js`, `frontend/src/components/Studio/SongCardEnhanced.js`, `frontend/src/components/Studio/TrackCard.js`  
**Change:** All `song.download_url_1` / `song.download_url_2` checks now include `.trim()` to handle empty strings.

### ✅ EDGE-002: No Audio Error Handling (Silent 404)
**Files:** `frontend/src/components/SongCard.js`, `frontend/src/components/SongViewModal.js`, `frontend/src/components/Studio/TrackCard.js`  
**Change:** Added `onError` handlers to all `<audio>` elements. When audio fails to load, a visible "⚠ Audio unavailable" message appears.

### ✅ EDGE-003: Azure TTS 429 Rate Limit — No Retry
**Files:** `backend/app/routes/songs.py`, `backend/app/routes/speech.py`  
**Change:** Added retry with exponential backoff (3 retries, starting at 2s delay) for Azure TTS 429 responses.

---

## Files Modified (Complete List)

| File | Bugs Fixed |
|------|-----------|
| `deploy/nginx/conf.d/aiaspeech.conf` | BUG-001 |
| `nginx-aiaspeech.conf` | BUG-001 |
| `docker-compose.yml` | BUG-002, SEC-002 |
| `backend/app/routes/auth.py` | SEC-001 |
| `backend/app/routes/webhooks.py` | SEC-002 |
| `backend/app/routes/speech.py` | SEC-003, EDGE-003 |
| `backend/app/routes/songs.py` | SEC-003, EDGE-003 |
| `frontend/src/App.js` | SEC-001 |
| `frontend/src/components/SongCard.js` | EDGE-001, EDGE-002 |
| `frontend/src/components/SongViewModal.js` | EDGE-001, EDGE-002 |
| `frontend/src/components/Studio/SongCardEnhanced.js` | EDGE-001 |
| `frontend/src/components/Studio/TrackCard.js` | EDGE-001, EDGE-002 |

---

## Deployment Notes for Hur

1. **Create audio directory on host:** `mkdir -p ./static/audio` in the project root on VPS
2. **Set webhook secret** (optional but recommended): Add `WEBHOOK_SECRET=<random-string>` to `.env`
3. **Rebuild frontend:** `cd frontend && npm run build` (React changes need rebuild)
4. **Rebuild + restart containers:** `docker-compose up -d --build`
5. **Verify:** Hit `https://speech.aiacopilot.com/static/audio/` — should get a response from Flask (not nginx 404)
