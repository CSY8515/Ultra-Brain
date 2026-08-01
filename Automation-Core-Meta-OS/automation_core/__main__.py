"""Minimal local verification entry point; this does not start a service."""

from .validation import CONTRACT_VERSION


if __name__ == "__main__":
    print(f"Automation Core Meta OS {CONTRACT_VERSION}: local caller-driven runtime")
