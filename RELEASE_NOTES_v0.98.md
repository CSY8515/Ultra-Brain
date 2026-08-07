# Ultra Brain v0.98

## UI Studio UX Refinement · Official Theme Evolution

- Added an independent `기본 조정` workspace for brightness, contrast, saturation, hue, texture, lighting, shadow, glow, transparency, and blur.
- Kept those adjustments when switching official themes so the controls are not tied to a single palette.
- Removed the separate preview tab; user UI preview now lives inside the editor and returns to editing without applying changes.
- Consolidated beginner image imports into one `가져오기` action and translated the visible creator workflow into Korean.
- Reduced duplicated English labels and renamed the editor controls around screens, elements, layers, and change history.
- Kept the approved solar concept art for Official and added subject-specific world images for Universe, Ecosystem, Ocean, Grassland, Lava, Galaxy, Minimal, Paper, and Archive. Each image carries its own decorations and central world/dome interior while preserving the Ultra Brain hierarchy.
- Updated the Streamlit production entry point to use the same v0.98 world assets, Korean UI Studio controls, independent adjustments, and lock/automatic-apply settings without a permanent sidebar.
- Completed the Streamlit Studio flow with theme preview-before-save, save/cancel, user image import, layout controls, per-target locks, and revision rollback.
- Kept hierarchy propagation, lock, override, rollback, and revision behavior intact.

Validation: vinext build, rendered UI tests, foundation validation, and regression tests passed.
