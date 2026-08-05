# Official UI Architecture

The implementation is isolated under `ui/` and does not modify OS Ecosystem, Living OS, or Universal Learning Engine source. `app/ultra-brain-shell.tsx` owns the semantic shell, `lib/theme-engine.js` resolves preferences, and CSS consumes resolved tokens.

The shell contains Orientation, World, Navigation, Status, Notification, and Settings surfaces. UI state is device-local. External propagation is represented and validated but no transport or downstream runtime mutation is introduced in v0.8.
