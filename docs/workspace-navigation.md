# Workspace navigation contract

The authenticated entry `/bienvenida/` opens `#/catalogo/observabilidad`.
Only Home is active on this route. The areas directory remains available from
the applications icon; it is not the login destination.

Application Back follows the hierarchy below. Browser Back/Forward follows the
actual visited sequence; neither is implemented by guessing a browser history
entry or returning every tool to Government.

| View | Application return |
| --- | --- |
| Diagram library root | Home / Observability |
| Diagram group | Diagram library root |
| Diagram editor | Its library group and ownership tab |
| Editor integrations | Same editor |
| Government | Home breadcrumb |
| Standards root | Government |
| Standards family | Standards root |
| Standards subfamily | Its family |
| Component standard | Its subfamily |
| Identity / controls / evidence / relationships | Component standard |
| Discovery connections | Home |
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
