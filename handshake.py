#!/usr/bin/env python3
"""Tooling for HANDSHAKE-001 (dual draw: ANU + IBM; target: NIST Randomness Beacon only).
Implements PREREGISTRATION.md.

    python3 handshake.py setup-ibm        # once: save your IBM API key on this computer (typed hidden)
    python3 handshake.py ibm-check        # check the IBM connection and list usable QPUs (no quota used)
    python3 handshake.py ibm-trial        # measure the IBM queue time (uses a few seconds of quota)
    python3 handshake.py preflight        # between T0-30min and T0-2min: the pre-registered self-check
    python3 handshake.py postpone --reason "..."   # before start: move T0 and T1 by exactly 24 h (max 7)
    python3 handshake.py start            # at T0: ANU draw + commitment, then submit the IBM job
    python3 handshake.py commit-ibm       # right after start: wait for the IBM job, then commit its result
    python3 handshake.py fetch-target     # at or after T1 + 1 min: fetch the NIST target
    python3 handshake.py reveal           # after fetch-target: open the commitments and report the result
    python3 handshake.py fetch-secondary  # after T1+1h, T1+24h, T1+7d: fetch N2, N3, N4; then the secondary report
    python3 handshake.py void --draw IBM --reason "..."   # record a void the tool cannot see (e.g. late X post)
    python3 handshake.py verify           # anyone: check commitments, target and result independently
    python3 handshake.py rehearse         # dry run against an already-published target (never a test)

The ANU part, fetch-target, reveal and verify use only the standard library.
The IBM parts need the versions pinned in requirements.txt.
"""
import argparse
import hashlib
import json
import math
import os
import platform
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

VERSION = "3.2"
ROOT = Path(__file__).resolve().parent
NUMBER_BITS = 24
NUMBER_HEX_LEN = 6
HEX6 = re.compile(r"[0-9A-F]{6}")
NIST_OUTPUT = re.compile(r"[0-9A-Fa-f]{128}")
CHANCE_ONE = 2 ** -24
POST_LIMIT = 280
DRAWS = ("ANU", "IBM")

ANU_URL = "https://api.quantumnumbers.anu.edu.au?length=3&type=uint8"
ANU_KEY_FILE = Path.home() / ".anu_qrng_key"  # outside the repository, chmod 600
NIST_TIME_URL = "https://beacon.nist.gov/beacon/2.0/pulse/time/{ms}"
NIST_INDEX_URL = "https://beacon.nist.gov/beacon/2.0/chain/{chain}/pulse/{index}"
NIST_LAST_URL = "https://beacon.nist.gov/beacon/2.0/pulse/last"

START_OPENS = timedelta(minutes=-1)       # start window, relative to T0
START_CLOSES = timedelta(minutes=10)
PREFLIGHT_OPENS = timedelta(minutes=-30)  # preflight window, relative to T0 (start and finish must lie inside)
PREFLIGHT_CLOSES = timedelta(minutes=-2)
IBM_DONE_BY = timedelta(minutes=30)       # the committed IBM job must have finished (server time) by T1 - this
IBM_RESUBMIT_MARGIN = timedelta(minutes=5)  # every IBM job must be created (server time) by T1 - 35 min
COMMIT_DEADLINE = timedelta(minutes=10)   # every commitment must be posted by T1 - this
MIN_WAIT = timedelta(hours=1)             # T1 - T0 must be at least this
TARGET_EARLIEST = timedelta(minutes=1)    # fetch-target refuses before T1 + this
POSTPONE_STEP = timedelta(hours=24)
MAX_POSTPONEMENTS = 7
MAX_ATTEMPTS = 10                         # per source (ANU requests; IBM submissions incl. resubmissions)
RETRY_WAITS = [5, 10, 15, 20, 30, 30, 45, 60, 60]  # seconds between attempts 1-2, 2-3, ..., 9-10
CLOCK_TOLERANCE_S = 10
NIST_FRESH = timedelta(minutes=3)
IBM_MIN_QUOTA_S = 60
OTS_TIMEOUT_S = 120                        # a stamp that takes longer is abandoned (supplementary only)
IBM_POLL_SECONDS = 30
# Secondary NIST targets (PREREGISTRATION.md §6.2): nominal offsets from T1. Each one is scheduled at
# (actual time of the previous pulse) + (gap between nominal offsets), so a late pulse shifts all later ones.
SECONDARY = [("N2", timedelta(hours=1)), ("N3", timedelta(hours=24)), ("N4", timedelta(days=7))]


# --- small helpers -----------------------------------------------------------

def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)


def die(msg):
    print(f"\nSTOP: {msg}", file=sys.stderr)
    sys.exit(1)


