# HANDSHAKE-001: A Pre-registered Single-Shot Test for Information Arriving from the Future

| | |
|---|---|
| Author | Han Yunze (X: @DavonGluck) |
| Document version | 3.2 (dual draw; NIST-only target; preflight and postponement rules; secondary NIST analysis) |
| Published | 2026-10-10 |
| Code | `handshake.py`, SHA-256 `21352f760902d51c952bfa12c0fccea06ad3434d246e43decaf6d2ae89c38c17` |

The SHA-256 of this file is posted on X by @DavonGluck and timestamped with OpenTimestamps **before T0**. That post and its timestamp, not any git history, establish that this protocol was fixed in advance.

---

## 1. Summary

This is a **single attempt** with **two independent quantum draws**, both made at T0. Each draw produces a 24-bit number, which is committed with a cryptographic hash and kept hidden:

- **ANU:** the Australian National University quantum random number service.
- **IBM:** 24 qubits on an IBM Quantum processor, each prepared in superposition and measured once.

At T1, 3 hours after T0, the **NIST Randomness Beacon** publishes a value that nobody could predict at T0. NIST is the only target source; there is no alternative or backup source. A draw is a **HIT** if its 6 hexadecimal characters equal the first 6 characters of that NIST value.

Under ordinary physics, each draw hits with probability 2⁻²⁴ (1 in 16,777,216). The probability that at least one of the two hits is about 1 in 8,388,608. The probability that both hit is 2⁻⁴⁸.

Three later NIST pulses (N2, N3, N4), taken about 1 hour, 24 hours and 7 days after T1, are compared with the already-public values in a **separate, secondary analysis** (§6.2). It asks whether the NIST beacon itself can be influenced, and it never changes the primary result.

## 2. Motivation and stance

The author is exploring a speculative idea: that information, though not matter, might reach earlier times through a channel outside ordinary spacetime, and might show up only as a selection among outcomes that were genuinely open, such as a quantum measurement. This is **not** established physics, and known physics predicts a chance-level result. The purpose of this protocol is narrow: to make one clean, transparent, fully pre-specified test that anyone can check.

There are two sources because there are two ways such information might act:

- **As a condition on the final recorded number.** Either source can show this.
- **As small biases on individual quantum events.** The ANU service passes its raw measurements through a cryptographic hash, which would erase such biases. IBM returns 24 raw projective measurements, one bit per event, with no hashing.

## 3. Hypotheses

- **H0 (chance):** the target's first 24 bits are uniformly distributed and independent of both draws and of every scheduling decision (retries, postponements). Then P(HIT) = 2⁻²⁴ per draw, whatever the distribution of the draw. The double-hit figure 2⁻⁴⁸ additionally assumes that the ANU draw is uniform and independent of the IBM draw (P(double hit) = 2⁻²⁴ × P(ANU = IBM)). These are ideal-model assumptions about the sources, not properties this protocol can guarantee.
- **H1 (information from a later time):** information about the target reaches a draw at T0 from some later time, raising its P(HIT) above 2⁻²⁴.

## 4. Fixed parameters

