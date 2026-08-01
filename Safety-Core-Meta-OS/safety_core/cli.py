"""Narrow local command-line adapter for Safety Core Meta OS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .audit import AuditLedger
from .common import CONTRACT_VERSION, canonical_json, load_json_strict
from .core import SafetyCore
from .errors import SafetyCoreError
from .validation import load_policy


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policies" / "default_policy.json"


def _emit(value: Any) -> None:
    print(canonical_json(value))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safety-core")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("validate", help="Validate the installed default policy.")

    assess = commands.add_parser("assess", help="Evaluate one execution request.")
    assess.add_argument("request", type=Path)
    assess.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    assess.add_argument("--ledger", type=Path)
    assess.add_argument("--expected-ledger-count", type=int)
    assess.add_argument("--expected-ledger-head")

    verify_log = commands.add_parser("verify-log", help="Verify an audit JSONL chain.")
    verify_log.add_argument("ledger", type=Path)
    verify_log.add_argument("--expected-count", type=int, required=True)
    verify_log.add_argument("--expected-head", required=True)

    backup = commands.add_parser("backup", help="Create a verified backup archive.")
    backup.add_argument("source", type=Path)
    backup.add_argument("archive", type=Path)

    recover = commands.add_parser(
        "recover", help="Recover a verified archive into a new destination."
    )
    recover.add_argument("archive", type=Path)
    recover.add_argument("destination", type=Path)
    return parser


def run(arguments: list[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    if args.command == "validate":
        policy = load_policy(DEFAULT_POLICY)
        _emit(
            {
                "status": "passed",
                "version": CONTRACT_VERSION,
                "policy": policy.id,
            }
        )
    elif args.command == "assess":
        core = SafetyCore.open(
            args.policy,
            args.ledger,
            expected_ledger_count=args.expected_ledger_count,
            expected_ledger_head=args.expected_ledger_head,
        )
        decision = core.assess_execution(load_json_strict(args.request))
        _emit(decision.to_dict())
    elif args.command == "verify-log":
        report = AuditLedger(args.ledger).verify(
            expected_count=args.expected_count,
            expected_head=args.expected_head,
        )
        _emit(report)
    elif args.command == "backup":
        core = SafetyCore(load_policy(DEFAULT_POLICY))
        _emit(core.create_backup(args.source, args.archive))
    elif args.command == "recover":
        core = SafetyCore(load_policy(DEFAULT_POLICY))
        _emit(core.recover_backup(args.archive, args.destination))
    return 0


def main() -> int:
    try:
        return run()
    except (SafetyCoreError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": type(exc).__name__,
                    "reason": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