def read_json(path, default=None):
    path = Path(path)
    if default is not None and not path.exists():
        return default
    return json.loads(path.read_text())


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def write_json(path, data, private=False):
    """Atomic write: temp file in the same directory, flush + fsync, then rename.
    Private files are created 0600 from the start, inside a 0700 directory."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if private:
        os.chmod(path.parent, 0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")  # mkstemp creates it 0600
    try:
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(data, indent=2, default=str) + "\n")
            f.flush()
            os.fsync(f.fileno())
        if not private:
            os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def append_event(base, kind, **data):
    """Append-only event log (public/events.jsonl). Never contains a hidden number."""
    path = Path(base) / "public" / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(canonical_json({"at_utc": iso(utcnow()), "event": kind, **data}) + "\n")
        f.flush()
        os.fsync(f.fileno())


def http_get(url, headers=None, timeout=20):
    """One GET. Returns (status, body, response_headers). status is None when no HTTP response arrived."""
    req = urllib.request.Request(url, headers={"User-Agent": f"handshake-001/{VERSION}", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace"), dict(e.headers or {})
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return None, str(e), {}


def attempt_loop(fn, label, deadline=None, max_attempts=MAX_ATTEMPTS, first_n=1, on_attempt=None):
    """Call fn() -> (state, value, detail) with state in {"ok", "retry", "ambiguous"}.
    "retry" means the attempt definitely produced no number; "ambiguous" stops at once (no retry).
    Never starts an attempt after `deadline`. Returns (value or None, attempts, final_state)."""
    attempts = []
    for i in range(max_attempts):
        n = first_n + i
        if deadline and utcnow() >= deadline:
            attempts.append({"n": n, "at_utc": iso(utcnow()), "state": "not_started", "detail": "deadline passed"})
            return None, attempts, "deadline"
        at = iso(utcnow())
        state, value, detail = fn(n)
        attempts.append({"n": n, "at_utc": at, "state": state, "detail": detail})
        if on_attempt:
            on_attempt(attempts[-1])
        if state == "ok":
            return value, attempts, "ok"
        if state == "ambiguous":
            return None, attempts, "ambiguous"
        if i == max_attempts - 1:
            break
        wait = RETRY_WAITS[min(i, len(RETRY_WAITS) - 1)]
        print(f"{label}: attempt {n} produced no number ({detail[:80]}); retrying in {wait}s")
        time.sleep(wait)
    return None, attempts, "exhausted"


def canonical(experiment_id, draw, number_hex, evidence_hex, salt_hex):
    return f"{experiment_id}|DRAW={draw}|NUMBER={number_hex}|EVIDENCE={evidence_hex}|SALT={salt_hex}"


def digests(message):
    b = message.encode("ascii")
    return {"sha256": hashlib.sha256(b).hexdigest(), "sha3_512": hashlib.sha3_512(b).hexdigest()}


def evidence_digest(draw_info):
    return hashlib.sha256(canonical_json(draw_info).encode("ascii")).hexdigest()


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ots_stamp(path, enabled=True):
    """Stamp `path` once. Returns True only if a proof file was actually created."""
    if not enabled:
        return False
    path = Path(path)
    if not shutil.which("ots"):
        print(f"OpenTimestamps CLI not found. Stamp {path} at https://opentimestamps.org now.")
        return False
    proof = path.with_name(path.name + ".ots")
    if proof.exists():
        print(f"OpenTimestamps: {proof.name} already exists; not overwriting it.")
        return False
    try:
        r = subprocess.run(["ots", "stamp", str(path)], capture_output=True, text=True, timeout=OTS_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as e:  # cannot launch, or timed out: never fatal, never voids a draw
        print(f"OpenTimestamps FAILED for {path.name}: {type(e).__name__}: {str(e)[:150]}\n"
              f"Stamp it manually at https://opentimestamps.org and note this in RECORD.md.")
        return False
    if r.returncode != 0 or not proof.exists():
        print(f"OpenTimestamps FAILED for {path.name}: {(r.stderr or r.stdout).strip()[:200]}\n"
              f"Stamp it manually at https://opentimestamps.org and note this in RECORD.md.")
        return False
    print(f"OpenTimestamps: submitted {path.name} -> {proof.name} "
          f"(a pending proof; run 'ots upgrade {proof.name}' after a few hours)")
    return True


def print_post(title, post):
    bar = "=" * 72
    print(f"{bar}\n{title}\n{bar}\n{post}\n{bar}\n({len(post)} characters; X limit {POST_LIMIT})")
    if len(post) > POST_LIMIT:
        print("WARNING: too long for a free X post; split it into two posts.")


# --- configuration, postponements --------------------------------------------

def postponements(base):
    return read_json(base / "public" / "postponements.json", default=[])


def load_config(path=ROOT / "config.json", base=ROOT):
    """Registered T0/T1 from config.json, shifted by 24 h per declared postponement."""
    cfg = read_json(path)
    try:
        t0, t1 = parse_iso(cfg["t0_utc"]), parse_iso(cfg["t1_utc"])
    except (KeyError, ValueError):
        die(f"Fill in t0_utc / t1_utc in {path} (format 2026-10-12T12:00:00Z).")
    if t0.second or t0.microsecond or t1.second or t1.microsecond or t1 - t0 < MIN_WAIT:
        die("T0 and T1 must be whole minutes and T1 must be at least 1 hour after T0 (PREREGISTRATION.md §4).")
    n = len(postponements(base))
    return {"experiment_id": cfg["experiment_id"], "t0": t0 + n * POSTPONE_STEP, "t1": t1 + n * POSTPONE_STEP,
            "t0_registered": t0, "t1_registered": t1, "postponements": n}


def paths(base, draw):
    d = draw.lower()
    return {"secret": base / "secret" / f"{d}.json", "commitment": base / "public" / f"{d}_commitment.json",
            "post": base / "public" / f"{d}_commitment.txt", "void": base / "public" / f"{d}_void.json"}


def record_void(base, draw, reason, extra=None):
    write_json(paths(base, draw)["void"], {"draw": draw, "void_at_utc": iso(utcnow()), "reason": reason, **(extra or {})})
    append_event(base, "void", draw=draw, reason=reason)
    print(f"\n*** {draw} DRAW VOID: {reason}\n    Recorded in {paths(base, draw)['void'].name}; this MUST be disclosed (PREREGISTRATION.md §7).")


def commit_number(cfg, base, draw, number_hex, draw_info, extra_public=None, stamp=True, post_lines=()):
    """Commit to the number AND to the evidence bundle (raw response, attempt log, job data) behind it."""
    p = paths(base, draw)
    if p["secret"].exists():
        die(f"{draw} draw already exists ({p['secret']}). Only ONE confirmatory draw per source is allowed.")
    if not HEX6.fullmatch(number_hex):
        die(f"{draw}: internal error, number is not 6 uppercase hex characters.")
    now = utcnow()
    salt_hex = secrets.token_hex(32)
    evidence_hex = evidence_digest(draw_info)
    message = canonical(cfg["experiment_id"], draw, number_hex, evidence_hex, salt_hex)
    d = digests(message)
    write_json(p["secret"], {"experiment_id": cfg["experiment_id"], "draw": draw, "committed_at_utc": iso(now),
                             "number_hex": number_hex, "evidence_sha256": evidence_hex, "salt_hex": salt_hex,
                             "canonical_message": message, "draw_info": draw_info}, private=True)
    write_json(p["commitment"], {"experiment_id": cfg["experiment_id"], "draw": draw, "committed_at_utc": iso(now),
                                 "t1_utc": iso(cfg["t1"]), **d, **(extra_public or {}),
                                 "canonical_format": f"{cfg['experiment_id']}|DRAW={draw}|NUMBER=<6 uppercase hex>"
                                                     "|EVIDENCE=<64 lowercase hex>|SALT=<64 lowercase hex>"})
    append_event(base, "commit", draw=draw, sha256=d["sha256"], sha3_512=d["sha3_512"])
    post = "\n".join([f"{cfg['experiment_id']} {draw}", *post_lines, f"SHA256:{d['sha256']}", f"SHA3-512:{d['sha3_512']}"])
    p["post"].write_text(post + "\n")
    print_post(f"{draw} COMMITTED (number hidden). Post this on X now, as text:", post)
    ots_stamp(p["post"], stamp)
    print(f"BACK UP NOW: copy {p['secret']} to a USB stick or encrypted cloud. If lost, this draw is void.")


# --- ANU ---------------------------------------------------------------------

def anu_key():
    key = os.environ.get("ANU_API_KEY") or (ANU_KEY_FILE.read_text().strip() if ANU_KEY_FILE.exists() else "")
    if not key:
        raise RuntimeError(f"no ANU key: export ANU_API_KEY=... or put it in {ANU_KEY_FILE}")
    return key


def anu_valid(resp):
    data = resp.get("data") if isinstance(resp, dict) else None
    return bool(resp and resp.get("success")) and isinstance(data, list) and len(data) == 3 \
        and all(isinstance(b, int) and 0 <= b <= 255 for b in data)


def anu_once(key):
    """One request. Returns (state, response, detail). The response body is never printed or logged:
    'retry' = definitely no number was returned; 'ambiguous' = a 200 answer that may carry numbers but is malformed."""
    status, body, _ = http_get(ANU_URL, {"x-api-key": key})
    if status is None:
        return "retry", None, "no HTTP response"
    try:
        resp = json.loads(body)
    except json.JSONDecodeError:
        resp = None
    if status != 200:
        msg = resp.get("message") if isinstance(resp, dict) and isinstance(resp.get("message"), str) else ""
        return "retry", None, f"HTTP {status} {msg[:60]}".strip()
    if anu_valid(resp):
        return "ok", resp, "HTTP 200"
    if isinstance(resp, dict) and "data" not in resp:
        return "retry", None, "HTTP 200 without data"
    return "ambiguous", None, "HTTP 200 with malformed content (not shown)"


def draw_anu(deadline=None, base=None):
    key = anu_key()
    log = (lambda a: append_event(base, "anu_attempt", **a)) if base else None
    resp, attempts, final = attempt_loop(lambda n: anu_once(key), "ANU", deadline, on_attempt=log)
    if resp is None:
        err = RuntimeError(f"no usable ANU number ({final}) after {len(attempts)} attempt(s)")
        err.attempts = attempts
        raise err
    number_hex = "".join(f"{b:02X}" for b in resp["data"])
    return number_hex, {"source": "ANU Quantum Random Numbers", "url": ANU_URL, "response": resp, "attempts": attempts}


def draw_os(deadline=None, base=None):
    return secrets.token_hex(3).upper(), {"source": "os CSPRNG (REHEARSAL ONLY - not quantum)",
                                          "attempts": [{"n": 1, "at_utc": iso(utcnow()), "state": "ok", "detail": "local"}]}


# --- IBM ---------------------------------------------------------------------

def ibm_service():
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError:
        raise RuntimeError("IBM toolkit missing: pip3 install -r requirements.txt")
    try:
        return QiskitRuntimeService()
    except Exception as e:
        raise RuntimeError(f"IBM account not set up ({e}); see CHECKLIST.zh.md step A")


def ibm_backend(mode):
    """Returns (service, backend). Raises RuntimeError with a readable reason."""
    if mode == "fake":
        try:
            from qiskit_ibm_runtime.fake_provider import FakeFez
        except ImportError:
            raise RuntimeError("IBM toolkit missing: pip3 install -r requirements.txt")
        return None, FakeFez()
    service = ibm_service()
    return service, service.least_busy(min_num_qubits=NUMBER_BITS, operational=True, simulator=False)


def ibm_circuit():
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    q, c = QuantumRegister(NUMBER_BITS, "q"), ClassicalRegister(NUMBER_BITS, "c")
    qc = QuantumCircuit(q, c, name="handshake")
    qc.h(q)
    qc.measure(q, c)
    return qc


def ibm_submit(backend, tags=None):
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import SamplerV2
    isa = generate_preset_pass_manager(optimization_level=1, backend=backend).run(ibm_circuit())
    sampler = SamplerV2(mode=backend, options={"environment": {"job_tags": tags}} if tags else None)
    return sampler.run([isa], shots=1)


def ibm_status(job):
    st = job.status()
    return str(getattr(st, "name", st)).upper()


def ibm_result_hex(job):
    bitstring = job.result()[0].data.c.get_bitstrings()[0]  # leftmost character = classical bit 23
    return f"{int(bitstring, 2):0{NUMBER_HEX_LEN}X}", bitstring


def ibm_timestamps(job):
    try:
        return {k: str(v) for k, v in (job.metrics().get("timestamps") or {}).items()}
    except Exception:
        return {}  # local fake jobs have no server metrics


def ibm_wait(job, until=None):
    """Poll until DONE/ERROR/CANCELLED or until `until`. Returns the last status string."""
    last = None
    while True:
        try:
            st = ibm_status(job)
        except Exception as e:  # transient network trouble: keep polling until the deadline
            st = f"UNKNOWN ({str(e)[:60]})"
        if st != last:
            print(f"[{iso(utcnow())}] IBM job {job.job_id()}: {st}")
            last = st
        if st in ("DONE", "ERROR", "CANCELLED"):
            return st
        if until and utcnow() >= until:
            return st
        time.sleep(IBM_POLL_SECONDS if until else 2)


def ibm_state_path(base):
    return base / "public" / "ibm_job.json"


def ibm_find_tagged(tag, since):
    """Jobs on the account carrying `tag`, created after `since`. Returns a list, or None if the query failed."""
    try:
        return list(ibm_service().jobs(job_tags=[tag], created_after=since - timedelta(minutes=2), limit=5))
    except Exception:
        return None


def ibm_submit_attempts(state, base, deadline, experiment_id):
    """Submit (with retries) within the shared 10-attempt budget. Every attempt is persisted before and after the
    submission call. If a submission call fails after it may have reached IBM, the account is searched for the
    attempt's unique tag: a found job is adopted, a confirmed absence allows a retry, an unknown state stops."""
    budget = MAX_ATTEMPTS - len(state["attempts"])
    if budget <= 0:
        return None
    holder = {}

    def once(n):
        tag = f"{experiment_id}-attempt-{n}"
        entry = {"n": n, "tag": tag, "state": "submitting", "begun_utc": iso(utcnow())}
        state["attempts"].append(entry)
        write_json(ibm_state_path(base), state)
        append_event(base, "ibm_submit_begin", n=n, tag=tag)
        stage, began = "select", utcnow()
        try:
            _, backend = ibm_backend(state["mode"])
            stage = "submit"
            job = ibm_submit(backend, tags=[experiment_id, tag] if state["mode"] == "real" else None)
            holder.update(job=job, backend=backend.name)
            return "ok", job, f"submitted {job.job_id()} on {backend.name}"
        except Exception as e:
            if stage == "select" or state["mode"] != "real":
                return "retry", None, f"no submission ({stage}): {str(e)[:120]}"
            found = ibm_find_tagged(tag, began)
            if found:
                job = found[0]
                holder.update(job=job, backend=getattr(job.backend(), "name", "?") if hasattr(job, "backend") else "?")
                return "ok", job, f"submission raised ({str(e)[:60]}) but job {job.job_id()} exists; adopted"
            if found == []:
                return "retry", None, f"submission failed and no job with tag {tag} exists: {str(e)[:80]}"
            return "ambiguous", None, f"submission raised and the account could not be searched: {str(e)[:80]}"

    def persist(a):
        entry = state["attempts"][-1]
        entry.update(state=a["state"], detail=a["detail"], ended_utc=iso(utcnow()))
        if a["state"] == "ok":
            entry.update(job_id=holder["job"].job_id(), backend=holder["backend"])
            state.update(job_id=holder["job"].job_id(), backend=holder["backend"], submitted_at_utc=entry["begun_utc"])
        write_json(ibm_state_path(base), state)
        append_event(base, "ibm_submit_end", n=a["n"], state=a["state"], detail=a["detail"],
                     job_id=entry.get("job_id"))

    job, attempts, final = attempt_loop(once, "IBM", deadline, max_attempts=budget,
                                        first_n=len(state["attempts"]) + 1, on_attempt=persist)
    state["last_outcome"] = final
    write_json(ibm_state_path(base), state)
    return job