| Parameter | Value |
|---|---|
| Experiment ID | `HANDSHAKE-001` |
| T0 | `2026-10-12T08:00:00Z` (UTC, whole minute; 10:00 in Germany, CEST), plus 24 hours for each postponement declared under §5.2 |
| T1 | `2026-10-12T11:00:00Z` (13:00 CEST) = T0 + 3 hours, shifted together with T0. The wait was chosen in advance from IBM queue-time trials, to leave ample margin |
| Preflight window | T0 − 30 min to T0 − 2 min (§5.1) |
| Start window | T0 − 1 min to T0 + 10 min, for the ANU draw and the IBM submission |
| IBM deadline | the IBM job that is committed must have finished by T1 − 30 min |
| Commitment deadline | every commitment must be posted on X by T1 − 10 min |
| Number size | 24 bits, written as 6 uppercase hexadecimal characters |
| **ANU draw** | A request to the ANU Quantum Random Numbers API with `length=3`, `type=uint8`. **Up to 10 attempts** are allowed, all inside the start window, with waits of 5, 10, 15, 20, 30, 30, 45, 60 and 60 seconds between them. A further attempt is made only if the previous one **definitely returned no number** (no HTTP response, an error status, or a reply without a data field). A reply that might contain numbers but is malformed is treated as ambiguous: there is no retry, and the ANU draw is void. Response bodies are never displayed. Every attempt is logged immediately and published. The 3 bytes are written as two-digit uppercase hex and concatenated, e.g. `[163, 240, 156]` → `A3F09C` |
| **IBM draw** | The least busy operational IBM Quantum processor with at least 24 qubits at the moment of each submission (no simulators). Circuit: 24 qubits, a Hadamard gate on each, then each qubit measured into classical bits `c[0]`…`c[23]`. Transpiled with optimisation level 1 and run with the SamplerV2 primitive, `shots=1`. **Up to 10 attempts in total**: retries of a failed submission inside the start window, and resubmissions after a job that ended in error or was cancelled by IBM, allowed until T1 − 35 min. A job that ended this way produced no visible number, so a resubmission cannot select an outcome. Every submission carries a unique tag. If a submission call fails after it may have reached IBM, the account is searched for that tag: a job that is found is adopted, a confirmed absence allows a retry, and an undecidable state voids the IBM draw. **Deadlines are judged by IBM's server timestamps**: the committed job must have been created by T1 − 35 min and finished by T1 − 30 min, and if these timestamps are missing the IBM draw is void. The IBM draw is the one job that completes successfully; its ID is published in the IBM commitment post, and every job ID and attempt is published in `public/ibm_job.json`. The returned 24-character bitstring (leftmost character = `c[23]`) is read as a binary number and written as 6 uppercase hex. Software versions are pinned in `requirements.txt` (qiskit 2.5.2, qiskit-ibm-runtime 0.50.0) |
| Salt | 256 bits per draw, from the operating system's CSPRNG, as 64 lowercase hex characters |
| Committed messages (ASCII, no newline) | `HANDSHAKE-001\|DRAW=<ANU or IBM>\|NUMBER=<6 hex>\|EVIDENCE=<64 hex>\|SALT=<64 hex>`. EVIDENCE is the SHA-256 of the canonical JSON of the full evidence bundle for that draw (raw ANU response and attempt log; IBM job ID, backend, attempts, bitstring, server timestamps, circuit and software versions). The bundle is published at the reveal (`public/opened/`), so the evidence is bound to the commitment. Whether the numbers truly came from ANU and IBM remains **author-attested**: ANU responses are unsigned, and IBM records are visible only to the account holder |
| Commitment | SHA-256 and SHA3-512 of each committed message, both published |
| **Target (the only source)** | **The first pulse of the NIST Randomness Beacon 2.0 whose `timeStamp` is equal to or later than T1.** Normally this is the pulse stamped exactly T1. If NIST skipped that minute, it is the next pulse NIST published. Target = first 6 characters of its `outputValue`, uppercased. This is exactly what `https://beacon.nist.gov/beacon/2.0/pulse/time/<T1 in milliseconds>` returns, so anyone, at any later time, gets the same pulse. If NIST is unreachable, or has not yet published any pulse at or after T1, the tool waits and retries; **the target is never replaced by anything else** |
| **Secondary targets N2, N3, N4** (§6.2) | Nominal offsets from T1: **+1 h, +24 h, +7 × 24 h**. Each is the first NIST pulse at or after its scheduled time, and the schedule is chained: the scheduled time of N(k) = the actual timeStamp of the pulse used for N(k−1) + (nominal offset of N(k) − nominal offset of N(k−1)), with N1 as the start. If a scheduled minute has no pulse, the next published pulse is used and **all later scheduled times move by the same delay**. Value = first 6 characters of `outputValue`, uppercased. Nothing is requested from the future for these pulses |

## 5. Procedure

**Before the first T0**
1. Publish this document and `handshake.py` (GitHub and Zenodo). Post the SHA-256 of this document on X, timestamp it with OpenTimestamps, and archive the post.
2. Rehearsals and IBM queue-time trials are allowed only against targets that were already published. Rehearsals use the ID `HANDSHAKE-001-REHEARSAL`; queue-time trials carry the IBM job tag `HANDSHAKE-001-TRIAL`. Both are labelled as such and never count.

**Between T0 − 30 min and T0 − 2 min**
3. Run `python3 handshake.py preflight` and require it to pass (§5.1).

