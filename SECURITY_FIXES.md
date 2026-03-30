# Security Fixes — Medium Priority
Date: 2026-03-21

---

## SEC-001 — JWT moved from localStorage to httpOnly cookies

**Risk:** XSS attacks could steal the JWT from `localStorage` and impersonate any user.
**Fix:** Backend sets `access_token` as an httpOnly cookie on login. JavaScript cannot read it.

### Files changed

| File | What changed |
|---|---|
| `backend/main_utils.py` | `get_current_user()` and `get_current_user_optional()` now read token from `request.cookies.get("access_token")` first, then fall back to `Authorization` header |
| `backend/routers/users.py` | `/token` sets `Set-Cookie: access_token` (httpOnly, SameSite=Lax). New `/me`, `/logout` endpoints added |
| `backend/main.py` | CORS origin changed from `"*"` to env-configurable `CORS_ORIGINS` (required for cookies to work cross-origin) |
| `frontend/lib/services.ts` | Removed `getAuthHeader()`. All fetches now use `credentials: "include"`. Added `getMe()`, `logout()` |
| `frontend/app/login/page.tsx` | Removed `localStorage.setItem("storagex_token", ...)` |
| `frontend/app/dashboard/page.tsx` | Removed `localStorage.getItem` + `jwtDecode`. Now calls `ApiService.getMe()` for user identity |
| `frontend/app/components/Navbar.tsx` | Removed `localStorage.getItem`. Calls `/users/me` to check auth state. Logout calls `ApiService.logout()` |

### Old code (preserved as comments in-file)
```
// OLD: localStorage.setItem("storagex_token", data.access_token)   ← login/page.tsx
// OLD: const token = localStorage.getItem("storagex_token")         ← dashboard/page.tsx
// OLD: setToken(localStorage.getItem("storagex_token"))             ← Navbar.tsx
// OLD: localStorage.removeItem("storagex_token")                    ← Navbar.tsx
// OLD: const getAuthHeader = () => { ... localStorage ... }        ← services.ts
// OLD: return {"access_token": access_token, "token_type": "bearer"} ← no cookies were set
```

---

## SEC-002 — WebSocket URL read from env var

**Risk:** `ws://localhost:8000` hardcoded in `dashboard/page.tsx` — breaks in any non-local environment.
**Fix:** Derive WS URL from `NEXT_PUBLIC_API_URL`, converting `http://` → `ws://` and `https://` → `wss://`.

### Files changed

| File | What changed |
|---|---|
| `frontend/app/dashboard/page.tsx` | `connectWebSocket()` now builds URL from env var |

### Old code (preserved as comment in-file)
```
// OLD: const wsUrl = `ws://localhost:8000/ws/${userId}`;
```
### New code
```typescript
const wsBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/^http/, "ws");
const wsUrl = `${wsBase}/ws/${userId}`;
```

---

## SEC-003 — Refresh token flow added

**Risk:** 24-hour access tokens with no refresh mechanism — stolen token valid for a full day. No way to invalidate sessions.
**Fix:** Access token lifetime reduced to **15 minutes**. A 7-day refresh token is issued alongside it.
On 401, `fetchWithAuth()` in `services.ts` automatically calls `/users/refresh` and retries.

### Files changed

| File | What changed |
|---|---|
| `backend/main_utils.py` | `ACCESS_TOKEN_EXPIRE_MINUTES`: 1440 → **15**. Added `REFRESH_TOKEN_EXPIRE_DAYS = 7`. Added `create_refresh_token()` |
| `backend/routers/users.py` | `/token` now also sets `refresh_token` httpOnly cookie (path=`/users/refresh` scope). New `/refresh` endpoint |
| `frontend/lib/services.ts` | Added `fetchWithAuth()` wrapper that auto-retries on 401 after refreshing. Added `refreshToken()` method |

### Old code (preserved as comment in-file)
```
# OLD: ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24   ← main_utils.py
# OLD: return {"access_token": access_token, "token_type": "bearer"}  ← no refresh token
```

---

## SEC-004 — Admin audit logging

**Risk:** No record of who performed admin actions (delete user, promote user). No way to trace abuse.
**Fix:** `log_admin_action()` in `main_utils.py` writes structured JSON to stdout on every admin action.

### Files changed

| File | What changed |
|---|---|
| `backend/main_utils.py` | Added `log_admin_action(action, admin_id, admin_email, target, details)` |
| `backend/routers/users.py` | Called on: LOGIN, LIST_USERS, DELETE_USER, PROMOTE_TO_ADMIN |

### Log format (appears in Docker logs)
```json
[AUDIT] {"event": "ADMIN_ACTION", "timestamp": "2026-03-21T12:00:00Z", "action": "DELETE_USER",
         "admin_id": 1, "admin_email": "admin@example.com", "target": "user:5",
         "details": {"deleted_email": "victim@example.com"}}
```

---

## SEC-005 — Rate limiting on login endpoint

**Risk:** `/users/token` had no rate limiting — unlimited brute-force attempts against any account.
**Fix:** 10 login attempts per IP per 60 seconds using the existing Redis `check_rate_limit()`. Returns HTTP 429 on breach. Gracefully passes through if Redis is down.

### Files changed

| File | What changed |
|---|---|
| `backend/routers/users.py` | `/token` checks `cache.check_rate_limit(f"login:{client_ip}", limit=10, window_seconds=60)` before any DB query |

### Old code (preserved as comment in-file)
```
# OLD: no rate limiting — any number of password guesses per second allowed
```

---

## Configuration notes

### New env vars

| Var | Default | Purpose |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed frontend origins |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Already existed — now also used to derive WS URL |

### Production checklist (not yet done — needs separate task)
- [ ] Set `SECRET_KEY` from env var (still hardcoded)
- [ ] Change `secure=False` → `secure=True` on cookies (requires HTTPS)
- [ ] Set `CORS_ORIGINS` to production domain
- [ ] Rotate MinIO / RabbitMQ / PostgreSQL credentials out of docker-compose.yml
