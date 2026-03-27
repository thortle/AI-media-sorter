# Security Audit Report — AI-media-sorter

**Repository:** thortle/AI-media-sorter  
**Branch audited:** main  
**Audit date:** 2026-03-27  
**Scope:** Full codebase — Python server, Jinja2 HTML template, Dockerfile, service scripts, configuration files.

---

## Summary

No hardcoded production secrets were found in the repository. Credentials, paths, and host addresses are
correctly read from environment variables, and sensitive files are properly gitignored. Several
security-hardening opportunities were identified, ranging from **Critical** to **Info**. All findings with
an associated fix have been patched in this PR.

---

## Findings

### CRITICAL-01 — Vulnerable dependencies: ReDoS, arbitrary-file-write, buffer overflow

| Field | Detail |
|-------|--------|
| **Severity** | Critical |
| **Files** | `photo-server/app/requirements.txt` |
| **CVEs / Advisories** | GHSA-2jv5-9r88-3w3p (python-multipart ReDoS ≤ 0.0.6), GHSA-r7r7-rcjp-q63v (python-multipart DoS < 0.0.18), GHSA-59g5-xgcq-4qw3 (python-multipart arbitrary-file-write < 0.0.22), GHSA-qf9m-jfwg-3q4p (FastAPI ReDoS ≤ 0.109.0), GHSA-j7hp-h8jx-5ppr (Pillow buffer overflow < 10.3.0) |

**Description:** The pinned versions contain multiple published CVEs:

- `python-multipart==0.0.6` — Content-Type header ReDoS (≤ 0.0.6), multipart/form-data boundary DoS
  (< 0.0.18), and arbitrary file-write via non-default configuration (< 0.0.22).
- `fastapi==0.109.0` — Inherits the python-multipart ReDoS when parsing Content-Type headers (≤ 0.109.0).
- `pillow==10.2.0` — Buffer overflow in image parsing (< 10.3.0).

The upload endpoint (`POST /api/upload`) directly exposes these libraries to untrusted input.

**Fix applied:** Upgraded to `python-multipart==0.0.22`, `fastapi==0.115.0`, `pillow==10.3.0`.

---

### HIGH-01 — Stored XSS via unescaped server data injected into `innerHTML`

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **File** | `photo-server/app/templates/index.html` |
| **Lines (before fix)** | 903, 982, 986, 1118, 1122, 1124, 1473, 1477 |

**Description:** Multiple photo-card and album-card templates interpolate server-supplied strings
(`photo.filename`, `album.name`) directly into `innerHTML` template literals without HTML-escaping:

```js
// Vulnerable – before fix
card.innerHTML = `<div class="album-name">${album.name}</div>`;
card.innerHTML = `<img alt="${photo.filename}" ...><div class="filename">${photo.filename}</div>`;
```

If a file on disk has a name containing `"`, `<`, or `>` characters (valid on Linux/macOS), or if an
authenticated user uploads a crafted filename via `POST /api/upload`, the string will be treated as raw
HTML. An attacker who can add or upload a file named, for example,
`"><img src=x onerror=alert(document.cookie)>.jpg` would trigger JavaScript execution in every
authenticated browser session that renders that card.

**Exploitability:** An authenticated user (or an operator who places files with special names in the photo
directory) can achieve persistent XSS that steals the `sessionStorage`-stored Basic Auth credential of any
other user who views the library.

**Fix applied:** Added an `escapeHtml()` DOM helper and applied it to every server-supplied value used in
`innerHTML` interpolations.

```js
function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str)));
    return div.innerHTML;
}
// Usage:
card.innerHTML = `<div class="album-name">${escapeHtml(album.name)}</div>`;
```

---

### HIGH-02 — Upload filename not sanitized: special characters persist into stored data

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **File** | `photo-server/app/main.py` |
| **Line (before fix)** | 582 |

**Description:** The upload endpoint sanitized only whitespace characters from the original filename stem:

```python
# Before fix
original_name = Path(file.filename).stem.replace(" ", "_")
safe_name = f"upload_{timestamp}_{original_name}{ext}"
```

