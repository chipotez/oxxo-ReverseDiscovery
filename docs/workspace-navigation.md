# Workspace navigation contract

The authenticated entry `/bienvenida/` opens `#/catalogo` (Tu espacio de trabajo).
Only Home is active on this route. The duplicate applications icon is removed.
Observability is a discipline within this directory.

Application Back follows the hierarchy below. Browser Back/Forward follows the
actual visited sequence; neither is implemented by guessing a browser history
entry or returning every tool to Government.

| View | Application return |
| --- | --- |
| Diagram library root | Home / areas directory |
| Diagram group | Diagram library root |
| Diagram editor | Its library group and ownership tab |
| Editor integrations | Same editor |
| Government | Home breadcrumb |
| Standards root | Government |
| Standards family | Standards root |
| Standards subfamily | Its family |
| Component standard | Its subfamily |
| Identity / controls / evidence / relationships | Component standard |
| Discovery connections | Observability |
| Discovery configuration or results | Connections |
| Discovery API explorer | Results or connections, according to entry point |
| Course detail from Training | Training |
| Course or use-case detail from Observability | Observability |

Nested React views record semantic URL parameters with `recordView`, without
remounting the live editor on each local transition. Hash changes and browser
history events restore those parameters. Group IDs, diagram IDs and standard
classification/section are navigation context, not editable document values.
Credentials and form contents are never placed in navigation URLs.

Before leaving a diagram, pending online edits must flush successfully. A failed
flush keeps the current view. Standard draft edits retain their existing custom
leave confirmation. Opening a direct component-standard link canonicalizes its
initial URL with replacement so Forward history is not erased by initialization.

Legacy mapping routes resolve to the diagram library. Unknown routes resolve to
Home. A single router owns the selected rail icon and Services/Modules state;
the shell must not independently overwrite these states or page headings.

## Verification

`scripts/qa_navigation.py` traverses every catalog family, subfamily, component,
and four standard sections, checking rendered hierarchical return and browser Back/Forward.
Stable GET responses from disposable fixtures are replayed after their first actual
read, so the recursive audit does not hammer the database for identical models.
It also covers login landing, groups, editor refresh and ownership context.
`scripts/qa_navigation_shell.py` covers directory entries, courses, legacy routes,
unknown routes, discovery, editor integrations, guest landing and the Home rail
at four viewport sizes in both themes. Both use the disposable QA environment.

Node interaction: hover never opens an editor. Single click selects; identity
summary text remains draggable. Double click on that text (or Enter) opens
Identity directly. Explicit category icons retain their click action. Legacy
visible fields are prepared automatically when entering Identity, preserving
values and pinning the resulting standard version. No migration confirmation is
shown. A partially clipped node is centered after selection at the current zoom;
a short delay distinguishes a single click from double click or drag. Ctrl/Meta/
Shift multiselection does not pan the viewport. Focus strengthens the existing
border, without a second outer outline.
