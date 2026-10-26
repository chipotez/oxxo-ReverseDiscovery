# Koodaria interface rules

Apply these rules to every new or changed view: Home, authentication, required
account actions, account management, dialogs, and future product screens.

- Use the available viewport **width and height**, including browser zoom and
  mobile keyboards. Use responsive CSS and progressive steps when a form does
  not fit. Keep primary actions visible at normal desktop and mobile sizes.
- Never obtain a no-scroll result by clipping content, hiding validation,
  disabling scrolling, applying CSS zoom, or shrinking the entire interface.
  Long collections must use meaningful pagination or separate views. At high
  accessibility zoom, allow scrolling instead of making text unreadable.
- Keep the Home wordmark's font, weight, size, and shell alignment across screens.
- Use the forest/mineral/sage palette in docs/design-system.md. Do not combine
  dark-mode text tokens with light surfaces. Test both OS color preferences.
- Meet WCAG AA text contrast (4.5:1 for ordinary text, 3:1 for large text) and
  3:1 for essential control boundaries and focus indication. Preserve native
  validation, accessible labels, keyboard access, and visible focus.
- Verify actual rendered content and action visibility at desktop, tablet,
  mobile, and short landscape viewports. A screenshot alone does not prove that
  an inner panel has no overflow.
- Use disposable accounts for identity QA. Never capture QR codes, OTP secrets,
  passwords, tokens, or real customer data in screenshots or evidence.
- New hierarchical selection dialogs must reuse `app/frontend/src/selection-dialog.jsx`
  and follow `docs/selection-dialog-spec.md` for dimensions, semantics, cascading
  selection, responsive pagination, focus, and confirmation behavior.