**At T0** (live-streamed)
4. Run `python3 handshake.py start`. It refuses to run without a passing preflight inside the preflight window. It draws and commits the ANU number (the number is not displayed), then submits the IBM job. Post the ANU commitment on X as text, timestamp it, and back up the secret file.
5. Run `python3 handshake.py commit-ibm`. It waits for the IBM job, resubmits if the rules in §4 allow, and commits the result as soon as a job completes (the number is not displayed). Post the IBM commitment, including the job ID, on X; timestamp it; back up the secret file.

**At T1** (live-streamed)
6. At or after T1 + 1 min, run `python3 handshake.py fetch-target`. Show the NIST pulse on NIST's website, post it, and timestamp `public/target.json`.

**After T1**
7. Run `python3 handshake.py reveal` and post both numbers and salts. Publish all files in `public/`, including the opened secret files in `public/opened/` (raw ANU response, IBM bitstring and timestamps), and the stream recordings.
8. From 1 minute after each secondary target's scheduled time (N2 ≈ T1 + 1 h, N3 ≈ T1 + 24 h, N4 ≈ T1 + 7 days; the tool refuses earlier, so that NIST has had time to publish), run `python3 handshake.py fetch-secondary` and post the value. After N4, the same command writes the secondary report (`public/secondary.json`), which is posted and published. Secondary targets need no live stream: NIST's archive is permanent and the rule fixes every value.

### 5.1 Preflight self-check (contingency plan)

The preflight verifies that nothing in **our own mechanism** will prevent the three numbers (ANU, IBM, NIST) from being obtained. It reveals nothing about any outcome. It may be repeated any number of times inside the preflight window, and **every run is logged in `public/preflight_log.json` and disclosed**, with its start and end times and the software environment. `start` proceeds only if at least one run inside the window passed every required check:

| Check | Required |
|---|---|
| The run both began and ended inside the preflight window | yes |
| `start` has not been run | yes |
| No secret from an earlier draw exists | yes |
| The SHA-256 of `handshake.py` equals the value registered at the top of this document | yes |
| The `PYTHONPATH` environment variable is unset or empty | yes |
| The computer clock is within 10 s of NIST's server time | yes |
| The NIST beacon is publishing: its latest pulse is at most 3 minutes old | yes |
| The ANU key and service work. This uses one request; the number is discarded unseen and never committed | yes |
| IBM is reachable and an operational QPU with ≥ 24 qubits is available | yes |
| At least 60 s of IBM quota remains | yes |
| The installed qiskit and qiskit-ibm-runtime versions equal the pinned versions | yes |
| The OpenTimestamps tool is installed | no (advisory) |

### 5.2 Postponement

If no preflight has passed by T0 − 2 min, or something outside the protocol prevents the author from running the attempt (for example a power cut, illness, or announced IBM or NIST maintenance), the author does **not** run `start`. Instead:

- The author runs `python3 handshake.py postpone --reason "..."`. This moves **T0 and T1 together by exactly 24 hours**. The reason and new times are recorded in `public/postponements.json` and posted on X before the start window closes (T0 + 10 min). A postponement declared later is not valid.
- A postponement is possible only **before `start` has run**. Before `start`, no number exists, so a postponement cannot select an outcome.
- At most **7** postponements are allowed. After that, the attempt is void.
- After a postponement, the preflight, start and target rules apply to the new T0 and T1.

## 6. Decision rule

Each valid draw is scored separately. A draw is a hit if and only if its 6 characters equal the 6 target characters exactly. There is no partial credit.

| Outcome | Meaning | Chance probability with 2 valid draws |
|---|---|---|
| **DOUBLE HIT** | both draws hit | 2⁻⁴⁸ ≈ 3.6 × 10⁻¹⁵ |
| **HIT (ANU)** or **HIT (IBM)** | exactly one draw hits | ≈ 1.2 × 10⁻⁷ for at least one hit |
| **INCONCLUSIVE** | no draw hits | — |

A single attempt **cannot refute H1**. A miss is expected even if H1 is true but such a channel is weak, unreliable, or unused. If a HIT occurs, the author will **not** claim it as proof. The next steps are fixed now: (a) look for mundane causes such as code errors, timing errors or a compromised source; (b) publish all data and code; (c) invite independent replication.