def ibm_recover_pending(state, base):
    """After a crash between 'submitting' and its outcome, look the attempt up by tag."""
    last = state["attempts"][-1] if state["attempts"] else None
    if not last or last.get("state") != "submitting" or state["mode"] != "real":
        return None
    found = ibm_find_tagged(last["tag"], parse_iso(last["begun_utc"]))
    if found is None:
        die("An IBM submission was interrupted and the account cannot be searched now; retry commit-ibm shortly.")
    if not found:
        last.update(state="retry", detail="interrupted; no job with this tag exists")
        write_json(ibm_state_path(base), state)
        return None
    job = found[0]
    last.update(state="ok", detail="interrupted; job found by tag and adopted", job_id=job.job_id())
    state.update(job_id=job.job_id(), submitted_at_utc=last["begun_utc"])
    write_json(ibm_state_path(base), state)
    append_event(base, "ibm_recovered", job_id=job.job_id(), tag=last["tag"])
    return job


# --- target: NIST only -------------------------------------------------------

def nist_pulse_json(url):
    """(status, pulse or None, detail)."""
    status, body, _ = http_get(url)
    if status != 200:
        return status, None, f"HTTP {status}: {body[:100]}"
    try:
        return status, json.loads(body)["pulse"], "ok"
    except (json.JSONDecodeError, KeyError) as e:
        return status, None, f"bad NIST response: {e}"


def nist_validate(pulse):
    ts = parse_iso(pulse["timeStamp"])
    if not NIST_OUTPUT.fullmatch(pulse.get("outputValue", "")):
        raise RuntimeError("NIST outputValue is not 128 hexadecimal characters")
    if not isinstance(pulse.get("chainIndex"), int) or not isinstance(pulse.get("pulseIndex"), int):
        raise RuntimeError("NIST pulse lacks integer chainIndex/pulseIndex")
    return ts


def fetch_target(t1):
    """The pre-registered target: the first NIST pulse whose timeStamp is at or after T1 (PREREGISTRATION.md §4).
    Raises RuntimeError when the target cannot be determined yet; it is never replaced by anything else."""
    return fetch_pulse(t1)


