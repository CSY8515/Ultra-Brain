"""Ultra Brain v0.98 Streamlit production entry point.

The Streamlit surface mirrors the official Ultra Brain world view.  The
default screen stays quiet and world-first; the only visible control is the
UI Studio button.  Theme selection swaps the complete world asset (including
its central world structure and interior details), while the basic visual
adjustments remain available independently from theme selection.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path
from typing import Final

import streamlit as st


VERSION: Final = "0.98"
REPOSITORY_ROOT: Final = Path(__file__).resolve().parent
EXISTING_UI_ENTRY: Final = REPOSITORY_ROOT / "ui" / "app" / "page.tsx"
PUBLIC_ROOT: Final = REPOSITORY_ROOT / "ui" / "public"
WORLD_ART: Final = PUBLIC_ROOT / "ultra-brain-world.png"
OS_ECOSYSTEM_URL: Final = "https://8javbq85jtappi6tkdhkt7g.streamlit.app/"


THEMES: Final = {
    "Official": {
        "asset": "ultra-brain-world.png",
        "accent": "#c8a55d",
        "accent_bright": "#f0d58a",
        "surface": "rgba(6, 15, 16, .82)",
        "surface_strong": "rgba(9, 22, 22, .96)",
        "text": "#f1ede2",
        "text_soft": "#aeb9af",
        "line": "rgba(195, 167, 96, .38)",
        "filter": "brightness(1.02) saturate(.92)",
        "world": "태양 중심 생명의 나무 세계",
        "detail": "중앙 태양 구체와 나무, 아래쪽 생태계 돔",
        "layout": "solar",
    },
    "Universe": {
        "asset": "world-universe.png",
        "accent": "#9d91e8",
        "accent_bright": "#d5ceff",
        "surface": "rgba(8, 8, 27, .86)",
        "surface_strong": "rgba(14, 12, 39, .97)",
        "text": "#f0efff",
        "text_soft": "#aaa8c7",
        "line": "rgba(157, 145, 232, .38)",
        "filter": "brightness(.92) saturate(.94)",
        "world": "궤도와 별빛의 우주 세계",
        "detail": "중앙 궤도 구체, 성운 고리, 별빛으로 된 내부 장식",
        "layout": "cosmic",
    },
    "Ecosystem": {
        "asset": "world-ecosystem.png",
        "accent": "#79b67b",
        "accent_bright": "#c4e6af",
        "surface": "rgba(5, 19, 12, .86)",
        "surface_strong": "rgba(8, 28, 17, .97)",
        "text": "#eff8e9",
        "text_soft": "#a8c3aa",
        "line": "rgba(121, 182, 123, .38)",
        "filter": "brightness(.94) saturate(1.08)",
        "world": "숲과 물이 이어지는 생태계 세계",
        "detail": "돔 속 나무와 물길, 잎 장식, 살아 있는 숲의 중심",
        "layout": "canopy",
    },
    "Ocean": {
        "asset": "world-ocean.png",
        "accent": "#56b8cf",
        "accent_bright": "#b8f0fa",
        "surface": "rgba(3, 16, 24, .88)",
        "surface_strong": "rgba(4, 25, 36, .97)",
        "text": "#edfaff",
        "text_soft": "#9bc1cc",
        "line": "rgba(86, 184, 207, .4)",
        "filter": "brightness(.98) saturate(1.05)",
        "world": "파도와 심해의 바다 세계",
        "detail": "바다 돔, 수면 아래 빛, 산호와 해저 생태 장식",
        "layout": "oceanic",
    },
    "Grassland": {
        "asset": "world-grassland.png",
        "accent": "#668744",
        "accent_bright": "#b6dc7a",
        "surface": "rgba(35, 49, 26, .78)",
        "surface_strong": "rgba(50, 67, 35, .94)",
        "text": "#f7f8df",
        "text_soft": "#d5dfbd",
        "line": "rgba(170, 207, 112, .42)",
        "filter": "brightness(1.02) saturate(1.06)",
        "world": "햇살과 바람의 초원 세계",
        "detail": "열린 들판, 빛나는 돔, 바람에 흔들리는 식물 장식",
        "layout": "field",
    },
    "Lava": {
        "asset": "world-lava.png",
        "accent": "#e87943",
        "accent_bright": "#ffc08e",
        "surface": "rgba(28, 8, 5, .88)",
        "surface_strong": "rgba(43, 12, 7, .97)",
        "text": "#fff1e7",
        "text_soft": "#d2a897",
        "line": "rgba(232, 121, 67, .44)",
        "filter": "brightness(1.02) saturate(1.1)",
        "world": "화산과 용암의 핵 세계",
        "detail": "용암이 흐르는 중앙 핵, 열기와 화산 암석 장식",
        "layout": "molten",
    },
    "Galaxy": {
        "asset": "world-galaxy.png",
        "accent": "#df86b8",
        "accent_bright": "#ffc7e5",
        "surface": "rgba(24, 8, 25, .88)",
        "surface_strong": "rgba(35, 10, 33, .97)",
        "text": "#fff0f8",
        "text_soft": "#c9a7bc",
        "line": "rgba(223, 134, 184, .42)",
        "filter": "brightness(.98) saturate(1.08)",
        "world": "성운과 은하의 빛 세계",
        "detail": "분홍 성운, 회전하는 은하, 빛나는 핵과 궤도 장식",
        "layout": "nebula",
    },
    "Minimal": {
        "asset": "world-universe.png",
        "accent": "#d2d7d0",
        "accent_bright": "#ffffff",
        "surface": "rgba(14, 17, 17, .86)",
        "surface_strong": "rgba(22, 26, 25, .97)",
        "text": "#f5f7f3",
        "text_soft": "#a7afaa",
        "line": "rgba(210, 215, 208, .3)",
        "filter": "brightness(.9) saturate(.2)",
        "world": "핵심 구조만 남긴 절제된 세계",
        "detail": "중앙 구조와 궤도만 남기고 장식을 정돈한 표현",
        "layout": "minimal",
    },
    "Archive": {
        "asset": "world-archive.png",
        "accent": "#b49b78",
        "accent_bright": "#e6d7b8",
        "surface": "rgba(22, 17, 12, .88)",
        "surface_strong": "rgba(31, 24, 17, .97)",
        "text": "#f2e9da",
        "text_soft": "#b7a994",
        "line": "rgba(180, 155, 120, .4)",
        "filter": "brightness(.94) saturate(.62) sepia(.2)",
        "world": "청동 기록과 보관의 세계",
        "detail": "기록 장치, 청동 고리, 보관된 세계의 돔 내부",
        "layout": "archive",
    },
}


ADJUSTMENTS: Final = {
    "밝기": (0.7, 1.3, 1.0),
    "명암": (0.7, 1.4, 1.0),
    "채도": (0.5, 1.5, 1.0),
    "색조": (-30.0, 30.0, 0.0),
    "광원": (0.0, 1.5, 1.0),
    "그림자": (0.4, 1.6, 1.0),
    "발광": (0.0, 1.8, 1.0),
    "질감": (0.0, 1.5, 1.0),
    "흐림": (0.0, 8.0, 0.0),
    "투명도": (0.45, 1.0, 1.0),
}


def load_existing_ui() -> None:
    """Verify that the official UI source and world assets are available."""

    if not EXISTING_UI_ENTRY.is_file():
        raise FileNotFoundError(f"Official UI source not found: {EXISTING_UI_ENTRY}")
    if not WORLD_ART.is_file():
        raise FileNotFoundError(f"Official concept art not found: {WORLD_ART}")


@lru_cache(maxsize=None)
def world_art_data_uri(filename: str) -> str:
    """Inline a checked-in world image for a single Streamlit render."""

    path = PUBLIC_ROOT / filename
    if not path.is_file():
        path = WORLD_ART
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def reset_adjustments() -> None:
    for key, (_, _, default) in ADJUSTMENTS.items():
        st.session_state[f"adjustment_{key}"] = default


def build_css(theme: dict[str, str]) -> str:
    values = {key: st.session_state.get(f"adjustment_{key}", default) for key, (_, _, default) in ADJUSTMENTS.items()}
    return f"""
    <style>
      :root {{
        --ub-accent: {st.session_state.get('accent', theme['accent'])};
        --ub-accent-bright: {theme['accent_bright']};
        --ub-surface: {theme['surface']};
        --ub-surface-strong: {theme['surface_strong']};
        --ub-text: {theme['text']};
        --ub-text-soft: {theme['text_soft']};
        --ub-line: {theme['line']};
        --ub-brightness: {values['밝기']};
        --ub-contrast: {values['명암']};
        --ub-saturation: {values['채도']};
        --ub-hue: {values['색조']}deg;
        --ub-lighting: {values['광원']};
        --ub-shadow: {values['그림자']};
        --ub-glow: {values['발광']};
        --ub-texture: {values['질감']};
        --ub-blur: {values['흐림']}px;
        --ub-transparency: {values['투명도']};
      }}
      html, body, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {{
        background:#020707 !important; color:var(--ub-text) !important;
      }}
      [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], footer {{ display:none !important; }}
      [data-testid="stMainBlockContainer"] {{ max-width:none !important; padding:0 !important; }}
      [data-testid="stMainBlockContainer"] > div {{ padding:0 !important; }}
      .ub-shell {{ position:relative; min-height:calc(100vh - 1px); width:100%; overflow:hidden; isolation:isolate; background:#020707; }}
      .ub-world-art {{ position:absolute; inset:0; z-index:0; width:100%; height:100%; background-image:url('{world_art_data_uri(theme['asset'])}'); background-position:center; background-repeat:no-repeat; background-size:contain; filter:{theme['filter']} brightness(var(--ub-brightness)) contrast(var(--ub-contrast)) saturate(var(--ub-saturation)) hue-rotate(var(--ub-hue)); opacity:var(--ub-transparency); transform:scale(1.002); }}
      .ub-world-art::after {{ content:""; position:absolute; inset:0; background:radial-gradient(circle at 50% 44%, transparent 38%, rgba(0,3,4,calc(.34 * var(--ub-shadow))) 100%); pointer-events:none; }}
      .ub-vignette {{ position:absolute; inset:0; z-index:1; pointer-events:none; background:linear-gradient(180deg,rgba(1,5,7,.18),transparent 18%,transparent 78%,rgba(1,3,4,.28)); }}
      .ub-world-light {{ position:absolute; inset:0; z-index:2; pointer-events:none; background:radial-gradient(circle at 50% 44%, var(--ub-accent), transparent 28%); opacity:calc(.12 * var(--ub-lighting) * var(--ub-glow)); mix-blend-mode:screen; }}
      .ub-world-texture {{ position:absolute; inset:0; z-index:2; pointer-events:none; background:repeating-radial-gradient(circle at 50% 44%, transparent 0 24px, color-mix(in srgb, var(--ub-accent) 8%, transparent) 25px 26px); opacity:calc(.18 * var(--ub-texture)); mix-blend-mode:soft-light; }}
      .ub-launch-slot {{ position:absolute; z-index:10; top:22px; left:24px; }}
      .ub-launch-slot button {{ min-height:38px; border:1px solid var(--ub-line); background:var(--ub-surface); color:var(--ub-text); font:600 10px Arial,sans-serif; letter-spacing:.08em; }}
      .ub-launch-slot button:hover {{ border-color:var(--ub-accent); color:var(--ub-accent-bright); }}
      .ub-world-center {{ position:absolute; z-index:5; top:37%; left:50%; width:min(420px,42vw); transform:translate(-50%,-50%); text-align:center; pointer-events:none; text-shadow:0 2px 18px rgba(0,0,0,.98),0 0 22px rgba(0,0,0,.82); }}
      .ub-world-center h1 {{ margin:10px 0; color:var(--ub-accent-bright); font:500 clamp(27px,2.8vw,38px)/1 Georgia,serif; letter-spacing:.045em; }}
      .ub-rule {{ display:block; width:72%; height:1px; margin:0 auto; background:linear-gradient(90deg,transparent,var(--ub-accent),transparent); box-shadow:0 0 calc(12px * var(--ub-glow)) var(--ub-accent); }}
      .ub-ecosystem {{ position:absolute; z-index:6; left:50%; bottom:12.5%; width:clamp(190px,18vw,280px); min-height:150px; transform:translateX(-50%); display:grid; place-items:center; color:var(--ub-text); text-decoration:none; border-radius:50%; transition:transform .35s ease, filter .35s ease; }}
      .ub-ecosystem::before {{ content:""; position:absolute; inset:0; border:1px solid transparent; border-radius:50%; background:radial-gradient(circle,transparent 45%,color-mix(in srgb,var(--ub-accent) 15%,transparent) 72%,transparent 73%); opacity:0; transition:.35s ease; }}
      .ub-ecosystem span {{ position:relative; color:var(--ub-text); font:500 clamp(14px,1.45vw,19px)/1.1 Georgia,serif; text-shadow:0 2px 12px #000,0 2px 22px #000; }}
      .ub-ecosystem:hover, .ub-ecosystem:focus-visible {{ transform:translateX(-50%) scale(1.055); filter:brightness(1.08); outline:none; }}
      .ub-ecosystem:hover::before, .ub-ecosystem:focus-visible::before {{ opacity:1; border-color:var(--ub-accent); box-shadow:0 0 44px color-mix(in srgb,var(--ub-accent) 20%,transparent),inset 0 0 25px color-mix(in srgb,var(--ub-accent) 12%,transparent); }}
      .ub-status {{ position:absolute; z-index:7; left:24px; bottom:20px; display:flex; gap:10px; align-items:center; padding:8px 12px; border:1px solid var(--ub-line); background:var(--ub-surface); color:var(--ub-text-soft); font-size:9px; }}
      .ub-dot {{ width:6px; height:6px; border-radius:50%; background:#94b67a; box-shadow:0 0 9px #94b67a; }}
      .ub-studio-panel {{ position:fixed; z-index:30; top:20px; right:20px; width:min(520px,calc(100vw - 40px)); max-height:calc(100vh - 40px); overflow:auto; padding:20px; border:1px solid var(--ub-line); background:linear-gradient(145deg,var(--ub-surface-strong),rgba(2,8,9,.96)); box-shadow:0 24px 80px rgba(0,0,0,.55); backdrop-filter:blur(18px); }}
      .ub-studio-panel h2 {{ margin:0 0 6px; font:500 20px Georgia,serif; color:var(--ub-accent-bright); }}
      .ub-studio-panel p {{ margin:0 0 14px; color:var(--ub-text-soft); font-size:11px; line-height:1.6; }}
      .ub-panel-title {{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:12px; }}
      .ub-panel-title small {{ color:var(--ub-text-soft); font-size:9px; }}
      .ub-world-note {{ margin:12px 0 16px; padding:11px; border:1px solid var(--ub-line); background:color-mix(in srgb,var(--ub-accent) 7%,transparent); color:var(--ub-text-soft); font-size:10px; line-height:1.55; }}
      .ub-divider {{ height:1px; margin:16px 0; background:var(--ub-line); opacity:.65; }}
      .ub-help {{ color:var(--ub-text-soft); font-size:10px; line-height:1.5; }}
      @media (max-width:760px) {{ .ub-world-art {{ background-size:cover; }} .ub-world-center {{ top:35%; width:76vw; }} .ub-world-center h1 {{ font-size:28px; }} .ub-ecosystem {{ bottom:15%; width:220px; }} .ub-status {{ left:12px; right:12px; justify-content:center; }} .ub-launch-slot {{ top:12px; left:12px; }} }}
    </style>
    """


def render_studio(theme: dict[str, str]) -> None:
    """Render the v0.98 controls without exposing a permanent sidebar."""

    st.markdown('<section class="ub-studio-panel" aria-label="UI 스튜디오">', unsafe_allow_html=True)
    st.markdown('<div class="ub-panel-title"><h2>UI 스튜디오</h2><small>Ultra Brain 기준 화면</small></div>', unsafe_allow_html=True)
    st.markdown('<p>테마를 고르면 색만 바뀌지 않습니다. 해당 세계의 이미지, 돔 내부, 장식, 빛과 질감이 함께 바뀝니다.</p>', unsafe_allow_html=True)
    tab_theme, tab_adjust, tab_apply = st.tabs(["테마", "기본 조정", "자동 적용"])
    with tab_theme:
        selected = st.selectbox("테마 선택", list(THEMES), index=list(THEMES).index(st.session_state["theme"]))
        if selected != st.session_state["theme"]:
            st.session_state["theme"] = selected
            st.rerun()
        current = THEMES[selected]
        st.markdown(f'<div class="ub-world-note"><strong>{current["world"]}</strong><br />{current["detail"]}<br /><span class="ub-help">Ultra Brain → Meta OS → OS Ecosystem → 하위 요소의 단계 구조는 유지됩니다.</span></div>', unsafe_allow_html=True)
        st.session_state["accent"] = st.color_picker("강조 색", st.session_state.get("accent", current["accent"]))
    with tab_adjust:
        st.caption("테마와 관계없이 기본 화면에 바로 적용되는 조정입니다.")
        for key, (minimum, maximum, default) in ADJUSTMENTS.items():
            state_key = f"adjustment_{key}"
            st.session_state[state_key] = st.slider(key, minimum, maximum, st.session_state.get(state_key, default), step=0.01 if key != "색조" else 1.0)
        if st.button("기본값으로 되돌리기", key="reset_adjustments"):
            reset_adjustments()
            st.rerun()
    with tab_apply:
        st.markdown('<div class="ub-world-note"><strong>자동 적용 범위</strong><br />잠금하지 않은 설정은 OS Ecosystem과 하위 계층으로 전달됩니다.<br />잠금한 대상은 현재 모습을 유지합니다.</div>', unsafe_allow_html=True)
        st.session_state["ecosystem_locked"] = st.checkbox("OS Ecosystem 잠금", value=st.session_state.get("ecosystem_locked", False))
        st.session_state["propagation_override"] = st.checkbox("OS Ecosystem 예외 적용", value=st.session_state.get("propagation_override", False))
        st.markdown('<div class="ub-help">현재 연결된 범위: OS Ecosystem. 하위 전용 편집기는 만들지 않고, Ultra Brain 기준 설정을 자동 적용합니다.</div>', unsafe_allow_html=True)
    st.markdown('</section>', unsafe_allow_html=True)


def render_world(theme: dict[str, str]) -> None:
    art = world_art_data_uri(theme["asset"])
    st.markdown(build_css(theme), unsafe_allow_html=True)
    st.markdown('<div class="ub-shell">', unsafe_allow_html=True)
    st.markdown(f'<div class="ub-world-art" style="background-image:url(\'{art}\')"></div><div class="ub-vignette"></div><div class="ub-world-light"></div><div class="ub-world-texture"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ub-launch-slot">', unsafe_allow_html=True)
    if st.button("✦  UI 스튜디오", key="studio_launch"):
        st.session_state["studio_open"] = not st.session_state["studio_open"]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<section class="ub-world-center" aria-label="Ultra Brain"><span class="ub-rule"></span><h1>Ultra Brain</h1><span class="ub-rule"></span></section>', unsafe_allow_html=True)
    st.markdown(f'<a class="ub-ecosystem" href="{OS_ECOSYSTEM_URL}" target="_blank" rel="noreferrer" aria-label="OS Ecosystem 열기"><span>OS Ecosystem</span></a><div class="ub-status"><span class="ub-dot"></span><strong>정상</strong><span>OS Ecosystem 연결됨</span><span>v{VERSION}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state["studio_open"]:
        render_studio(theme)


def main() -> None:
    st.set_page_config(page_title=f"Ultra Brain v{VERSION}", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")
    load_existing_ui()
    st.session_state.setdefault("theme", "Official")
    st.session_state.setdefault("studio_open", False)
    st.session_state.setdefault("accent", THEMES["Official"]["accent"])
    for key, (_, _, default) in ADJUSTMENTS.items():
        st.session_state.setdefault(f"adjustment_{key}", default)
    theme = THEMES[st.session_state["theme"]]
    render_world(theme)


if __name__ == "__main__":
    main()
