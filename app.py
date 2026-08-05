"""Official Streamlit entry point for Ultra Brain v0.8.

This module is intentionally limited to bootstrap concerns. The existing UI
implementation remains under ``ui/app`` and is not reimplemented here.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st


REPOSITORY_ROOT = Path(__file__).resolve().parent
EXISTING_UI_ENTRY = REPOSITORY_ROOT / "ui" / "app" / "page.tsx"


def load_existing_ui_entry() -> Path:
    """Resolve the existing UI entry without changing or reimplementing it."""

    if not EXISTING_UI_ENTRY.is_file():
        raise FileNotFoundError(f"Existing UI entry was not found: {EXISTING_UI_ENTRY}")
    return EXISTING_UI_ENTRY


def main() -> None:
    """Start the official Ultra Brain Streamlit bootstrap."""

    st.set_page_config(
        page_title="Ultra Brain",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    ui_entry = load_existing_ui_entry()
    relative_entry = ui_entry.relative_to(REPOSITORY_ROOT).as_posix()

    st.title("Ultra Brain")
    st.caption("Official Streamlit bootstrap for the existing Ultra Brain UI.")
    st.markdown(f"Existing UI entry: `{relative_entry}`")


if __name__ == "__main__":
    main()
