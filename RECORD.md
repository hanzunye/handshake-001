# HANDSHAKE-001 — Record

> Fill this in as you go. It is published with the data after the experiment. Times are in UTC.
> Never write any key, password or secret number into this file before the reveal.

## 1. Fixed parameters

| | |
|---|---|
| Registered T0 / T1 | 2026-10-12T08:00:00Z / 2026-10-12T11:00:00Z (10:00 / 13:00 CEST) |
| Postponements (n, reasons) | |
| Effective T0 / T1 | |
| WAIT_HOURS | 3 |
| SHA-256 `PREREGISTRATION.md` | |
| SHA-256 `handshake.py` | `21352f760902d51c952bfa12c0fccea06ad3434d246e43decaf6d2ae89c38c17` (frozen 2026-10-09) |
| SHA-256 `config.json` | `c1b236f4201b87c1c4dc73cd592da9af94952e9943b89b2e1201a877c3c2c056` |
| GitHub repository | https://github.com/hanzunye/handshake-001 |
| Zenodo DOI (pre-registration) | 10.5281/zenodo.23269344 (release v1.0-prereg, archived 2026-10-09 19:00 UTC; file hashes checked) |
| YouTube live URL | https://youtube.com/live/Czs_cNhEQR0 (scheduled 2026-10-12 07:25 UTC) |
| Local recording file | |

## 2. IBM queue-time trials (before the experiment)

| Date / time | Backend | Queued | Running | Total | Notes |
|---|---|---|---|---|---|
| 2026-10-05 21:07 | ibm_kingston | ~1.6 s | ~4.6 s | 8.8 s | idle time of day |
| 2026-10-09 17:17 UTC | ibm_fez | 1.7 s | 9.9 s | 11.5 s | real rehearsal (`rehearse --anu anu --ibm real`), server timestamps |
| | | | | | |
| | | | | | |

## 3. Posts and archives

| # | Content | Platform | Post URL | Posted at | archive.ph | web.archive.org | OTS file |
|---|---|---|---|---|---|---|---|
| 1 | Pre-registration (pinned) | X | https://x.com/DavonGluck/status/2108645176260313365 | 2026-10-09 19:46:01 UTC | https://archive.ph/XKAfI (hash checked) | https://web.archive.org/web/20261009195954/https://publish.x.com/oembed?url=https:%2F%2Ftwitter.com%2FDavonGluck%2Fstatus%2F2108645176260313365 (oEmbed; x.com itself refused) | `PREREGISTRATION.md.ots` |
| 1b | Pre-registration | second platform | | | | | |
| 2 | Postponement (if any) | X | | | | | |
| 3 | ANU commitment | X | | | | | `public/anu_commitment.txt.ots` |
| 3b | ANU commitment | second platform | | | | | |
| 4 | IBM commitment | X | | | | | `public/ibm_commitment.txt.ots` |
| 4b | IBM commitment | second platform | | | | | |
| 5 | Target | X | | | | | `public/target.json.ots` |
| 5b | Target | second platform | | | | | |
| 6 | Reveal | X | | | | | |
| 6b | Reveal | second platform | | | | | |
| 6c | Secondary N2 (T1+1h) | X | | | | | `public/secondary_N2.json.ots` |
| 6d | Secondary N3 (T1+24h) | X | | | | | `public/secondary_N3.json.ots` |
| 6e | Secondary N4 (T1+7d) + secondary report | X | | | | | `public/secondary_N4.json.ots` |
| 7 | Result summary (pinned) | X | | | | | |
| 7b | Result summary | second platform | | | | | |

## 4. Key data (from `public/`)

| | |
|---|---|
| Preflight runs (time → pass/fail) | |
| ANU attempts (count, times) | |
| IBM attempts and job IDs | |
| Committed IBM job ID / backend | |
| IBM created / running / finished | |
| NIST target pulse (timestamp, chain, index) | |
| T1 pulse missing? | |
| Target (6 hex) | |
| ANU number (after reveal) | |
| IBM number (after reveal) | |
| Result | |
| N2 / N3 / N4 (pulse time, value, shift) | |
| Secondary matches (of n comparisons) | |

## 5. Backups of secret files

| File | Location | Copied at |
|---|---|---|
| `secret/anu.json` | USB | |
| `secret/anu.json` | encrypted cloud | |
| `secret/ibm.json` | USB | |
| `secret/ibm.json` | encrypted cloud | |

## 6. OpenTimestamps

| File | Stamped at | Upgraded at (`ots upgrade`) | Verified at (opentimestamps.org) |
|---|---|---|---|
| `PREREGISTRATION.md` | | | |
| `handshake.py` | | | |
| `config.json` | | | |
| `public/anu_commitment.txt` | | | |
| `public/ibm_commitment.txt` | | | |
| `public/target.json` | | | |
| `public/secondary_N2.json` | | | |
| `public/secondary_N3.json` | | | |
| `public/secondary_N4.json` | | | |

## 7. Incidents, voids, interruptions

> Include every live-stream interruption (from–to, UTC) and every failed OpenTimestamps stamp.

| Time | What happened | What was done |
|---|---|---|
| 2026-10-09 19:00 UTC | `PREREGISTRATION.md` states "Published 2026-10-10", but GitHub, Zenodo and OpenTimestamps record its publication on 2026-10-09 (one day earlier). | Left unchanged: the document was already hashed, stamped and archived. The X post, Zenodo and OTS times are the evidence; an earlier real publication only strengthens the before-T0 claim. |
| | | |