def fetch_pulse(t1):
    """First NIST pulse with timeStamp >= t1 (used for N1 and for the secondary targets).
    Checks the schema, that the pulse before it is earlier than t1 (so it really is the first one),
    and that its 'previous' link equals that pulse's outputValue."""
    url = NIST_TIME_URL.format(ms=int(t1.timestamp() * 1000))
    last = None
    for attempt in range(3):
        status, pulse, detail = nist_pulse_json(url)
        if status == 404:
            raise RuntimeError(f"NIST has published no pulse at or after {iso(t1)} yet. "
                               "The target is the first one it publishes; retry later.")
        if pulse is not None:
            break
        last = detail
        time.sleep(3 * (attempt + 1))
    else:
        raise RuntimeError(f"NIST unreachable ({last}). The target is unchanged; retry later.")

    ts = nist_validate(pulse)
    if ts < t1:
        raise RuntimeError(f"NIST returned a pulse before {iso(t1)} ({pulse['timeStamp']}); refusing to use it.")
    prev_url = NIST_INDEX_URL.format(chain=pulse["chainIndex"], index=pulse["pulseIndex"] - 1)
    p_status, prev, p_detail = nist_pulse_json(prev_url)
    if p_status == 404:
        prev_info = {"previous": "none (first pulse of its chain)", "link_ok": None}
    elif prev is None:
        raise RuntimeError(f"Cannot check the preceding NIST pulse ({p_detail}); retry later.")
    else:
        prev_ts = nist_validate(prev)
        if prev_ts >= t1:
            raise RuntimeError(f"The preceding pulse {prev['timeStamp']} is not before {iso(t1)}; NIST answer inconsistent.")
        link = next((lv.get("value") for lv in pulse.get("listValues", []) if lv.get("type") == "previous"), None)
        if link is None or link.upper() != prev["outputValue"].upper():
            raise RuntimeError("NIST chain link to the preceding pulse does not match; refusing to use this pulse.")
        prev_info = {"previous_timestamp": prev["timeStamp"], "previous_uri": prev.get("uri"), "link_ok": True}
    return {"source": "NIST Randomness Beacon 2.0", "request_url": url, "pulse_uri": pulse["uri"],
            "chain_index": pulse["chainIndex"], "pulse_index": pulse["pulseIndex"],
            "pulse_timestamp": pulse["timeStamp"], "t1_pulse_missing": ts != t1, **prev_info,
            "value": pulse["outputValue"].upper(), "target_hex": pulse["outputValue"][:NUMBER_HEX_LEN].upper(),
            "raw": {"pulse": pulse}}


# --- environment, preflight ----------------------------------------------------

def registered_code_hash():
    m = re.search(r"`handshake\.py`, SHA-256 `([0-9a-f]{64})`", (ROOT / "PREREGISTRATION.md").read_text())
    return m.group(1) if m else None


def pinned_versions():
    return dict(re.findall(r"^([A-Za-z0-9_.-]+)==(\S+)", (ROOT / "requirements.txt").read_text(), re.M))


def environment_fingerprint():
    from importlib import metadata
    dists = sorted(f"{d.metadata['Name']}=={d.version}" for d in metadata.distributions() if d.metadata["Name"])
    return {"python": platform.python_version(), "executable": sys.executable,
            "packages_sha256": hashlib.sha256("\n".join(dists).encode()).hexdigest(), "n_packages": len(dists)}


def do_preflight(cfg, base, enforce=True, ibm_mode="real", anu=True):
    checks = []

    def add(name, ok, detail, required=True):
        checks.append({"check": name, "ok": bool(ok), "required": required, "detail": detail})
        mark = "OK  " if ok else ("FAIL" if required else "warn")
        print(f"[{mark}] {name}: {detail}")

    started = utcnow()
    lo, hi = cfg["t0"] + PREFLIGHT_OPENS, cfg["t0"] + PREFLIGHT_CLOSES
    add("start not yet run", not (base / "public" / "start.json").exists(), "public/start.json absent")
    add("no stale secrets", not any((base / "secret").glob("*.json")) if (base / "secret").exists() else True,
        "secret/ holds no draw")

    reg, actual = registered_code_hash(), file_sha256(ROOT / "handshake.py")
    add("code matches pre-registration", reg == actual or not enforce,
        f"registered {reg or 'NOT FILLED IN'}, actual {actual}")
    add("no PYTHONPATH override", not os.environ.get("PYTHONPATH"), f"PYTHONPATH={os.environ.get('PYTHONPATH', '')!r}")

    status, body, headers = http_get(NIST_LAST_URL)
    server = parsedate_to_datetime(headers["Date"]) if headers.get("Date") else None
    offset = (utcnow() - server).total_seconds() if server else None
    add("computer clock", offset is not None and abs(offset) <= CLOCK_TOLERANCE_S,
        f"offset {offset:+.0f}s vs NIST server time" if offset is not None else f"no server time ({status})")
    try:
        last_ts = parse_iso(json.loads(body)["pulse"]["timeStamp"]) if status == 200 else None
    except (json.JSONDecodeError, KeyError, ValueError):
        last_ts = None
    add("NIST beacon publishing", last_ts is not None and utcnow() - last_ts <= NIST_FRESH,
        f"latest pulse {iso(last_ts) if last_ts else 'n/a'} (must be within {int(NIST_FRESH.total_seconds() // 60)} min)")

    if anu:
        try:
            state, _, detail = anu_once(anu_key())  # the number is discarded unseen; it is never committed
            ok = state == "ok"
        except RuntimeError as e:
            ok, detail = False, str(e)
        add("ANU key and service", ok, f"{detail} (1 request used; number discarded unseen)")

    try:
        service, backend = ibm_backend(ibm_mode)
        pending = backend.status().pending_jobs if ibm_mode == "real" else 0
        add("IBM connection and QPU", True, f"least busy: {backend.name}, pending jobs {pending}")
        if ibm_mode == "real":
            left = service.usage().get("usage_remaining_seconds")
            add("IBM quota", left is not None and left >= IBM_MIN_QUOTA_S, f"{left} s remaining")
        from importlib import metadata
        pins = pinned_versions()
        for pkg in ("qiskit", "qiskit-ibm-runtime"):
            installed = metadata.version(pkg)
            add(f"{pkg} version", installed == pins.get(pkg), f"installed {installed}, pinned {pins.get(pkg)}")
    except Exception as e:
        add("IBM connection and QPU", False, str(e)[:150])

    add("OpenTimestamps CLI", shutil.which("ots") is not None, "ots on PATH", required=False)

    finished = utcnow()
    add("preflight window", (lo <= started and finished <= hi) or not enforce,
        f"ran {iso(started)} to {iso(finished)}; window {iso(lo)} to {iso(hi)}")
    passed = all(c["ok"] for c in checks if c["required"])
    log = read_json(base / "public" / "preflight_log.json", default=[])
    log.append({"started_utc": iso(started), "finished_utc": iso(finished), "t0_utc": iso(cfg["t0"]),
                "pass": passed, "environment": environment_fingerprint(), "checks": checks})
    write_json(base / "public" / "preflight_log.json", log)
    append_event(base, "preflight", passed=passed, started_utc=iso(started), finished_utc=iso(finished))
    print(f"\nPREFLIGHT {'PASSED' if passed else 'FAILED'} (logged; every preflight run is disclosed).")
    if not passed:
        print("Fix the failing item and run preflight again before the window closes, "
              "or postpone: python3 handshake.py postpone --reason \"...\"")
    return passed


def require_preflight(cfg, base):
    lo, hi = cfg["t0"] + PREFLIGHT_OPENS, cfg["t0"] + PREFLIGHT_CLOSES
    log = read_json(base / "public" / "preflight_log.json", default=[])

    def good(r):
        if not (r.get("started_utc") and r.get("finished_utc") and r.get("checks")):
            return False
        return (all(c["ok"] for c in r["checks"] if c["required"]) and r.get("pass") is True
                and lo <= parse_iso(r["started_utc"]) and parse_iso(r["finished_utc"]) <= hi)
    if not any(good(r) for r in log):
        die(f"No preflight that passed and ran entirely between {iso(lo)} and {iso(hi)}. "
            "Per PREREGISTRATION.md §5 do not start; postpone instead.")


