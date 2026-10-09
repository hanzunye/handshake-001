# HANDSHAKE-001

A pre-registered, single-shot test of whether information can arrive at a quantum random draw from a later time. The test uses two independent draws, one from ANU and one from IBM.

- **Protocol (authoritative):** [`PREREGISTRATION.md`](PREREGISTRATION.md)
- **How to check everything yourself:** [`VERIFY.md`](VERIFY.md)
- **Tool:** [`handshake.py`](handshake.py). Python 3.9+. Running the draws needs `pip3 install -r requirements.txt`; verifying needs only the standard library.
- **Author:** Han Yunze (X: [@DavonGluck](https://x.com/DavonGluck))

| | |
|---|---|
| Status | not yet run |
| Pre-registration post | {{link}} |
| Zenodo DOI (pre-registration) | [10.5281/zenodo.23269344](https://doi.org/10.5281/zenodo.23269344) |
| Live stream | {{link}} |
| T0 / T1 (UTC) | 2026-10-12T08:00:00Z / 2026-10-12T11:00:00Z (10:00 / 13:00 CEST) |
| Commitment posts | ANU: {{link}} · IBM: {{link}} |
| Result | {{DOUBLE HIT / HIT (ANU) / HIT (IBM) / INCONCLUSIVE}} |

## Outline

At T0, two 24-bit quantum numbers are drawn and committed: one from the ANU QRNG service, and one from 24 qubits measured on IBM Quantum hardware. A secret salt keeps each number hidden. At T1, the NIST Randomness Beacon publishes an unpredictable value. A draw is a HIT if its 6 hex characters equal the first 6 hex characters of that value; by chance this happens with probability 1 in 16,777,216 per draw. A single miss refutes nothing.

## Trial and rehearsal

```
python3 handshake.py ibm-trial                  # measures the real IBM queue time
python3 handshake.py rehearse --ibm fake        # full pipeline, IBM simulated locally (needs requirements-dev.txt)
python3 handshake.py rehearse --anu anu --ibm real
```

Rehearsals use a target that is already public, so they never count as a test.

## License

To the extent possible under law, the author has waived all copyright and related rights to this work under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