Characters such as `<`, `>`, `"`, `'`, `;`, `|`, and backticks were preserved, allowing the constructed
filename to contain HTML/JavaScript metacharacters that are then stored in `descriptions.json` and later
rendered in the web UI (feeding HIGH-01).

**Fix applied:** Replaced with a strict allowlist regex that keeps only `[a-zA-Z0-9_-]`:

```python
original_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", Path(file.filename).stem)
safe_name = f"upload_{timestamp}_{original_stem}{ext}"
```

---

### MEDIUM-01 — Path-containment check uses string prefix, not `Path.is_relative_to()`

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `photo-server/app/main.py` |
| **Lines (before fix)** | 81, 91 |

**Description:** `sanitize_album_path()` and `sanitize_rel_path()` used a `str.startswith()` check to
verify that a resolved path stays inside the photo root:

```python
if not str(album_path).startswith(str(PHOTO_BASE_PATH.resolve())):
```

If `PHOTO_BASE_PATH` resolves to `/photos`, this check would erroneously **pass** for a path that resolves
to `/photos_evil` (a directory that shares the string prefix but is outside the intended root). While direct
path traversal via `..` is blocked separately, the prefix check is a critical defence-in-depth layer and
should be semantically correct.

**Fix applied:** Replaced both checks with `Path.is_relative_to()` (Python 3.9+, available in the Python
3.11 runtime used by the Dockerfile):

```python
if not album_path.is_relative_to(PHOTO_BASE_PATH.resolve()):
    raise HTTPException(status_code=400, detail="Invalid album name")
```

---

### MEDIUM-02 — No upload file size limit (potential DoS / disk exhaustion)

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `photo-server/app/main.py` |
| **Line (before fix)** | 588 |

**Description:** The entire upload file was read into memory (`await file.read()`) before any size check.
An authenticated user could upload an arbitrarily large file, exhausting server RAM and disk space.

**Fix applied:** Added a 50 MB cap (covers large HEIC files from modern phones) enforced immediately after `file.read()`:

```python
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

content = await file.read()
if len(content) > MAX_UPLOAD_BYTES:
    raise HTTPException(status_code=413, detail="File too large …")
```

Adjust `MAX_UPLOAD_BYTES` to suit your largest expected photo size.

---

### MEDIUM-03 — Docker container runs as root

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `photo-server/Dockerfile` |

**Description:** The Dockerfile had no `USER` instruction, causing the application to run as UID 0 (root)
inside the container. A successful exploit of any application vulnerability would give the attacker root
privileges within the container, easing container-escape attempts.

**Fix applied:** Added a non-privileged `appuser` account and switched to it before the final `CMD`:

```dockerfile
RUN adduser --disabled-password --gecos "" appuser
USER appuser
```

> **Note:** If your volume mounts require write access, ensure the host directories are owned or writable
> by UID/GID matching `appuser` inside the container (default UID 1000 on Debian-slim).

---

### MEDIUM-04 — Moondream service accepts arbitrary file paths with no path-scope validation

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `services/moondream_service.py` |
| **Line (before fix)** | 42–44 |

**Description:** The `/describe` endpoint accepted a caller-supplied `photo_path` and passed it directly to
the image model without any path validation:

```python
path = Path(request.photo_path)
if not path.exists():
    raise HTTPException(status_code=404, detail="Photo not found")
model.analyze_image(str(path))
```

Because the service listens on `0.0.0.0:8001` with no authentication, any host-network client (or the
Docker container itself, via `host.docker.internal`) could pass an arbitrary path such as
`/etc/passwd` and have the vision model attempt to open it as an image. Even if the model cannot parse
the file usefully, the existence of files outside the photo directory is revealed via the 404 vs. 500
response difference, constituting an information-disclosure / path-traversal risk.

**Fix applied:** Added a `PHOTO_DIR` environment variable and a `is_relative_to()` containment check. `PHOTO_DIR` is now **required** — the service raises `RuntimeError` at startup if it is not set, preventing accidental access to the entire filesystem:

```python
_photo_dir_env = os.getenv("PHOTO_DIR")
if not _photo_dir_env:
    raise RuntimeError("PHOTO_DIR environment variable is required …")
_ALLOWED_PHOTO_DIR = Path(_photo_dir_env).resolve()

path = Path(request.photo_path).resolve()
if not path.is_relative_to(_ALLOWED_PHOTO_DIR):
    raise HTTPException(status_code=403, detail="Access to this path is not permitted")
```

Set `PHOTO_DIR` to your actual photo directory when starting the service.

---

### MEDIUM-05 — Insecure default credentials (`admin` / `changeme`)

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `photo-server/app/main.py` (line 44–45), `photo-server/docker-compose.example.yml` |

**Description:** If the `AUTH_USERNAME` or `AUTH_PASSWORD` environment variables are not set, the
application falls back to `admin` / `changeme`. These are well-known defaults that appear in wordlists
used by automated credential-stuffing tools.

**Fix applied:** Added a startup warning that is printed whenever either default value is detected:

```python
_DEFAULT_CREDENTIALS = {"admin", "changeme"}
if AUTH_USERNAME in _DEFAULT_CREDENTIALS or AUTH_PASSWORD in _DEFAULT_CREDENTIALS:
    log.warning(
        "⚠  Default AUTH_USERNAME/AUTH_PASSWORD detected. "
        "Set AUTH_USERNAME and AUTH_PASSWORD environment variables …"
    )
```

**Recommended hardening:** Consider making the service refuse to start (raising a `RuntimeError`) if
default credentials are detected in a production deployment.

---

### MEDIUM-06 — Hardcoded developer host path leaked in `get_ai_description`

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `photo-server/app/main.py` |
| **Line (before fix)** | 532 |

**Description:** The upload handler contained a hardcoded path translation specific to the developer's
machine:

```python
host_path = str(photo_path).replace("/photos", "/Volumes/T7_SSD/G-photos")
```

This both leaks details about the developer's filesystem layout and means the upload-description feature
would silently fail for any deployment that is not on the developer's exact machine (the Moondream service
would receive the wrong path).

**Fix applied:** Removed the hardcoded path translation. A new `HOST_PHOTO_DIR` environment variable now
supplies the host-side directory. The container translates its internal path to the host path before
calling the Moondream service:

```python
if HOST_PHOTO_DIR:
    rel = photo_path.relative_to(PHOTO_BASE_PATH)
    host_path = str(Path(HOST_PHOTO_DIR) / rel)
else:
    host_path = str(photo_path)
```

Set `HOST_PHOTO_DIR` in your `.env` to the same value as `PHOTO_DIR` (the host-side photo directory).
This is pre-wired in `docker-compose.example.yml` as `HOST_PHOTO_DIR=${PHOTO_DIR}`.

---

### LOW-01 — Internal trash path exposed in delete API response

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **File** | `photo-server/app/main.py` |
| **Line (before fix)** | 512 |

**Description:** The `DELETE /api/photo/{filename}` response included `"trash_path": str(trash_photo_path)`,
exposing the absolute filesystem path of the container's trash directory to authenticated API clients.
This is an unnecessary information disclosure.

**Fix applied:** Removed `trash_path` from the success response.

---

### LOW-02 — Exception details returned in HTTP 500 responses

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **File** | `photo-server/app/main.py` |
| **Lines** | 240, 380, 415, 501, 644 |

**Description:** Several exception handlers propagate the raw exception message directly to the client:

```python
raise HTTPException(status_code=500, detail=f"Failed to convert image: {str(e)}")
raise HTTPException(status_code=500, detail=str(e))          # list_albums
raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
```

Exception messages can contain internal file paths, library versions, or system details that are useful
to an attacker.

**Recommended hardening (not patched in this PR):** Log the exception server-side and return a generic
message to the client:

```python
log.exception("Image conversion failed for %s", photo_path)
raise HTTPException(status_code=500, detail="Image processing error")
```

---

### LOW-03 — Basic Auth credentials stored in `sessionStorage` (base64, not encrypted)

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **File** | `photo-server/app/templates/index.html` |
| **Lines** | 797–798 |