### 6.1 How each outcome pattern will be interpreted

These interpretations are fixed now, before any data exist.

**Where could the information land?** A hit shows a correlation, beyond chance, between a draw made at T0 and a value published at T1. Under H1, that information could have reached either of two places: one of our draws at T0, or the NIST beacon's own random generation shortly before T1. Both are open physical outcomes. In NIST's case, the influence would make its value equal a number that is revealed only after T1. Neither route is a mundane loophole. NIST cannot know our salted numbers before the reveal, and ANU and IBM cannot know the NIST value at T0, so both routes would themselves be anomalous. The NIST output, like the ANU output, is a cryptographic hash of its raw randomness. Small per-event biases would therefore be erased there too; only influence acting as a condition on the final value could reach it.

| Pattern | Interpretation under H1 |
|---|---|
| **DOUBLE HIT** | Information reached **at least one of our draws**. Influencing NIST alone cannot produce it: NIST's value can equal only one number, so a double hit would also require ANU = IBM, which has probability 2⁻²⁴. This is the pattern H1 predicts if information acts as a condition on the final recorded number and was delivered to both draws, as the request in §9 asks. |
| **HIT (IBM) only** | Either small biases acting on IBM's individual quantum events (which ANU's and NIST's hashing would erase), or a condition on the final value acting at IBM or at NIST. A single attempt cannot tell these apart. |
| **HIT (ANU) only** | A condition on the final value acting at ANU or at NIST. As with every hit, the search for an error comes first. |
| **INCONCLUSIVE** | The expected outcome. If each draw is reached with some small probability r, a double hit requires r². |

**What a DOUBLE HIT would and would not settle.** Under H0 its probability is 2⁻⁴⁸ ≈ 3.6 × 10⁻¹⁵, roughly the odds of winning a national lottery jackpot twice in a row with one ticket each time.

- **Chance:** excluded.
- **Software or timing error:** effectively excluded by design. Both numbers are committed and publicly posted hours before the target exists. The tool reads no pulse at or after T1 before T1 + 1 min; the preflight reads only the latest pulse already published before T0, to confirm the beacon is running. An error would therefore have needed knowledge of a value that had not yet been generated. The integrity checks in §8 must still pass.
- **Fraud or collusion:** **not** excluded for outside observers. To someone who does not know the author, deliberate manipulation remains far more probable than 10⁻¹⁵. Only independent execution or replication by others can remove this explanation. The author regards a double hit with all checks passing as decisive for the author's own conclusion, and will state openly that it is not decisive for others.
- **Mechanism:** not established. A double hit would show that some correlation with a later-published value exists. It would not confirm any particular model of how that correlation arises.

### 6.2 Secondary analysis: can the NIST beacon itself be influenced?

By the time N2, N3 and N4 (§4) are generated, the ANU number, the IBM number and N1 are all public. If the NIST beacon can be influenced, a later pulse might come to equal one of these values. The analysis is passive: nothing is requested from the future for these pulses (§9).

- **Comparisons (all fixed now):** N2 against N1, ANU and IBM; N3 against N1, N2, ANU and IBM; N4 against N1, N2, N3, ANU and IBM. That is **12 comparisons** when both draws are valid, fewer if a draw is void; void draws are not used. A comparison is a match if and only if the 6 characters are identical.
- **Chance:** under ordinary physics, the probability of at least one match among 12 comparisons is approximately 7.2 × 10⁻⁷ (about 1 in 1.4 million; this treats the comparisons as independent, which they are not exactly). The approximate figure for the actual number of comparisons is reported.
- **Separate from the primary result.** Secondary matches are reported on their own (`public/secondary.json`) and never change the primary outcome of §6.
- **What a match would mean:** that the beacon's output can be steered towards an already-public value, which would make NIST a possible landing place for the primary hits in §6.1. It would **not** by itself show that information travels to earlier times, because these values were already public when the later pulses were generated. A match with N1 alone (with no draw involved) would mean the beacon can be influenced independently of our draws.
- **No match** is the expected outcome and refutes nothing.

## 7. Validity conditions

