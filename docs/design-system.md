# Interface design

Koodaria uses light, slightly green surfaces and mineral text. Forest green is
reserved for actions and emphasis. Quiet borders, rounded surfaces, and limited
shadows connect the public site and identity screens.

| Role | Color |
| --- | --- |
| Canvas | `#f8faf7` |
| Card | `#ffffff` |
| Primary text | `#243c39` |
| Secondary text | `#576560` |
| Action | `#2f6557` |
| Action hover / link | `#28594d` |
| Navigation | `#edf3ed` |
| Essential input boundary | `#738779` |

Use the same complete light palette even when the operating system prefers dark
mode until a separately verified dark palette exists. Keycloak's account theme
sets `darkMode=false`; it does not partially override an active dark theme.

The wordmark is live lowercase text, system font, weight 500, 34px (31px on small
screens), line-height 1.2, letter-spacing -1.5px, with a forest green dot. Align it
with the public shell, not with the account sidebar.

Every view must adapt to both viewport dimensions. Prefer two-column forms on
wide screens, compact spacing on short screens, and progressive steps where the
content cannot fit legibly. Never crop fields or errors to conceal overflow.
Keep native scrolling as an accessibility fallback for extreme zoom, long user
content, and software keyboards. Lists require pagination as they grow. Native
security validation and identity actions must remain functional.

Validate at least 1440×800, 1366×768, 1024×600, 390×844, 375×667,
320×568, and 844×390; check document and inner-panel overflow, reachable primary
actions, keyboard use, and light/dark OS preferences. Measure contrast rather
than judging color pairs only by appearance. Account-specific QA uses disposable
identities and excludes secrets from evidence.

The authenticated shell uses a compact floating header (maximum 1100px) and a
64px icon rail (52px on phones). On short landscape windows the rail arranges
icons in two columns so every action remains reachable. The central canvas is
currently empty; retain a screen-reader heading for the selected section.
The appearance control has an explicit mineral-green dark palette; do not mix
its text and surface values with the light palette. Theme preference is local
and contains no identity data. Login and account-management themes retain their
separately verified light palette.
