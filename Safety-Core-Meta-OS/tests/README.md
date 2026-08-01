# Safety Core Automated Tests

The v0.2 suite uses only `unittest` and temporary directories outside the
repository. It covers strict validation, deterministic risk boundaries,
fail-closed execution, monitoring, incidents, hash-chain tamper detection,
bounded backup/recovery, and frozen Foundation/other-Meta-OS protection.

Run from `Safety-Core-Meta-OS/`:

```text
python -B -m unittest discover -s tests -v
```

Tests do not perform network calls, execute external commands, install
dependencies, overwrite existing recovery targets, or modify governed
repository artifacts.
