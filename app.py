"""Ultra Brain v0.97 Streamlit production UI entry point.

The source of truth for the visual direction remains the existing Vinext UI in
``ui/app``. This entry point maps that same world scene into Streamlit without
changing the React implementation or introducing a second product flow.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Final

import streamlit as st


REPOSITORY_ROOT: Final = Path(__file__).resolve().parent
EXISTING_UI_ENTRY: Final = REPOSITORY_ROOT / "ui" / "app" / "page.tsx"
WORLD_ART: Final = REPOSITORY_ROOT / "ui" / "public" / "ultra-brain-world.png"
OS_ECOSYSTEM_URL: Final = "https://8javbq85jtappi6tkdhkt7g.streamlit.app/"

THEMES: Final = {
    "Official": {
        "accent": "#c8a55d",
        "accent_bright": "#f0d58a",
        "surface": "rgba(6, 15, 16, .78)",
        "surface_strong": "rgba(9, 22, 22, .94)",
        "text": "#f1ede2",
        "text_soft": "#aeb9af",
        "line": "rgba(195, 167, 96, .34)",
        "world_filter": "brightness(1.08) saturate(.9)",
    },
    "Dark": {
        "accent": "#83aa8c",
        "accent_bright": "#bcd3af",
        "surface": "rgba(5, 13, 16, .82)",
        "surface_strong": "rgba(8, 19, 23, .95)",
        "text": "#eef2ed",
        "text_soft": "#9eaaa5",
        "line": "rgba(128, 169, 146, .30)",
        "world_filter": "brightness(.74) saturate(.72) hue-rotate(8deg)",
    },
    "Light": {
        "accent": "#7a5b25",
        "accent_bright": "#a47a2f",
        "surface": "rgba(239, 235, 216, .84)",
        "surface_strong": "rgba(246, 243, 226, .96)",
        "text": "#20251f",
        "text_soft": "#566057",
        "line": "rgba(92, 75, 40, .32)",
        "world_filter": "brightness(1.16) saturate(.55) sepia(.28)",
    },
}


def load_existing_ui() -> None:
    """Assert that the existing UI source and its art asset are present."""

    if not EXISTING_UI_ENTRY.is_file():
        raise FileNotFoundError(f"Existing UI source not found: {EXISTING_UI_ENTRY}")
    if not WORLD_ART.is_file():
        raise FileNotFoundError(f"Existing UI art asset not found: {WORLD_ART}")


@st.cache_data(show_spinner=False)
def world_art_data_uri() -> str:
    """Load the existing concept art once and inline it for Streamlit HTML."""

    return "data:image/png;base64," + base64.b64encode(WORLD_ART.read_bytes()).decode("ascii")


def render_sidebar(theme_name: str, theme: dict[str, str]) -> tuple[str, str, str, bool, bool]:
    """Render the global navigation and the existing theme-control foundation."""

    with st.sidebar:
        st.markdown(
            """
            <div class="ub-side-brand">
              <span class="ub-side-sigil">✦</span>
              <span><strong>Ultra Brain</strong><small>v0.8 · Official UI</small></span>
            </div>
            <div class="ub-side-rule"></div>
            <div class="ub-side-kicker">GLOBAL NAVIGATION</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <a class="ub-side-nav is-current" href="{OS_ECOSYSTEM_URL}" target="_blank" rel="noreferrer">
              <span class="ub-side-nav-icon">⌂</span>
              <span><strong>OS Ecosystem</strong><small>Connected system</small></span>
              <b>↗</b>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="ub-side-section">
              <span>CONNECTION</span>
              <strong><i class="ub-health-dot"></i> Healthy</strong>
              <small>OS Ecosystem v0.74 · active</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="ub-side-kicker ub-side-kicker-settings">THEME CONTROLS</div>', unsafe_allow_html=True)
        selected_theme = st.selectbox("Theme profile", list(THEMES), index=list(THEMES).index(theme_name), label_visibility="collapsed")
        selected_accent = st.color_picker("Accent", theme["accent"], label_visibility="visible")
        density = st.selectbox("Density", ["compact", "comfortable", "spacious"], index=1, format_func=lambda value: value.title())
        motion = st.toggle("Motion", value=True)
        locked = st.toggle("Lock OS Ecosystem propagation", value=False)
        st.markdown(
            f"""
            <div class="ub-side-footer">
              <span>UI SYSTEM</span><strong>ultra-brain.ui/v1</strong>
              <small>{'Propagation locked' if locked else 'Propagation compatible'}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return selected_theme, selected_accent, density, motion, locked


def build_css(theme: dict[str, str], accent: str, density: str, motion: bool) -> str:
    """Return the shared token layer and world-first layout styles."""

    space = {"compact": ".84", "comfortable": "1", "spacious": "1.16"}[density]
    accent_bright = theme["accent_bright"] if accent.lower() == theme["accent"].lower() else accent
    motion_css = "" if motion else "*:not(.ub-world-art):not(.ub-focus-art){transition:none!important;animation:none!important;}"
    return f"""
    <style>
      :root {{
        --ub-accent: {accent};
        --ub-accent-bright: {accent_bright};
        --ub-surface: {theme['surface']};
        --ub-surface-strong: {theme['surface_strong']};
        --ub-text: {theme['text']};
        --ub-text-soft: {theme['text_soft']};
        --ub-line: {theme['line']};
        --ub-space: {space};
      }}
      html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > section {{
        background: #020707 !important; color: var(--ub-text) !important;
      }}
      [data-testid="stHeader"] {{ background: transparent !important; }}
      [data-testid="stMainBlockContainer"] {{ max-width: none !important; padding: 0 !important; }}
      [data-testid="stMainBlockContainer"] > div {{ padding: 0 !important; }}
      [data-testid="stSidebar"] {{
        min-width: 248px; max-width: 248px; background: linear-gradient(180deg, #071113 0%, #040909 100%) !important;
        border-right: 1px solid var(--ub-line);
      }}
      [data-testid="stSidebar"] > div:first-child {{ padding: 20px 16px 22px; }}
      [data-testid="stSidebar"] * {{ font-family: Arial, sans-serif; }}
      [data-testid="stSidebar"] label {{ color: var(--ub-text-soft) !important; font-size: 10px !important; letter-spacing: .08em; }}
      [data-testid="stSidebar"] [data-baseweb="select"] > div {{ background: rgba(255,255,255,.025); border-color: var(--ub-line); color: var(--ub-text); }}
      [data-testid="stSidebar"] [data-testid="stColorPicker"] {{ margin-bottom: 8px; }}
      [data-testid="stSidebar"] [data-testid="stToggle"] label {{ font-size: 11px !important; letter-spacing: .02em; color: var(--ub-text) !important; }}
      [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{ margin-bottom: 3px; }}
      .ub-side-brand {{ display:flex; align-items:center; gap:11px; color:var(--ub-text); }}
      .ub-side-brand > span:last-child {{ display:grid; gap:3px; }}
      .ub-side-brand strong {{ font:600 16px/1 Georgia, serif; letter-spacing:.04em; }}
      .ub-side-brand small {{ color:var(--ub-text-soft); font-size:9px; letter-spacing:.12em; text-transform:uppercase; }}
      .ub-side-sigil {{ display:grid; place-items:center; width:34px; height:34px; border:1px solid var(--ub-line); color:var(--ub-accent-bright); font-size:16px; transform:rotate(45deg); }}
      .ub-side-sigil::first-letter {{ transform:rotate(-45deg); }}
      .ub-side-rule {{ height:1px; margin:18px 0 21px; background:linear-gradient(90deg,var(--ub-line),transparent); }}
      .ub-side-kicker {{ margin:0 0 9px; color:var(--ub-text-soft); font-size:9px; letter-spacing:.14em; }}
      .ub-side-kicker-settings {{ margin-top:25px; }}
      .ub-side-nav {{ display:grid; grid-template-columns:27px 1fr 18px; align-items:center; gap:8px; padding:11px 9px; border:1px solid var(--ub-line); background:rgba(200,165,93,.08); color:var(--ub-text); text-decoration:none; }}
      .ub-side-nav:hover {{ border-color:var(--ub-accent); background:rgba(200,165,93,.13); }}
      .ub-side-nav-icon {{ display:grid; place-items:center; width:24px; height:24px; border:1px solid var(--ub-line); color:var(--ub-accent-bright); }}
      .ub-side-nav span:nth-child(2) {{ display:grid; gap:3px; }}
      .ub-side-nav strong {{ font-size:11px; font-weight:600; }}
      .ub-side-nav small {{ color:var(--ub-text-soft); font-size:9px; }}
      .ub-side-nav b {{ color:var(--ub-accent-bright); font-weight:400; }}
      .ub-side-section {{ display:grid; gap:7px; margin-top:18px; padding:13px 10px; border:1px solid rgba(195,167,96,.16); background:rgba(255,255,255,.018); }}
      .ub-side-section span {{ color:var(--ub-text-soft); font-size:8px; letter-spacing:.13em; }}
      .ub-side-section strong {{ display:flex; align-items:center; gap:7px; font-size:11px; }}
      .ub-side-section small {{ color:var(--ub-text-soft); font-size:9px; }}
      .ub-health-dot {{ display:inline-block; width:6px; height:6px; border-radius:50%; background:#94b67a; box-shadow:0 0 9px #94b67a; }}
      .ub-side-footer {{ display:grid; gap:5px; margin-top:27px; padding-top:14px; border-top:1px solid var(--ub-line); color:var(--ub-text-soft); font-size:9px; }}
      .ub-side-footer span {{ letter-spacing:.12em; }}
      .ub-side-footer strong {{ color:var(--ub-text); font:500 13px Georgia, serif; }}
      .ub-side-footer small {{ color:var(--ub-accent-bright); }}
      .ub-shell {{ position:relative; min-height:100vh; width:100%; overflow:hidden; isolation:isolate; background:#020707; }}
      .ub-world-art, .ub-focus-art {{ position:absolute; inset:0; width:100%; height:100%; background-position:center; background-repeat:no-repeat; pointer-events:none; }}
      .ub-world-art {{ z-index:0; background-size:contain; filter:{theme['world_filter']}; opacity:.98; transform:scale(1.002); }}
      .ub-focus-art {{ z-index:2; background-size:contain; opacity:0; clip-path:ellipse(9.5% 9.5% at 50% 70%); filter:brightness(1.18) saturate(1.12) drop-shadow(0 0 18px rgba(232,190,100,.42)); transform:scale(1); transform-origin:50% 70%; transition:opacity .35s ease,clip-path .4s ease,transform .4s cubic-bezier(.22,.61,.36,1),filter .4s ease; }}
      .ub-vignette {{ position:absolute; inset:0; z-index:1; pointer-events:none; background:linear-gradient(180deg,rgba(1,5,7,.22),transparent 18%,transparent 78%,rgba(1,5,6,.2)),radial-gradient(circle at 50% 44%,transparent 44%,rgba(0,3,4,.32) 100%); }}
      .ub-topbar {{ position:absolute; z-index:8; top:18px; left:22px; right:22px; min-height:54px; display:flex; justify-content:space-between; align-items:center; padding:10px 14px; border:1px solid var(--ub-line); background:linear-gradient(90deg,var(--ub-surface-strong),var(--ub-surface),var(--ub-surface-strong)); box-shadow:0 18px 48px rgba(0,0,0,.28); backdrop-filter:blur(18px); }}
      .ub-topbar::after {{ content:""; position:absolute; left:50%; bottom:-1px; width:160px; height:1px; transform:translateX(-50%); background:var(--ub-accent); box-shadow:0 0 16px var(--ub-accent); opacity:.72; }}
      .ub-path {{ display:flex; align-items:center; gap:12px; color:var(--ub-text-soft); font-size:10px; letter-spacing:.12em; text-transform:uppercase; }}
      .ub-path i {{ color:var(--ub-accent); font-style:normal; }}
      .ub-path strong {{ color:var(--ub-text); font-weight:500; }}
      .ub-health {{ display:flex; align-items:center; gap:8px; color:var(--ub-text-soft); font-size:9px; letter-spacing:.1em; text-transform:uppercase; }}
      .ub-health b {{ display:inline-block; width:6px; height:6px; border-radius:50%; background:#94b67a; box-shadow:0 0 9px #94b67a; }}
      .ub-world-center {{ position:absolute; z-index:3; top:37%; left:50%; width:min(390px,42vw); transform:translate(-50%,-50%); text-align:center; pointer-events:none; text-shadow:0 2px 18px rgba(0,0,0,.98),0 0 22px rgba(0,0,0,.82); }}
      .ub-world-center h1 {{ margin:10px 0; color:var(--ub-accent-bright); font:500 clamp(26px,2.7vw,40px)/1 Georgia,serif; letter-spacing:.045em; }}
      .ub-title-rule {{ display:block; width:76%; height:1px; margin:0 auto; background:linear-gradient(90deg,transparent,var(--ub-accent),transparent); box-shadow:0 0 10px color-mix(in srgb,var(--ub-accent) 42%,transparent); }}
      .ub-title-rule-top {{ width:52%; }}
      .ub-seed {{ position:absolute; z-index:6; left:50%; bottom:12.5%; width:clamp(190px,18vw,280px); height:clamp(190px,23vh,260px); transform:translateX(-50%); color:var(--ub-text); text-align:center; text-decoration:none; border-radius:48% 48% 42% 42%; transition:transform .35s cubic-bezier(.22,.61,.36,1); }}
      .ub-seed-aura {{ position:absolute; inset:2% 8% 5%; border:1px solid transparent; border-radius:50%; background:radial-gradient(circle,transparent 45%,color-mix(in srgb,var(--ub-accent) 15%,transparent) 72%,transparent 73%); opacity:0; transform:scale(.88); transition:.38s ease; }}
      .ub-seed-copy {{ position:absolute; left:50%; top:50%; display:grid; justify-items:center; gap:3px; width:100%; transform:translate(-50%,-50%); color:var(--ub-text) !important; text-shadow:0 2px 12px #000,0 2px 22px #000; transition:transform .35s ease; }}
      .ub-seed-copy strong {{ color:var(--ub-text) !important; font:500 clamp(16px,1.8vw,24px)/1.1 Georgia,serif; letter-spacing:.035em; }}
      .ub-seed-action {{ margin-top:5px; padding:5px 10px; color:var(--ub-text); font-size:10px; letter-spacing:.05em; opacity:0; transform:translateY(4px); transition:.25s ease; }}
      .ub-seed-action b {{ margin-left:6px; color:var(--ub-accent-bright); }}
      .ub-seed:hover, .ub-seed:focus-visible {{ transform:translateX(-50%) scale(1.035); outline:2px solid var(--ub-accent-bright); outline-offset:4px; }}
      .ub-seed:hover .ub-seed-aura, .ub-seed:focus-visible .ub-seed-aura {{ opacity:1; transform:scale(1.08); border-color:var(--ub-accent); box-shadow:0 0 44px color-mix(in srgb,var(--ub-accent) 20%,transparent),inset 0 0 25px color-mix(in srgb,var(--ub-accent) 12%,transparent); }}
      .ub-seed:hover .ub-seed-copy, .ub-seed:focus-visible .ub-seed-copy {{ transform:translate(-50%,-50%) translateY(-9px); }}
      .ub-seed:hover .ub-seed-action, .ub-seed:focus-visible .ub-seed-action {{ opacity:1; transform:translateY(0); color:var(--ub-accent-bright); }}
      .ub-seed:hover ~ .ub-focus-art, .ub-seed:focus-visible ~ .ub-focus-art {{ opacity:1; clip-path:ellipse(10.4% 10.4% at 50% 70%); transform:scale(1.045); filter:brightness(1.28) saturate(1.2) drop-shadow(0 0 28px rgba(242,202,118,.6)); }}
      .ub-rail {{ position:absolute; z-index:8; right:24px; top:50%; transform:translateY(-50%); display:grid; justify-items:center; gap:7px; color:var(--ub-text-soft); font-size:9px; letter-spacing:.08em; text-align:center; }}
      .ub-rail a {{ display:grid; place-items:center; width:42px; aspect-ratio:1; border:1px solid var(--ub-line); background:var(--ub-surface); color:var(--ub-accent-bright); text-decoration:none; font-size:16px; transition:.22s ease; }}
      .ub-rail a:hover {{ border-color:var(--ub-accent); box-shadow:0 0 18px color-mix(in srgb,var(--ub-accent) 16%,transparent); }}
      .ub-status {{ position:absolute; z-index:8; left:22px; bottom:18px; display:flex; align-items:center; gap:12px; min-height:38px; padding:6px 12px; border:1px solid var(--ub-line); background:var(--ub-surface); color:var(--ub-text-soft); font-size:9px; letter-spacing:.06em; backdrop-filter:blur(16px); }}
      .ub-status strong {{ color:var(--ub-text); font-weight:500; }}
      .ub-status i {{ width:1px; height:12px; background:var(--ub-line); }}
      .ub-status-dot {{ width:6px; height:6px; border-radius:50%; background:#94b67a; box-shadow:0 0 9px #94b67a; }}
      {motion_css}
      @media (max-width:760px) {{
        [data-testid="stSidebar"] {{ min-width:210px; max-width:210px; }}
        .ub-topbar {{ top:10px; left:10px; right:10px; }}
        .ub-topbar .ub-health {{ display:none; }}
        .ub-world-art, .ub-focus-art {{ background-size:cover; }}
        .ub-world-center {{ top:35%; width:72vw; }}
        .ub-world-center h1 {{ font-size:28px; }}
        .ub-seed {{ bottom:15%; width:220px; height:235px; }}
        .ub-focus-art {{ clip-path:ellipse(15% 9.5% at 50% 70%); }}
        .ub-seed:hover ~ .ub-focus-art, .ub-seed:focus-visible ~ .ub-focus-art {{ clip-path:ellipse(16.5% 10.4% at 50% 70%); }}
        .ub-rail {{ right:12px; }}
        .ub-status {{ left:10px; right:10px; justify-content:center; }}
      }}
      [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stHeader"], [data-testid="stToolbar"], footer {{ display:none !important; }}
      .ub-studio-launch {{ position:absolute; z-index:8; top:24px; left:24px; display:inline-flex; align-items:center; gap:8px; min-height:40px; padding:6px 11px; border:1px solid var(--ub-line); background:rgba(6,15,16,.72); color:var(--ub-text); font:600 10px Arial,sans-serif; letter-spacing:.08em; text-transform:uppercase; }}
      .ub-studio-launch b {{ display:grid; place-items:center; width:22px; height:22px; border:1px solid var(--ub-line); color:var(--ub-accent-bright); font-size:12px; }}
    </style>
    """


def render_world(theme: dict[str, str], accent: str, density: str, motion: bool) -> None:
    """Render the existing world-first UI composition with Streamlit HTML."""

    art = world_art_data_uri()
    st.markdown(build_css(theme, accent, density, motion), unsafe_allow_html=True)
    st.markdown(
        f"""
        <main class="ub-shell" aria-label="Ultra Brain">
          <div class="ub-world-art" style="background-image:url('{art}')"></div>
          <div class="ub-vignette" aria-hidden="true"></div>
          <div class="ub-studio-launch"><b>✦</b><span>UI Studio</span></div>
          <section class="ub-world-center" aria-label="Ultra Brain central identity">
            <span class="ub-title-rule ub-title-rule-top"></span>
            <h1>Ultra Brain</h1>
            <span class="ub-title-rule"></span>
          </section>
          <a class="ub-seed" href="{OS_ECOSYSTEM_URL}" target="_blank" rel="noreferrer" aria-label="Open OS Ecosystem">
            <span class="ub-seed-aura" aria-hidden="true"></span>
            <span class="ub-seed-copy"><strong>OS Ecosystem</strong></span>
          </a>
          <div class="ub-focus-art" style="background-image:url('{art}')" aria-hidden="true"></div>
        </main>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Run the official Ultra Brain Streamlit UI."""

    st.set_page_config(page_title="Ultra Brain v0.97", layout="wide", initial_sidebar_state="collapsed")
    load_existing_ui()
    render_world(THEMES["Official"], THEMES["Official"]["accent"], "comfortable", True)


if __name__ == "__main__":
    main()
