# Design Token Standard

Tokens are resolved from a Theme Profile and exposed as CSS custom properties. Required groups are `color`, `typography`, `shape`, `shadow`, `layout`, and `motion`, matching OS Ecosystem `ultra-brain.ui/v1`.

Screen components must not introduce unregistered palette or motion values. Feature-specific values use a scoped override and record their source. Unsafe CSS fragments, unknown fields, and incompatible contract versions fail before preview or forwarding.
