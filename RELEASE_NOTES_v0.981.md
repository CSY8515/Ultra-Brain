# Ultra Brain v0.981

## Production UI correction

- Restored the Streamlit world as a single full-viewport surface so the concept art, title and OS Ecosystem seed render in the correct positions.
- Added explicit theme-world assets for Light, Dark, Minimal and Paper instead of reusing the Official image.
- Passed the applied theme, world and revision through the OS Ecosystem hand-off URL for downstream propagation.
- Kept the Ultra Brain solar concept as the Official world and preserved the hierarchy for each theme world.
- Tightened the UI Studio canvas layout, compacted tool panels and made tools toggle off when selected again.

## Validation

- Streamlit entry compiles successfully.
- Sites production bundle builds successfully.
- Rendered HTML tests pass.
