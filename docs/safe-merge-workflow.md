# Safe Merge Workflow

This guide covers the recommended steps for safely evaluating the draft security PR and
reconciling it with local work that was made directly on `main`.

---

## Situation

- You have local uncommitted (or committed) changes on `main`.
- There is a **draft security PR** on a separate branch that you want to review and eventually merge.
- You want to avoid losing local work and avoid breaking the app.

---

## Step 1 — Save your local work off `main`

Before touching anything else, move your current work to its own branch so it is never at risk.

```bash
# Check what you have
git status
git stash list

# Create a feature branch from your current state
git switch -c feature/my-work    # creates branch and switches to it

# Stage and commit everything (even if it is WIP)
git add -A
git commit -m "WIP: local feature changes"
```

> **Tip:** If you are not ready to commit, use `git stash push -u -m "WIP: local feature changes"`
> instead of `git commit`. Run `git stash pop` later to restore the changes.
> The `-u` flag includes untracked files; the `-m` flag adds a label visible in `git stash list`.

---

## Step 2 — Reset local `main` to match the remote

Now that your work is safe on `feature/my-work`, bring local `main` back in sync with GitHub.

```bash
git switch main
git fetch origin
git reset --hard origin/main   # discards any stray local-only commits on main
```

---

## Step 3 — Check out the security PR branch locally

Find the branch name from the PR page on GitHub (e.g. `copilot/fix-security-audit`), then:

```bash
git fetch origin
git switch -c review/security-pr origin/<PR_BRANCH_NAME>

# Review what changed versus main
git diff origin/main...HEAD
```

---

## Step 4 — Test the security PR in isolation

Run the app and any checks you normally use:

```bash
# Start the server
cd photo-server
docker compose up -d

# Smoke-test a few searches and page loads, then stop
docker compose down

# (Optional) Run a secret scan
gitleaks detect --source . --verbose
pip-audit -r requirements.txt
```

If everything looks good, continue to Step 5. If issues are found, comment on the PR or fix
them on this branch before merging.

---

## Step 5 — Merge the security PR via the GitHub UI

Prefer merging through GitHub rather than direct command-line pushes:

1. On the PR page, click **Ready for review** to take it out of draft.
2. Review the diff one more time.
3. Click **Merge pull request** → **Confirm merge**.

This creates a clean merge commit and preserves the review history.

---

## Step 6 — Update your feature branch on top of the new `main`

```bash
git switch feature/my-work
git fetch origin
git rebase origin/main    # replay your feature commits on top of merged main
# — or — 
git merge origin/main     # merge instead of rebase if you prefer
```

Resolve any conflicts, then:

```bash
# Quick sanity test after rebase/merge
cd photo-server
docker compose up -d
# verify the app still works
docker compose down
```

---

## Step 7 — Open a PR for your feature work

Do not push directly to `main`. Open a PR from `feature/my-work`:

```bash
git push origin feature/my-work
# Then open a PR on GitHub as usual
```

---

## When to make the repo public again

Before flipping the repo back to public, complete the pre-publish checklist in
[`SECURITY.md`](../SECURITY.md#2-before-making-the-repository-public-again):

- [ ] No secrets in git history (run gitleaks / trufflehog)
- [ ] Dependencies audited (`pip-audit`)
- [ ] No sensitive files tracked (`git ls-files` check)
- [ ] Branch protection enabled on `main`
- [ ] GitHub secret scanning + push protection enabled

---

## Summary

```
main (remote, clean)
  └── review/security-pr   ← test PR here, then merge via GitHub UI
  └── feature/my-work      ← your local changes, rebased after merge
```

Keep each concern on its own branch and merge in order:
**security PR first → then your feature work on top**.
