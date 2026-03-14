# Admin Runbooks

This directory contains operational runbooks for platform administrators and founders.

**All `*.md` files in this directory are git-ignored** and must never be committed
to the repository. The runbooks contain credentials, internal URLs, and access
procedures that must not be visible to anyone with read access to the repo.

## Documents in this directory (local-only)

| File | Contents |
|---|---|
| `ADMIN-RUNBOOK.md` | Master admin reference — env vars, secrets, access control, deploy procedure |

## Where to get them

Runbooks are stored in the team's secure channel. Contact the founder / lead engineer:

- **Primary:** 1Password vault → "LedgerLite Ops" collection
- **Backup:** Shared private Notion page (access via invite only)

## What to do if you need access

1. Request access from the founder via the team Slack `#ops` channel
2. You will be granted read-only access to the specific runbook you need
3. Never copy credentials into chat messages, emails, or public tickets

## Security reminder

If you accidentally commit any file from this directory:

```bash
# Remove it from git history immediately
git rm --cached docs/admin/<filename>
git commit -m "chore: remove accidentally committed admin doc"
git push

# Then rotate ALL credentials mentioned in the file
# Notify the security lead immediately
```