def do_postpone(cfg, base, reason):
    if (base / "public" / "start.json").exists():
        die("start has already run; postponement is no longer possible.")
    post = postponements(base)
    if len(post) >= MAX_POSTPONEMENTS:
        die(f"The maximum of {MAX_POSTPONEMENTS} postponements is used up. Per PREREGISTRATION.md §5 the attempt is void.")
    now = utcnow()
    if now > cfg["t0"] + START_CLOSES:
        die("The start window has already closed without a postponement; the attempt is void.")
    entry = {"n": len(post) + 1, "declared_at_utc": iso(now), "reason": reason,
             "from_t0_utc": iso(cfg["t0"]), "to_t0_utc": iso(cfg["t0"] + POSTPONE_STEP),
             "to_t1_utc": iso(cfg["t1"] + POSTPONE_STEP)}
    write_json(base / "public" / "postponements.json", post + [entry])
    append_event(base, "postpone", **entry)
    post_text = (f"{cfg['experiment_id']} postponed ({entry['n']}/{MAX_POSTPONEMENTS})\n"
                 f"T0 -> {entry['to_t0_utc']}\nT1 -> {entry['to_t1_utc']}\nReason: {reason}")
    print_post(f"Post this on X before the start window closes ({iso(cfg['t0'] + START_CLOSES)}):", post_text)


# --- steps -------------------------------------------------------------------

def do_start(cfg, base, anu_draw=draw_anu, ibm_mode="real", enforce=True, stamp=True):
    now = utcnow()
    window_close = cfg["t0"] + START_CLOSES
    if enforce:
        if not (cfg["t0"] + START_OPENS <= now <= window_close):
            die(f"Outside the start window ({iso(cfg['t0'] + START_OPENS)} to {iso(window_close)}). "
                "Do not draw (PREREGISTRATION.md §5, §7).")
        require_preflight(cfg, base)
    marker = base / "public" / "start.json"
    if marker.exists():
        die(f"start was already run at {read_json(marker)['started_at_utc']}. "
            "Only one confirmatory attempt is allowed, even if its draws were void.")
    write_json(marker, {"experiment_id": cfg["experiment_id"], "started_at_utc": iso(now), "tool_version": VERSION,
                        "t0_utc": iso(cfg["t0"]), "t1_utc": iso(cfg["t1"]), "postponements": cfg.get("postponements", 0),
                        "code_sha256": file_sha256(ROOT / "handshake.py"), "environment": environment_fingerprint()})
    append_event(base, "start", t0_utc=iso(cfg["t0"]), t1_utc=iso(cfg["t1"]))
    deadline = window_close if enforce else None

    # 1) ANU: draw (up to 10 attempts inside the start window) and commit immediately
    try:
        number_hex, info = anu_draw(deadline=deadline, base=base)
    except Exception as e:
        record_void(base, "ANU", f"ANU draw failed: {e}", {"attempts": getattr(e, "attempts", [])})
    else:
        try:
            commit_number(cfg, base, "ANU", number_hex, info, stamp=stamp,
                          extra_public={"anu_attempts": info["attempts"]})
        except Exception as e:
            p = paths(base, "ANU")
            if p["commitment"].exists():  # already committed: a later, supplementary step failed; the draw stands
                print(f"WARNING: a step after the ANU commitment failed ({e}). The ANU draw stays committed; "
                      f"post the hashes from {p['commitment']} and back up {p['secret']}.")
            else:
                record_void(base, "ANU", f"ANU commitment failed: {e}", {"attempts": info["attempts"]})

    # 2) IBM: submit (up to 10 attempts inside the start window); commit-ibm commits once the job has run
    if ibm_mode == "none":
        return None
    state = {"mode": ibm_mode, "attempts": [], "must_be_created_by_utc": iso(cfg["t1"] - IBM_DONE_BY - IBM_RESUBMIT_MARGIN),
             "must_finish_by_utc": iso(cfg["t1"] - IBM_DONE_BY)}
    job = ibm_submit_attempts(state, base, deadline, cfg["experiment_id"])
    if job is None:
        record_void(base, "IBM", f"IBM submission failed ({state.get('last_outcome')}) after "
                                 f"{len(state['attempts'])} attempt(s)", {"attempts": state["attempts"]})
        return None
    print(f"\nIBM job submitted: {job.job_id()} on {state['backend']}. Now run: python3 handshake.py commit-ibm")
    return job


def do_commit_ibm(cfg, base, job=None, enforce=True, stamp=True):
    if not ibm_state_path(base).exists():
        die("No IBM job on record; run start first.")
    if paths(base, "IBM")["void"].exists():
        die("The IBM draw is already void.")
    if paths(base, "IBM")["secret"].exists():
        die("The IBM draw is already committed.")
    state = read_json(ibm_state_path(base))
    done_by = cfg["t1"] - IBM_DONE_BY
    resubmit_by = done_by - IBM_RESUBMIT_MARGIN
    if job is None:
        job = ibm_recover_pending(state, base)
    if job is None and state.get("job_id"):
        try:
            job = ibm_service().job(state["job_id"])
        except Exception as e:
            die(f"Cannot reach the IBM job ({e}). Fix the connection and rerun commit-ibm before the deadline.")
    if job is None:
        job = ibm_submit_attempts(state, base, resubmit_by if enforce else None, cfg["experiment_id"])
        if job is None:
            return record_void(base, "IBM", "no IBM job could be submitted", {"attempts": state["attempts"]})

    while True:
        status = ibm_wait(job, until=done_by if enforce else None)
        entry = next((a for a in reversed(state["attempts"]) if a.get("job_id") == job.job_id()), state["attempts"][-1])
        entry["final_status"] = status
        if status == "ERROR":
            try:
                entry["error_message"] = str(job.error_message())[:200]
            except Exception:
                pass
        write_json(ibm_state_path(base), state)
        append_event(base, "ibm_job_final", job_id=job.job_id(), status=status)
        if status == "DONE":
            break
        if status in ("ERROR", "CANCELLED"):
            # The job produced no visible number, so a resubmission cannot select an outcome (PREREGISTRATION.md §4).
            if enforce and utcnow() >= resubmit_by:
                return record_void(base, "IBM", f"job {job.job_id()} ended {status} too late to resubmit",
                                   {"attempts": state["attempts"]})
            job = ibm_submit_attempts(state, base, resubmit_by if enforce else None, cfg["experiment_id"])
            if job is None:
                return record_void(base, "IBM", f"job ended {status}; no resubmission possible "
                                                f"({len(state['attempts'])} of {MAX_ATTEMPTS} attempts used)",
                                   {"attempts": state["attempts"]})
            print(f"Resubmitted as {job.job_id()}; waiting again.")
            continue
        try:
            job.cancel()
        except Exception:
            pass
        return record_void(base, "IBM", f"job {job.job_id()} not finished by {iso(done_by)} (status {status})",
                           {"attempts": state["attempts"]})

    stamps = ibm_timestamps(job)
    if state["mode"] == "real" and enforce:
        # Deadlines are judged by IBM's server timestamps; without them the draw is void (fail closed).
        try:
            created, finished = parse_iso(stamps["created"]), parse_iso(stamps["finished"])
        except (KeyError, ValueError):
            return record_void(base, "IBM", f"job {job.job_id()} has no usable server timestamps ({stamps})",
                               {"attempts": state["attempts"]})
        if created > resubmit_by or finished > done_by or finished < created:
            return record_void(base, "IBM", f"server times created {stamps['created']}, finished {stamps['finished']} "
                                            f"violate the deadlines ({iso(resubmit_by)}, {iso(done_by)})",
                               {"attempts": state["attempts"]})
    if enforce and utcnow() > cfg["t1"] - COMMIT_DEADLINE:
        return record_void(base, "IBM", "too close to T1 to commit", {"attempts": state["attempts"]})
    number_hex, bitstring = ibm_result_hex(job)
    try:
        from importlib import metadata
        software = {p: metadata.version(p) for p in ("qiskit", "qiskit-ibm-runtime")}
    except Exception:
        software = {}
    draw_info = {"source": "IBM Quantum", "mode": state["mode"], "job_id": job.job_id(), "backend": state.get("backend"),
                 "attempts": state["attempts"], "bitstring": bitstring, "timestamps": stamps,
                 "circuit": f"{NUMBER_BITS} qubits, H on each, measure q[i]->c[i]; optimization_level=1; SamplerV2 shots=1",
                 "software": software}
    commit_number(cfg, base, "IBM", number_hex, draw_info,
                  extra_public={"job_id": job.job_id(), "backend": state.get("backend"), "ibm_timestamps": stamps,
                                "ibm_attempts": state["attempts"]},
                  post_lines=[f"JOB:{job.job_id()}"], stamp=stamp)


