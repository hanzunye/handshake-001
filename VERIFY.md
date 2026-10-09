# How to verify HANDSHAKE-001

You do not need to trust the author, GitHub or this repository for the timing, the commitments, the target or the result: all of these can be checked independently, as described below. One thing cannot be checked by anyone but the author: that the numbers really came from ANU and IBM. That provenance is author-attested (see the end of §3).

## 1. The protocol was fixed before T0

1. Download `PREREGISTRATION.md` (from GitHub or Zenodo) and compute its hash:
   `shasum -a 256 PREREGISTRATION.md` (macOS) or `sha256sum PREREGISTRATION.md` (Linux).
2. Compare it with the hash in the author's pre-registration post on X. That post must be dated **before T0**.
3. Optionally, verify the OpenTimestamps proof (supplementary evidence; the X post time is primary). Without your own Bitcoin node, the easiest way is to drop `PREREGISTRATION.md` and `PREREGISTRATION.md.ots` onto https://opentimestamps.org. With a node, run `ots verify PREREGISTRATION.md.ots`. The same applies to every `*.ots` file below.
4. Check that `handshake.py` hashes to the value written in the pre-registration.

## 2. Both numbers were fixed before T1

1. Find the author's two commitment posts on X, `HANDSHAKE-001 ANU` and `HANDSHAKE-001 IBM`. Each must be dated **before T1 − 10 minutes**, and each lists a SHA-256 and a SHA3-512 hash.
2. Optionally: `ots verify public/anu_commitment.txt.ots` and `ots verify public/ibm_commitment.txt.ots`.
3. If either draw was declared void, the reason is published in `public/anu_void.json` or `public/ibm_void.json`.

## 3. The reveal matches the commitments, and the result is correct

Run the following, giving the hashes exactly as they appear in the X posts (not as they appear in this repository):

```
python3 handshake.py verify \
  --anu-sha256 <...> --anu-sha3-512 <...> \
  --ibm-sha256 <...> --ibm-sha3-512 <...>
```

The verify step uses only the Python standard library; Qiskit is not needed. It recomputes every hash from the revealed numbers and salts, recomputes each draw's EVIDENCE digest from its bundle in `public/opened/` (a missing bundle counts as a failure), **fetches the target independently**, and recomputes the result. The target is the first NIST Randomness Beacon pulse stamped at or after T1. NIST is the only source, and NIST's archive is permanent, so every verifier gets the same pulse at any time. Void draws whose commitments exist are opened and their hashes checked, but they are not scored. If the experiment was postponed, T0 and T1 shift by 24 hours per entry in `public/postponements.json`; the script applies this automatically.

You can also do it by hand. `number`, `evidence` and `salt` are in `public/reveal.json`:

```
printf '%s' 'HANDSHAKE-001|DRAW=ANU|NUMBER=<number>|EVIDENCE=<evidence>|SALT=<salt>' | shasum -a 256
printf '%s' 'HANDSHAKE-001|DRAW=ANU|NUMBER=<number>|EVIDENCE=<evidence>|SALT=<salt>' | openssl dgst -sha3-512
```

Repeat with `DRAW=IBM` for the IBM draw. EVIDENCE is the SHA-256 of the `draw_info` object in `public/opened/anu.json` (or `ibm.json`), serialised as JSON with sorted keys, no spaces (`,` and `:` as separators) and ASCII escaping; the verify script recomputes it. Then open `https://beacon.nist.gov/beacon/2.0/pulse/time/<T1 in milliseconds>`. NIST returns the first pulse at or after T1, which is the target. Compare the first 6 characters of its `outputValue` with each number.

### What this does and does not prove

The commitments prove that each number was fixed before the target existed, and the EVIDENCE digest proves that the raw ANU response and IBM job record in `public/opened/` were not changed after the commitment. They cannot prove that the numbers came from ANU and IBM: ANU responses are unsigned, and IBM job records are visible only to the account holder. That provenance is **author-attested**, as stated in the pre-registration.

## 4. Nothing was hidden

The pre-registration requires that every attempt and every void draw be disclosed. Check the author's account for any other commitment posts for this experiment.

## 5. The attempt log is complete

`public/preflight_log.json` lists every preflight run, `public/postponements.json` lists every postponement, and every ANU and IBM attempt is listed in that draw's commitment file (`public/anu_commitment.json`, `public/ibm_commitment.json`) or, if the draw was void, in its void file (`public/anu_void.json`, `public/ibm_void.json`). Every IBM submission and job ID is also in `public/ibm_job.json`, and `public/events.jsonl` logs every step as it happened. `start` must have run only after a preflight that passed and that both began and ended inside the window T0 − 30 min to T0 − 2 min. `public/events.jsonl` is the running log of every step.

## 6. Secondary analysis (N2, N3, N4)

`python3 handshake.py verify` also re-derives the secondary schedule from NIST's archive. N2, N3 and N4 sit at nominal offsets of +1 h, +24 h and +7 days from T1, chained so that a missing pulse shifts every later time by the same delay. The script checks that each re-fetched pulse equals the saved file for it (pulse time and value), then recomputes the comparisons (12 when both draws are valid, fewer if a draw is void) and checks the full comparison list, the matches, the count and the approximate chance against `public/secondary.json`. Each secondary value is also saved on its own in `public/secondary_N2.json`, `secondary_N3.json` and `secondary_N4.json`, each with an OpenTimestamps proof; `verify --offline` uses these instead of fetching from NIST. By hand: N(k) = the first pulse returned by `https://beacon.nist.gov/beacon/2.0/pulse/time/<scheduled time in ms>`, where the scheduled time = the timeStamp of N(k−1) + the gap between the nominal offsets.

