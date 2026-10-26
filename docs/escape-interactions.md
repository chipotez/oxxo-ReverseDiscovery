# Escape and identity editing

Use `useEscapeLayer(active, close, priority)` for floating panels. One Escape
closes the foremost modal, then a panel's current detail, then its summary,
then the canvas selection. A native select popup consumes its own dismissal.
Dirty forms must ask before leaving; Escape never means discard or save.
Use `confirmDialog` for queued, accessible confirmations with explicit actions.
Compact confirmations size to their content within the shared dialog shell.

Visible resource identity text opens the governed Identity form. Imported
legacy fields are explicitly incorporated into a new standard version for
that resource before editing. Other resources keep their pinned versions.
The address field accepts multiple IPs or DNS names, one per line, and stores
that text in the existing standard-defined `address` field. No parallel
untyped metadata field is introduced.

Regression: `scripts/qa_identity_escape.py` uses disposable diagrams only.

Identity and control editors use one complete form, not pagination derived
from the tallest field. Desktop forms use two columns; narrow/short viewports
scroll the form body while preserving the heading and synchronization state.
The `address` field displays as IPs and Ctrl/Command + Enter inserts a newline.
Editor and resource forms rely on acknowledged autosave; recovery actions
remain available when saving fails. Comment navigation centers its anchor.