def do_fetch_target(cfg, base, enforce=True, stamp=True):
    out = base / "public" / "target.json"
    if out.exists():
        die(f"Target already fetched: {out}")
    now = utcnow()
    if enforce and now < cfg["t1"] + TARGET_EARLIEST:
        die(f"Too early. Run this at or after {iso(cfg['t1'] + TARGET_EARLIEST)}.")
    try:
        res = fetch_target(cfg["t1"])
    except RuntimeError as e:
        die(f"{e} (nothing was written)")
    res.update({"t1_utc": iso(cfg["t1"]), "fetched_at_utc": iso(now)})
    write_json(out, res)
    append_event(base, "target", pulse=res["pulse_timestamp"], target_hex=res["target_hex"])
    note = " (the T1 pulse itself is missing; per §4 the first later pulse is the target)" if res["t1_pulse_missing"] else ""
    print(f"TARGET: NIST pulse {res['pulse_timestamp']} -> {res['target_hex']}{note}\n[full outputValue: {res['value']}]")
    print_post("Post this on X:", "\n".join([
        f"{cfg['experiment_id']} target",
        f"NIST pulse {res['pulse_timestamp']} (chain {res.get('chain_index')}, pulse {res.get('pulse_index')})",
        f"TARGET={res['target_hex']}"] + (["T1 pulse missing: first later pulse used (prereg §4)"] if res["t1_pulse_missing"] else [])))
    print(f"Archive it too: https://web.archive.org/save/{res['request_url']}")
    ots_stamp(out, stamp)


def score(numbers, target_hex):
    """numbers: {draw: hex} for valid draws. Returns (result, hits, chance-of-any-hit)."""
    hits = [d for d, n in numbers.items() if n == target_hex]
    k = len(numbers)
    chance = 1 - (1 - CHANCE_ONE) ** k if k else None
    if not numbers:
        return "VOID", hits, chance
    if len(hits) == 2:
        return "DOUBLE HIT", hits, chance
    return (f"HIT ({hits[0]})" if hits else "INCONCLUSIVE"), hits, chance


def secondary_chain(p1_time, fetch=fetch_pulse, until=None):
    """Walk the secondary schedule from the actual N1 pulse time. Returns a list of dicts for the pulses that are
    due (scheduled time + TARGET_EARLIEST <= until) and available; stops at the first one that is not."""
    out, prev_time, prev_offset = [], p1_time, timedelta(0)
    for name, offset in SECONDARY:
        scheduled = prev_time + (offset - prev_offset)
        if until and until < scheduled + TARGET_EARLIEST:
            break
        try:
            pulse = fetch(scheduled)
        except RuntimeError as e:
            print(f"{name}: not available yet ({str(e)[:90]})")
            break
        actual = parse_iso(pulse["pulse_timestamp"])
        out.append({"name": name, "nominal_offset_from_t1": str(offset), "scheduled_utc": iso(scheduled),
                    "shift_seconds": int((actual - scheduled).total_seconds()), **pulse})
        prev_time, prev_offset = actual, offset
    return out


def secondary_compare(numbers, n1_hex, chain):
    """Compare every secondary pulse with N1, the earlier secondary pulses and the scored draws."""
    comparisons, earlier = [], {"N1": n1_hex}
    for p in chain:
        refs = {**earlier, **numbers}
        for ref, value in refs.items():
            comparisons.append({"pulse": p["name"], "against": ref, "match": p["target_hex"] == value})
        earlier[p["name"]] = p["target_hex"]
    return comparisons


def secondary_comparison_count(n_draws):
    return sum(k + n_draws for k in range(1, len(SECONDARY) + 1))  # N2: N1+draws, N3: N1,N2+draws, ...


def do_fetch_secondary(cfg, base, enforce=True, stamp=True):
    """Fetch the secondary NIST targets that are due (one immutable file each); when all are in and the reveal
    exists, write the report (approximate family-wise chance)."""
    public = base / "public"
    if not (public / "target.json").exists():
        die("Fetch the primary target first (fetch-target).")
    n1 = read_json(public / "target.json")
    chain = secondary_chain(parse_iso(n1["pulse_timestamp"]), until=utcnow() if enforce else None)
    for p in chain:
        f = public / f"secondary_{p['name']}.json"
        if f.exists():
            if read_json(f)["target_hex"] != p["target_hex"]:
                die(f"{p['name']} changed on re-fetch ({read_json(f)['target_hex']} -> {p['target_hex']}); investigate.")
            continue
        write_json(f, {**p, "fetched_at_utc": iso(utcnow())})
        append_event(base, "secondary", name=p["name"], pulse=p["pulse_timestamp"], value=p["target_hex"])
        print_post(f"{p['name']} fetched. Post this on X:", "\n".join([
            f"{cfg['experiment_id']} secondary {p['name']}",
            f"NIST pulse {p['pulse_timestamp']} (chain {p.get('chain_index')}, pulse {p.get('pulse_index')})",
            f"{p['name']}={p['target_hex']}"] + ([f"shifted {p['shift_seconds']}s (pulse missing at schedule)"]
                                                  if p["shift_seconds"] else [])))
        print(f"Archive it too: https://web.archive.org/save/{p['request_url']}")
        ots_stamp(f, stamp)
    if len(chain) < len(SECONDARY):
        print(f"{len(chain)} of {len(SECONDARY)} secondary targets in; "
              f"run fetch-secondary again after {SECONDARY[len(chain)][0]} is due.")
        return
    report = public / "secondary.json"
    if report.exists():
        print(f"Secondary report already written: {report}")
        return
    if not (public / "reveal.json").exists():
        die("All secondary targets are in; run reveal first, then fetch-secondary again for the report.")
    reveal = read_json(public / "reveal.json")
    numbers = {d: v["number_hex"] for d, v in reveal["draws"].items()}
    comps = secondary_compare(numbers, n1["target_hex"], chain)
    matches = [f"{c['pulse']}={c['against']}" for c in comps if c["match"]]
    chance = 1 - (1 - CHANCE_ONE) ** len(comps)
    write_json(report, {"experiment_id": cfg["experiment_id"], "pulses": [p["name"] for p in chain],
                        "comparisons": comps, "matches": matches, "n_comparisons": len(comps),
                        "approx_chance_of_any_match": chance})
    append_event(base, "secondary_report", matches=matches, n_comparisons=len(comps))
    print_post("Secondary report. Post this on X:", "\n".join([
        f"{cfg['experiment_id']} secondary report",
        " ".join(f"{p['name']}={p['target_hex']}" for p in chain),
        f"Matches: {', '.join(matches) if matches else 'none'}",
        f"{len(comps)} comparisons; chance of any match ~1 in {round(1 / chance):,}",
        "Separate from the primary result (prereg §6.2)"]))
    ots_stamp(report, stamp)


def do_void(cfg, base, draw, reason):
    """Record a void the script cannot detect itself, e.g. a commitment posted on X after T1 - 10 min."""
    if paths(base, draw)["void"].exists():
        die(f"{draw} is already void: {read_json(paths(base, draw)['void'])['reason']}")
    record_void(base, draw, f"declared by the author: {reason}")


