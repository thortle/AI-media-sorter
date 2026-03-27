# Security Hardening Checklist

This checklist covers the most impactful steps to harden this self-hosted photo library before
exposing it to any network (local or remote).

---

## 1. Credential hygiene

| Step | What to do |
|------|------------|
| Rotate credentials | If `.env` or `docker-compose.yml` with real credentials was **ever** pushed to a public repo, treat all secrets as compromised and rotate them immediately. |
| Strong auth | Set `AUTH_USERNAME` and `AUTH_PASSWORD` to long, random values in `.env`. Never reuse credentials from other services. |
| Never commit secrets | `.env` and `photo-server/docker-compose.yml` are gitignored — keep it that way. Use `.env.example` as the only committed template. |

## 2. Before making the repository public again

Run these checks locally before flipping the repo back to public:

```bash
# 1. Scan git history for secrets (install once: brew install gitleaks  /  pip install truffleHog)
gitleaks detect --source . --verbose
# or
trufflehog git file://. --only-verified

# 2. Audit Python dependencies for known CVEs
pip install pip-audit
pip-audit -r requirements.txt
pip-audit -r photo-server/app/requirements.txt

# 3. Confirm no sensitive files are tracked
git ls-files | grep -E '\.env$|docker-compose\.yml|\.pem$|\.key$|secret'
```

If any secrets are found in history, use [BFG Repo Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
or `git filter-repo` to scrub them before re-publishing.

## 3. Branch protection (GitHub UI)

Settings → Branches → Add branch protection rule for `main`:

- [x] Require a pull request before merging
- [x] Require at least 1 approving review
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require status checks to pass before merging (add any CI checks here)
- [x] Do not allow bypassing the above settings

## 4. GitHub secret scanning & push protection

Settings → Security → Code security:

- [x] Enable **Secret scanning**
- [x] Enable **Push protection** (blocks accidental pushes of detected secrets)

These are available on public repos and private repos on GitHub Free/Team/Enterprise.

## 5. Docker container hardening

In `photo-server/docker-compose.yml`, prefer read-only photo mounts where possible and avoid
running the container as root:

```yaml
services:
  photo-server:
    # run as non-root user
    user: "1000:1000"
    volumes:
      # mount photos read-only if uploads are not needed
      - ${PHOTO_DIR}:/photos:ro
    # Optional advanced hardening: make the container filesystem read-only.
    # Requires adding tmpfs entries for every path the app writes to
    # (logs, cache, uploads). Omit if unsure — running as a non-root user
    # already provides meaningful isolation.
    # read_only: true
    # tmpfs:
    #   - /tmp
    #   - /app/thumbnails   # add any other writable paths the app needs
```

## 6. Network exposure

- Do **not** bind port `8000` to `0.0.0.0` unless access from outside localhost is intentional.
- Use Tailscale (already documented in README) or a reverse proxy with TLS for remote access.
- Consider adding rate limiting (e.g., nginx `limit_req`) in front of the API if exposed externally.

## 7. Input validation (code paths)

The current server has basic auth but limited input validation. Known areas to review:

- `photo/{filename}` and `thumbnail/{filename}` — ensure filenames are sanitised to prevent
  path traversal (e.g., reject paths containing `..`).
- `/api/upload` — validate MIME type and extension server-side; reject non-image uploads.
- `/api/photo/{filename}` DELETE — confirm the resolved path is inside `PHOTO_DIR` before moving.

See also: [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)

---

## Quick reference: key files

| File | Purpose | Committed? |
|------|---------|-----------|
| `.env` | Live credentials + paths | **No** (gitignored) |
| `.env.example` | Credential template with placeholders | Yes |
| `photo-server/docker-compose.yml` | Live compose config with bind mounts | **No** (gitignored) |
| `photo-server/docker-compose.example.yml` | Template without real paths | Yes |

---

*For the safe workflow to test and merge the draft security PR without breaking local work,
see [`docs/safe-merge-workflow.md`](docs/safe-merge-workflow.md).*