- **A draw is void** if its source fails after all allowed attempts, if its commitment is not posted on X by T1 − 10 min, or if its secret file is lost before the reveal.
- **The IBM draw is also void** if no job completed on real quantum hardware by T1 − 30 min, judged by IBM's server timestamps, or if those timestamps are missing. A job that is still queued or running at that time is cancelled.
- **A draw is also void** if its state becomes ambiguous (§4): a malformed ANU reply that might contain numbers, or an IBM submission whose existence cannot be decided.
- **If one draw is void**, the other proceeds alone, and its chance probability is 2⁻²⁴.
- **The attempt is void** in any of these cases: both draws are void; `start` is run without a passing preflight inside the window; the start window closes without `start` and without a postponement; or the limit of 7 postponements is exceeded.
- Some voids, such as a commitment posted late on X, cannot be detected by the tool. The author records them with `python3 handshake.py void --draw <ANU|IBM> --reason "..."` before the reveal. A void draw whose commitment exists is still opened at the reveal, for transparency, but it is **never scored**.
- `start` may be run **only once**, even if all of its draws turned out void. A second confirmatory draw from the same source is not allowed.
- Every void, every postponement and every preflight run is **reported publicly, never hidden**. Any later attempt receives a new ID and its own pre-registration, and the total number of attempts is always disclosed.

## 8. Integrity measures

- **Hiding:** each 24-bit number is committed together with a secret 256-bit salt. The commitment is computationally hiding: recovering the number requires guessing the salt, about 2²⁵⁶ trials for a classical computer or about 2¹²⁸ for a quantum (Grover) search, both far beyond any feasible computation.
- **Binding:** two hash families are used (SHA-2 and SHA-3), and both hashes are published. Changing a number after it was committed would require finding a second message with the same SHA-256 and the same SHA3-512, which is believed infeasible.
- **Evidence binding:** each committed message contains the SHA-256 of that draw's evidence bundle (§4), so the raw ANU response and the IBM job record published at the reveal cannot be altered afterwards. That they came from ANU and IBM remains author-attested.
- **Time evidence:** the primary evidence is the X post times, preserved by Internet Archive or archive.today snapshots. Supplementary evidence: OpenTimestamps proofs anchored in Bitcoin (a failed or missing stamp is recorded but does not void a draw) and the Zenodo record. IBM's server timestamps (created, running, finished) are also recorded and shown on stream; they are visible only to the account holder, and the commitment chain does not depend on them. Git commit dates are **not** evidence.
- **Transparency:** the T0 and T1 segments are live-streamed as supplementary evidence; any interruption of the stream is recorded with its times, and does not by itself void a draw. The code is open; all data, attempt logs, preflight logs and postponements are published after the reveal.
- **Target integrity:** each NIST pulse is signed by NIST and hash-chained to earlier pulses, and its chain and pulse index are recorded. The tool checks the pulse's format, that the previous pulse is stamped before T1, and that the pulse's `previous` value equals the previous pulse's `outputValue`; it does not verify NIST's signature. The target pulse is also archived (OpenTimestamps and a web archive) immediately after it is fetched.

## 9. A request to the future

> To anyone, at any time (perhaps after 2048), who is able to send information to an earlier time:
>
> Please send the **6 characters** of the target to **both** draws of **HANDSHAKE-001**. The target is the first six hexadecimal characters of the `outputValue` of the **first NIST Randomness Beacon pulse stamped at or after `2026-10-12T11:00:00Z` UTC**. If this experiment was postponed, T1 is that time plus 24 hours for each postponement listed in `public/postponements.json`. The two draws are:
> - the ANU QRNG draw made at `2026-10-12T08:00:00Z` UTC (same postponement rule), whose attempt log is in the ANU commitment file;
> - the IBM Quantum job whose ID is given in the HANDSHAKE-001 IBM commitment post.
>
> The value is permanently archived by NIST and in this experiment's public records. Later NIST pulses (N2–N4) are also examined in a secondary analysis, but nothing is asked of you for them.
>
> To keep this as safe as possible for you:
> - The message is only 24 bits.
> - The value has no practical use. Sending it cannot advantage or harm anyone.
> - You do not need to identify yourself.
> - Please do nothing unsafe, unlawful, or against your own judgement. If you cannot, or choose not to, that is completely fine.
>
> Thank you.

## 10. Availability

All code, data, timestamps, logs, and stream recordings are released under CC0 1.0 (public domain dedication) after the reveal.
