# HANDSHAKE-001 — Record

> Fill this in as you go. It is published with the data after the experiment. Times are in UTC.
> Never write any key, password or secret number into this file before the reveal.

## 1. Fixed parameters

| | |
|---|---|
| Registered T0 / T1 | 2026-10-12T08:00:00Z / 2026-10-12T11:00:00Z (10:00 / 13:00 CEST) |
| Postponements (n, reasons) | none |
| Effective T0 / T1 | same as registered |
| WAIT_HOURS | 3 |
| SHA-256 `PREREGISTRATION.md` | `f4c83cd7d93c9c90e2a3439ebfd833d271f8cde8678ec000b51cdd96db01fb06` (rechecked unchanged 2026-10-12 11:05 UTC, with `handshake.py` and `config.json`) |
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
| 3 | ANU draw VOID (no commitment exists) | X | https://x.com/DavonGluck/status/2109556900610334920 | 2026-10-12 08:08:53 UTC | https://archive.ph/09l9Z (text checked) | | — |
| 3b | ANU commitment | second platform | | | | | |
| 4 | IBM commitment | X | https://x.com/DavonGluck/status/2109556704207688099 (hashes checked against `public/ibm_commitment.txt`) | 2026-10-12 08:08:06 UTC | https://archive.ph/xOl2W (hashes checked) | | `public/ibm_commitment.txt.ots` |
| 4b | IBM commitment | second platform | | | | | |
| 5 | Target | X | https://x.com/DavonGluck/status/2109600561599533222 (text checked against `public/target.json`) | 2026-10-12 11:02:23 UTC (before the reveal at 11:03:04 UTC) | | NIST pulse page: https://web.archive.org/web/20261012110744/https://beacon.nist.gov/beacon/2.0/pulse/time/1791802800000 (value checked); x.com save refused (HTTP 523) | `public/target.json.ots` |
| 5b | Target | second platform | | | | | |
| 6 | Reveal | X | https://x.com/DavonGluck/status/2109600991993528819 (text checked against `public/reveal.json`) | 2026-10-12 11:04:05 UTC | | x.com save refused (HTTP 523) | — |
| 6b | Reveal | second platform | | | | | |
| 6c | Secondary N2 (T1+1h) | X | | | | | `public/secondary_N2.json.ots` |
| 6d | Secondary N3 (T1+24h) | X | | | | | `public/secondary_N3.json.ots` |
| 6e | Secondary N4 (T1+7d) + secondary report | X | | | | | `public/secondary_N4.json.ots` |
| 7 | Result summary (pinned) | X | | | | | |
| 7b | Result summary | second platform | | | | | |

## 4. Key data (from `public/`)

| | |
|---|---|
| Preflight runs (time → pass/fail) | 07:46:00–07:46:01 UTC FAIL (virtual environment not activated: IBM toolkit missing); 07:47:05–07:47:15 UTC PASS |
| ANU attempts (count, times) | 1 attempt, 08:00:01 UTC: HTTP 200 with malformed content → ambiguous → ANU VOID (§4) |
| IBM attempts and job IDs | 1 attempt, 08:00:03–08:00:12 UTC: db6972o4qg6s73c4e6k0 |
| Committed IBM job ID / backend | db6972o4qg6s73c4e6k0 / ibm_kingston |
| IBM created / running / finished | 08:00:11.97 / 08:00:16.86 / 08:00:29.74 UTC (server); committed 08:03:59 UTC |
| NIST target pulse (timestamp, chain, index) | 2026-10-12T11:00:00.000Z, chain 2, pulse 1980143 (fetched 11:01:02 UTC; link to previous pulse checked; independently re-fetched and matched) |
| T1 pulse missing? | no |
| Target (6 hex) | `02B168` |
| ANU number (after reveal) | none (ANU draw void; nothing was committed) |
| IBM number (after reveal) | `94FEC6` (salt and evidence published in `public/opened/ibm.json`; SHA-256 and SHA3-512 independently recomputed and matched the X commitment) |
| Result | **INCONCLUSIVE**: no hit (chance of a hit with one 24-bit draw: 2^-24 ≈ 6.0×10^-8). Revealed 11:03:04 UTC. `verify` with the hashes copied from the X post: `VERDICT: consistent - result INCONCLUSIVE` (11:05 UTC). |
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
| `PREREGISTRATION.md` | 2026-10-09 18:53 UTC | | |
| `handshake.py` | 2026-10-09 18:53 UTC | | |
| `config.json` | 2026-10-09 18:53 UTC | | |
| `public/anu_commitment.txt` | — (ANU void, no commitment) | | |
| `public/ibm_commitment.txt` | 2026-10-12 08:04 UTC | | |
| `public/target.json` | 2026-10-12 11:01 UTC | | |
| `public/secondary_N2.json` | | | |
| `public/secondary_N3.json` | | | |
| `public/secondary_N4.json` | | | |

## 7. Incidents, voids, interruptions

> Include every live-stream interruption (from–to, UTC) and every failed OpenTimestamps stamp.

| Time | What happened | What was done |
|---|---|---|
| 2026-10-12 07:46 UTC | First preflight run failed: the virtual environment was not activated, so the IBM toolkit was not found. | Activated `.venv`; second run at 07:47 passed. Both runs are in `public/preflight_log.json`. |
| 2026-10-12 08:00:01 UTC | ANU returned HTTP 200 but the reply failed validation. Classified as ambiguous under §4: no retry, ANU draw void, nothing committed. | Void recorded in `public/anu_void.json`; void announced on X at 08:08:53 UTC. IBM continued alone. |
| 2026-10-12 08:02:27 UTC | Post-void diagnostic (not a draw, nothing committed, number values not displayed): one ANU request returned HTTP 200, `success: true`, `type: uint8`, `length: "3"`, `data: []` (empty list). So ANU was returning an empty number list; the preflight at 07:47 had still received valid data. | Recorded here for transparency. Uses 1 request of the ANU quota. |
| 2026-10-12 ~08:18 UTC | The computer restarted unexpectedly (boot at 08:19:00 UTC). `public/` and `secret/ibm.json` were intact afterwards. Live stream and local recording were interrupted from about 08:18 UTC; the stream was restarted at about 10:55 UTC (12:55 CEST), before T1. | Nothing in the protocol depends on the stream; the IBM commitment had already been posted at 08:08 UTC. |
| 2026-10-12 08:31:10 UTC | Second post-void diagnostic: ANU returned HTTP 200 with 3 valid bytes (values not displayed). So ANU's empty replies were temporary: valid at 07:47 UTC, empty at 08:00:01 and 08:02:27 UTC, valid again by 08:31:10 UTC. | Not a draw, nothing committed; the ANU draw stays void as pre-registered. |
| 2026-10-09 19:00 UTC | `PREREGISTRATION.md` states "Published 2026-10-10", but GitHub, Zenodo and OpenTimestamps record its publication on 2026-10-09 (one day earlier). | Left unchanged: the document was already hashed, stamped and archived. The X post, Zenodo and OTS times are the evidence; an earlier real publication only strengthens the before-T0 claim. |
| | | |