def do_reveal(cfg, base):
    public = base / "public"
    if not (public / "target.json").exists():
        die("Run fetch-target first (the target must be on record before anything is revealed).")
    target = read_json(public / "target.json")
    scored, unscored, lines = {}, {}, []
    for draw in DRAWS:
        p = paths(base, draw)
        if not p["commitment"].exists():
            continue
        if not p["secret"].exists():
            if not p["void"].exists():
                record_void(base, draw, "secret file lost before the reveal")
            continue
        secret, commitment = read_json(p["secret"]), read_json(p["commitment"])
        if evidence_digest(secret["draw_info"]) != secret["evidence_sha256"]:
            die(f"{draw}: evidence bundle does not match its digest. Do NOT publish; investigate.")
        d = digests(canonical(cfg["experiment_id"], draw, secret["number_hex"], secret["evidence_sha256"],
                              secret["salt_hex"]))
        if d["sha256"] != commitment["sha256"] or d["sha3_512"] != commitment["sha3_512"]:
            die(f"{draw}: secret does not match the published commitment. Do NOT publish; investigate.")
        write_json(public / "opened" / f"{draw.lower()}.json", secret)  # full secret, published after the reveal
        entry = {"number_hex": secret["number_hex"], "evidence_sha256": secret["evidence_sha256"],
                 "salt_hex": secret["salt_hex"], "canonical_message": secret["canonical_message"], **d}
        if p["void"].exists():
            unscored[draw] = entry  # opened for transparency, never scored (PREREGISTRATION.md §7)
        else:
            scored[draw] = entry
            lines.append(f"{draw}={secret['number_hex']} SALT={secret['salt_hex']}")
    result, hits, chance = score({d: v["number_hex"] for d, v in scored.items()}, target["target_hex"])
    voids = [d for d in DRAWS if paths(base, d)["void"].exists()]
    write_json(public / "reveal.json", {"experiment_id": cfg["experiment_id"], "draws": scored,
                                        "unscored_void_draws": unscored, "void_draws": voids,
                                        "target_hex": target["target_hex"], "target_pulse": target["pulse_timestamp"],
                                        "result": result, "hits": hits, "chance_of_any_hit": chance})
    append_event(base, "reveal", result=result, hits=hits)
    post = "\n".join([f"{cfg['experiment_id']} reveal", *lines, f"TARGET={target['target_hex']}", f"RESULT={result}"]
                     + ([f"VOID:{','.join(voids)}"] if voids else []))
    print_post("Post this on X:", post)
    print("Full evidence (raw ANU response, IBM job data) is in public/opened/; EVIDENCE hashes are in the commitments.")
    explain(result, len(scored), chance)


def explain(result, k, chance):
    if result == "VOID":
        print("No valid draw. The attempt is void and must be reported as such.")
    elif result == "DOUBLE HIT":
        print(f"DOUBLE HIT: both independent draws match. Chance probability {2 ** -48:.1e} "
              "(assuming a uniform target and a uniform ANU draw).")
    elif result.startswith("HIT"):
        print(f"{result}. Chance of at least one match among {k} draw(s): {chance:.2e} (about 1 in {round(1 / chance):,}).")
    else:
        print("INCONCLUSIVE, as pre-registered. A miss neither supports nor refutes the hypothesis.")
    if "HIT" in result:
        print("Before any claim: look for mundane causes (code bug, timing, compromised source), publish everything.")


def check_opened(base, draw, entry, cfg, posted):
    """Recompute EVIDENCE from the opened bundle and the two hashes from the canonical message."""
    ok = True
    opened = base / "public" / "opened" / f"{draw.lower()}.json"
    if opened.exists():
        bundle = read_json(opened)
        good = evidence_digest(bundle["draw_info"]) == entry["evidence_sha256"]
        ok &= good
        print(f"[{'OK' if good else 'FAIL'}] {draw} evidence bundle matches its committed EVIDENCE digest")
    else:
        ok = False
        print(f"[FAIL] {draw} evidence bundle (public/opened/{draw.lower()}.json) is missing")
    d = digests(canonical(cfg["experiment_id"], draw, entry["number_hex"], entry["evidence_sha256"], entry["salt_hex"]))
    want = (posted or {}).get(draw) or read_json(paths(base, draw)["commitment"])
    for k in ("sha256", "sha3_512"):
        good = d[k] == want[k].lower()
        ok &= good
        print(f"[{'OK' if good else 'FAIL'}] {draw} {k} matches the commitment")
    fmt = bool(HEX6.fullmatch(entry["number_hex"]))
    ok &= fmt
    print(f"[{'OK' if fmt else 'FAIL'}] {draw} number is 6 uppercase hexadecimal characters")
    return ok


def do_verify(cfg, base, posted=None, offline=False):
    """posted: optional {draw: {"sha256":..., "sha3_512":...}} as copied from the X posts."""
    public = base / "public"
    reveal = read_json(public / "reveal.json")
    ok, numbers = True, {}
    for draw, v in reveal.get("unscored_void_draws", {}).items():
        print(f"--- {draw} (void, opened for transparency, not scored)")
        ok &= check_opened(base, draw, v, cfg, posted)
    for draw, v in reveal["draws"].items():
        print(f"--- {draw}")
        ok &= check_opened(base, draw, v, cfg, posted)
        if draw == "IBM":
            c = read_json(paths(base, draw)["commitment"])
            print(f"[--] IBM job {c.get('job_id')} on {c.get('backend')}, server timestamps {c.get('ibm_timestamps') or 'n/a'}"
                  " (IBM records are private to the account; provenance is author-attested)")
        numbers[draw] = v["number_hex"]
    for draw in reveal.get("void_draws", []):
        print(f"[--] {draw} draw void (disclosed): {read_json(paths(base, draw)['void'])['reason']}")

    print("--- target")
    if offline:
        target = read_json(public / "target.json")
        print(f"[--] target taken from target.json (offline): {target['target_hex']}")
    else:
        try:
            target = fetch_target(cfg["t1"])
        except RuntimeError as e:
            die(f"Could not fetch the target independently: {e} (retry, or use --offline)")
        print(f"[OK] target fetched independently: NIST pulse {target['pulse_timestamp']} -> {target['target_hex']}"
              f" (first pulse at or after T1; chain link {'checked' if target.get('link_ok') else 'n/a'})")

    result, _, chance = score(numbers, target["target_hex"])
    same = result == reveal.get("result")
    ok &= same
    print(f"[{'OK' if same else 'FAIL'}] recomputed result {result} matches the published result")

    if (public / "secondary.json").exists():
        published = read_json(public / "secondary.json")
        chain = ([read_json(public / f"secondary_{n}.json") for n, _ in SECONDARY] if offline
                 else secondary_chain(parse_iso(target["pulse_timestamp"])))
        comps = secondary_compare(numbers, target["target_hex"], chain)
        matches = [f"{c['pulse']}={c['against']}" for c in comps if c["match"]]
        sec_chance = 1 - (1 - CHANCE_ONE) ** len(comps)
        for p in chain:  # each saved secondary file must equal the pulse NIST serves
            f = public / f"secondary_{p['name']}.json"
            saved = read_json(f) if f.exists() else {}
            same_p = (saved.get("target_hex"), saved.get("pulse_timestamp")) == (p["target_hex"], p["pulse_timestamp"])
            ok &= same_p
            print(f"[{'OK' if same_p else 'FAIL'}] {p['name']}: NIST pulse {p['pulse_timestamp']} -> {p['target_hex']} "
                  f"{'matches' if same_p else 'does NOT match'} {f.name}")
        good = len(chain) == len(SECONDARY) and matches == published["matches"] \
            and len(comps) == published["n_comparisons"] and comps == published["comparisons"] \
            and abs(sec_chance - published["approx_chance_of_any_match"]) <= 1e-12 * sec_chance
        ok &= good
        print(f"[{'OK' if good else 'FAIL'}] secondary targets "
              f"{' '.join(p['name'] + '=' + p['target_hex'] for p in chain)} -> matches {matches or 'none'} "
              f"(published: {published['matches'] or 'none'})")
    print("\nAlso check by hand (the script cannot see these):\n"
          f"  - each commitment post on X was published before {iso(cfg['t1'] - COMMIT_DEADLINE)}\n"
          "  - the OpenTimestamps proofs (*.ots) verify (e.g. at opentimestamps.org)\n"
          "  - PREREGISTRATION.md hashes to the SHA-256 posted on X before the first T0")
    if not ok:
        print("\nVERDICT: PROBLEM FOUND - the published data are inconsistent; the result cannot be trusted.")
        return False
    print(f"\nVERDICT: consistent - result {result}")
    explain(result, len(numbers), chance)
    return True