**Description:** After a successful login the JavaScript stores the Base64-encoded `Authorization` header
in `sessionStorage`:

```js
sessionStorage.setItem('photoServerAuth', header);
```

`sessionStorage` is accessible to any JavaScript running on the same origin. If an XSS vulnerability is
present (see HIGH-01), the credential can be exfiltrated. Base64 is not encryption — decoding the stored
value yields `username:password` in plain text. `sessionStorage` is cleared when the tab closes, which is
better than `localStorage`, but the risk remains while the tab is open.

**Recommended hardening:** This is an inherent trade-off of client-side Basic Auth. The XSS fix in HIGH-01
reduces the exploitability. For higher security, consider server-side sessions (e.g., signed cookies with
`HttpOnly; Secure; SameSite=Strict`) instead of client-side credential storage.

---

### INFO-01 — No HTTPS enforcement

| Field | Detail |
|-------|--------|
| **Severity** | Info |
| **File** | `photo-server/Dockerfile`, `photo-server/docker-compose.example.yml` |

**Description:** The server listens on plain HTTP. Basic Auth credentials are transmitted in
Base64-over-HTTP, making them trivially interceptable on any untrusted network segment (e.g., home LAN
with other devices, coffee-shop Wi-Fi).

**Recommended hardening:** Place the server behind a TLS-terminating reverse proxy (nginx, Caddy, or
Tailscale HTTPS). The README already mentions Tailscale for remote access — enabling Tailscale HTTPS
certificates provides end-to-end encryption with no extra infrastructure.

---

### INFO-02 — No rate limiting on authentication or API endpoints

| Field | Detail |
|-------|--------|
| **Severity** | Info |
| **File** | `photo-server/app/main.py` |

**Description:** There is no brute-force protection on the Basic Auth check. An attacker with network
access can make unlimited login attempts.

**Recommended hardening:** Add rate limiting via `slowapi` (a FastAPI-compatible library wrapping
`limits`) or place the server behind a proxy that enforces per-IP request limits.

---

### INFO-03 — FastAPI automatic API documentation accessible in production

| Field | Detail |
|-------|--------|
| **Severity** | Info |
| **File** | `photo-server/app/main.py` |

**Description:** FastAPI serves interactive API documentation at `/docs` and `/redoc` by default. These
endpoints are not protected by `verify_credentials` (though the underlying API endpoints themselves are).
The docs reveal the full API surface to anyone who can reach port 8000.

**Recommended hardening:** Disable the docs in production:

```python
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
```

---

## Credential Exposure Verdict

| Category | Result |
|----------|--------|
| Hardcoded API keys / tokens | ✅ None found |
| Hardcoded passwords | ✅ None found (defaults are env-var-overridable) |
| Secrets in `.env` committed to git | ✅ `.env` is gitignored |
| Secrets in example/config files | ✅ `.env.example` uses placeholder values only |
| Secrets in test files, docs, or scripts | ✅ None found |
| Secrets in Dockerfile or docker-compose | ✅ None; credentials passed via env at runtime |

---

## Patched vs. Recommended-Only Fixes

| ID | Patched in this PR | Recommended hardening only |
|----|:-----------------:|:--------------------------:|
| CRITICAL-01 Vulnerable dependencies | ✅ | |
| HIGH-01 innerHTML XSS | ✅ | |
| HIGH-02 Upload filename sanitization | ✅ | |
| MEDIUM-01 Path prefix vs. `is_relative_to` | ✅ | |
| MEDIUM-02 Upload size limit | ✅ | |
| MEDIUM-03 Docker non-root user | ✅ | |
| MEDIUM-04 Moondream path scope | ✅ | |
| MEDIUM-05 Default credential warning | ✅ | |
| MEDIUM-06 Hardcoded host path | ✅ | |
| LOW-01 Trash path in response | ✅ | |
| LOW-02 Exception details in 500 responses | | ✅ |
| LOW-03 Credentials in sessionStorage | | ✅ |
| INFO-01 No HTTPS | | ✅ |
| INFO-02 No rate limiting | | ✅ |
| INFO-03 FastAPI docs exposed | | ✅ |