def do_setup_ibm():
    """Save the IBM account on this computer (~/.qiskit). The key is typed hidden and never printed."""
    import getpass
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError:
        die("IBM toolkit missing: pip3 install -r requirements.txt")
    token = getpass.getpass("IBM Cloud API key (input hidden): ").strip()
    if not token:
        die("No key entered.")
    instance = input("Instance CRN (optional; press Enter to skip): ").strip() or None
    QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token=token, instance=instance,
                                      set_as_default=True, overwrite=True)
    print("Saved. Next: python3 handshake.py ibm-check")


def do_ibm_check():
    """Check the IBM connection and list usable QPUs. Submits nothing; uses no quota."""
    try:
        service = ibm_service()
    except RuntimeError as e:
        die(str(e))
    backends = service.backends(min_num_qubits=NUMBER_BITS, operational=True, simulator=False)
    if not backends:
        die("Connected, but no operational QPU with >= 24 qubits is available to this account.")
    print(f"Connected. QPUs with >= {NUMBER_BITS} qubits available to this account:")
    for b in sorted(backends, key=lambda b: b.status().pending_jobs):
        print(f"  {b.name:<18} {b.num_qubits:>4} qubits   pending jobs: {b.status().pending_jobs}")
    try:
        print(f"Usage: {service.usage()}")
    except Exception:
        pass
    print("Next: python3 handshake.py ibm-trial  (submits one real job; uses a few seconds of quota)")


def do_ibm_trial(mode="real"):
    """Measure how long an IBM job takes from submission to completion. Not part of any test."""
    try:
        _, backend = ibm_backend(mode)
    except RuntimeError as e:
        die(str(e))
    t_submit = utcnow()
    job = ibm_submit(backend, tags=["HANDSHAKE-001-TRIAL"] if mode == "real" else None)
    print(f"Trial job {job.job_id()} submitted to {backend.name} at {iso(t_submit)}")
    status = ibm_wait(job)
    t_end = utcnow()
    stamps = ibm_timestamps(job)
    total = t_end - t_submit
    print(f"\nStatus: {status}\nServer timestamps: {stamps or 'n/a'}\nTotal wall time: {total}")
    if status == "DONE":
        number_hex, bits = ibm_result_hex(job)
        print(f"Trial result (not a test): {bits} -> {number_hex}")
    hours = max(3, math.ceil(3 * total.total_seconds() / 3600))
    print(f"\nSuggested T1 - T0: at least {hours} hours (3x this trial, minimum 3). "
          "Queue times vary a lot; try at the same weekday/hour you plan to use, ideally more than once.")


def do_rehearse(args):
    t1 = parse_iso(args.t1) if args.t1 else (utcnow() - timedelta(hours=1)).replace(second=0, microsecond=0)
    if t1 > utcnow() - timedelta(minutes=2):
        die("A rehearsal must use a target that is already published (T1 in the past).")
    cfg = {"experiment_id": "HANDSHAKE-001-REHEARSAL", "t0": t1 - timedelta(hours=3), "t1": t1}
    base = ROOT / "rehearsal" / utcnow().strftime("%Y%m%dT%H%M%SZ")
    print(f"REHEARSAL - NOT A TEST: the target at {iso(t1)} is already public.\n")
    job = do_start(cfg, base, draw_anu if args.anu == "anu" else draw_os, args.ibm, enforce=False, stamp=False)
    if args.ibm != "none" and job is not None:
        do_commit_ibm(cfg, base, job=job, enforce=False, stamp=False)
    do_fetch_target(cfg, base, enforce=False, stamp=False)
    do_reveal(cfg, base)
    print("\n--- secondary targets (complete only if T1 is more than 7 days in the past) ---")
    do_fetch_secondary(cfg, base, enforce=False, stamp=False)
    print("\n--- independent verification ---")
    ok = do_verify(cfg, base)
    voids = [d for d in DRAWS if paths(base, d)["void"].exists()]
    expected = {"ANU"} | ({"IBM"} if args.ibm != "none" else set())
    ok &= not (expected & set(voids))
    print(f"\nRehearsal files: {base}")
    if voids:
        print(f"Void draws in this rehearsal: {', '.join(voids)} - see public/*_void.json")
    print(f"REHEARSAL {'PASSED' if ok else 'FAILED'} (pipeline check only; every expected draw must be valid).")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("setup-ibm", "ibm-check", "ibm-trial", "preflight", "start", "commit-ibm", "fetch-target", "reveal",
                 "fetch-secondary"):
        sub.add_parser(name)
    po = sub.add_parser("postpone", help="before start: move T0 and T1 by exactly 24 hours (max 7)")
    po.add_argument("--reason", required=True)
    vo = sub.add_parser("void", help="record a void the script cannot detect (e.g. a late X post)")
    vo.add_argument("--draw", choices=list(DRAWS), required=True)
    vo.add_argument("--reason", required=True)
    v = sub.add_parser("verify")
    for draw in ("anu", "ibm"):
        v.add_argument(f"--{draw}-sha256", help=f"{draw.upper()} SHA-256 as posted on X")
        v.add_argument(f"--{draw}-sha3-512", help=f"{draw.upper()} SHA3-512 as posted on X")
    v.add_argument("--offline", action="store_true", help="use the saved target files instead of re-fetching")
    r = sub.add_parser("rehearse")
    r.add_argument("--t1", help="past target time, e.g. 2026-10-05T18:55:00Z (default: one hour ago)")
    r.add_argument("--anu", choices=["os", "anu"], default="os", help="'anu' uses one request of your monthly quota")
    r.add_argument("--ibm", choices=["none", "fake", "real"], default="fake",
                   help="'fake' simulates locally (requirements-dev.txt); 'real' uses a few seconds of IBM quota")
    args = p.parse_args()

    if args.cmd == "rehearse":
        return do_rehearse(args)
    if args.cmd == "setup-ibm":
        return do_setup_ibm()
    if args.cmd == "ibm-check":
        return do_ibm_check()
    if args.cmd == "ibm-trial":
        return do_ibm_trial()
    cfg = load_config()
    if args.cmd == "preflight":
        sys.exit(0 if do_preflight(cfg, ROOT) else 1)
    elif args.cmd == "postpone":
        do_postpone(cfg, ROOT, args.reason)
    elif args.cmd == "start":
        do_start(cfg, ROOT)
    elif args.cmd == "commit-ibm":
        do_commit_ibm(cfg, ROOT)
    elif args.cmd == "fetch-target":
        do_fetch_target(cfg, ROOT)
    elif args.cmd == "reveal":
        do_reveal(cfg, ROOT)
    elif args.cmd == "fetch-secondary":
        do_fetch_secondary(cfg, ROOT)
    elif args.cmd == "void":
        do_void(cfg, ROOT, args.draw, args.reason)
    elif args.cmd == "verify":
        posted = {d.upper(): {"sha256": getattr(args, f"{d}_sha256"), "sha3_512": getattr(args, f"{d}_sha3_512")}
                  for d in ("anu", "ibm") if getattr(args, f"{d}_sha256") and getattr(args, f"{d}_sha3_512")}
        sys.exit(0 if do_verify(cfg, ROOT, posted, args.offline) else 1)


if __name__ == "__main__":
    main()
