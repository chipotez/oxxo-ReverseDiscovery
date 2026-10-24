# Inspección y decisiones — 22 de octubre de 2026

## Evidencia previa a la implementación

Repositorio `/Users/imip/Documents/iMIP-Repos/oxxo-ReverseDiscovery`, remoto `chipotez/oxxo-ReverseDiscovery`. Git sin commits; rama inicial `dev` con upstream inexistente. No había frontend, framework, dependencias, CI ni estrategia de despliegue. El único archivo del usuario era `koodaria-v2-standalone.zip`, con tres HTML independientes: Home, Enterprise y Workspace. Se conservó sin modificar. Su checksum se registra en `reference.txt`; no se importaron sus páginas como aplicación.

Se creó `feature/koodaria-public-home-v1` antes de implementar. Aplicación e infraestructura se mantienen separadas en directorios y commits. No había AGENTS.md en el árbol inspeccionado.

Servidor `yard-hostinger`, Fedora 44, acceso SSH administrativo por Tailscale. Podman rootless de `mip`. Cinco contenedores existentes: `themike-site`, `themike-postgres`, `themike-keycloak`, `themike-portal-ui`, `themike-portal-auth`. Redes `podman`, `themike-auth`, `themike-ops`. Persistencia en tres volúmenes endurecidos para Postgres y Caddy; ninguno se monta en Koodaria.

El Caddy existente recibe 80/443 mediante los puertos 8080/8443 del host; administra TLS para `themike.io`, `www.themike.io` y `login.themike.io`. Sirve la landing y enruta el portal mediante OAuth2 Proxy hacia Keycloak. Se inspeccionaron Caddyfile y Quadlets de usuario. No hay virtual host de Koodaria ni entorno de desarrollo previo dedicado. No se modificaron archivos existentes ni autenticación.

## Arquitectura elegida

Home pública precompilada con Python estándar, HTML semántico, CSS y módulos JavaScript nativos. Una Home editorial con pestañas y desplegables no necesita un framework, base de datos o servidor de APIs. La salida es un único artefacto estático, pero sus componentes, datos, tokens e interacciones se desarrollan por separado: no son tres maquetas desconectadas.

El JSON centraliza contenido repetitivo y navegación; el compilador reutiliza funciones para tarjetas, catálogo e iconos y escapa todos los valores editoriales. El JavaScript se limita a interacciones progresivas. Los tipos de catálogo se documentan con JSDoc; Python valida identificadores y nombres de iconos. No se afirma una comprobación TypeScript que este stack no realiza.

Paleta actual: verde mineral `#193A37`, bosque `#2F6557`, acento oscuro `#28594D`, salvia `#85A69D`, fondos verde claro `#F3F6F1` / `#F8FAF7`, blanco y oscuro técnico `#141D27`. Los botones principales usan texto blanco sobre verde bosque. Por preferencia explícita del usuario, esta paleta sustituye los acentos cobre, marrón y arena iniciales. Iconos oficiales Tabler locales, SVG outline de trazo 1.4. Fuentes del sistema para evitar descargas de terceros.

El runtime reutiliza por ID inmutable la imagen local de Caddy ya parcheada. Se ejecuta como UID 1000, sirviendo únicamente `/koodaria` por HTTP interno; no es una segunda entrada de reverse proxy, no administra certificados y no configura rutas hacia otros servicios. Su Caddyfile está separado del proxy global. La imagen base contiene también archivos estáticos heredados, que no se sirven: el root es `/koodaria`. Una base mínima independiente sería una mejora posterior, tras mantener los parches verificados del runtime.

## Identidad desplegada — 23 de octubre de 2026

Keycloak 26.8.1 comparte la instalación existente, pero Koodaria usa un realm independiente. `login.koodaria.com` tiene certificado de Let’s Encrypt renovado por el Caddy existente. El atributo `frontendUrl` del realm fija el emisor y los endpoints en ese dominio. El hostname global del laboratorio se conserva; `KC_HOSTNAME_ADMIN` y el frontend de master apuntan al dominio de Koodaria para administrar sin pasar por themike.io. El acceso del laboratorio se verificó después del cambio.

`/login` y `/login/` en koodaria.com inician el cliente confidencial `koodaria-web` y terminan en `/bienvenida/`. La gestión nativa de cuenta (`account-console`) permanece accesible desde el menú personal. La Home no recibe contraseñas, secretos de cliente ni tokens. El backend mínimo de bienvenida y su sesión se describen abajo.

El flujo propio `koodaria-browser-2fa` exige usuario/contraseña y luego OTP. El subflujo OTP es obligatorio y sus condiciones de omisión están deshabilitadas. `CONFIGURE_TOTP` está habilitado como acción predeterminada; aun cuando una cuenta se cree sin acciones pendientes, el flujo exige configurar el autenticador. Se conserva el orden explícito de ejecución: contraseña antes de OTP. Sin una sesión SSO vigente, los accesos posteriores exigen ambos factores. Las sesiones SSO existentes pueden reutilizarse hasta expirar o cerrar sesión.

Registro público deshabilitado, contraseña mínima de 14 caracteres, protección contra intentos repetidos y concesiones directas de contraseña deshabilitadas. TOTP de seis dígitos cada 30 segundos, compatible con aplicaciones autenticadoras habituales. Recuperación de contraseña deshabilitada hasta configurar SMTP. Los eventos de acceso se conservan 30 días; los eventos administrativos no incluyen detalles completos para evitar registrar datos sensibles.

### Organizaciones

El usuario eligió separar cada empresa cliente. Existe una organización `Kyndryl` sin miembros ni dominios. No se inventaron empresas ni usuarios reales. Las organizaciones son pares dentro del realm, no una jerarquía anidada. La relación comercial Kyndryl–cliente y sus permisos cruzados deberán modelarse explícitamente en el backend futuro. El correo por sí solo no concede membresía. La pertenencia a organizaciones no sustituye los controles de autorización sobre los datos.

### Operación y validación

Configuración declarativa en `infra/keycloak/koodaria-realm.json`, tema en `infra/keycloak/themes/koodaria`, proxy en `infra/edge/koodaria-identity.caddy`. Los scripts de provisionamiento requieren una cuenta de servicio administrativa y un archivo privado (600); no usan contraseñas humanas. La cuenta temporal de recuperación se retira al finalizar el despliegue; el MFA del administrador humano se conserva.

Se respaldó Postgres antes de modificarlo en `/home/mip/backups/koodaria-20261023/before-identity.dump` (directorio privado). Las unidades y el Caddyfile anteriores están en `/root/remediation-20261023/koodaria-identity`. Para rollback del acceso público, restaurar las unidades del gateway y su Caddyfile; el realm nuevo puede conservarse deshabilitado sin tocar los realms del laboratorio. No restaurar toda la base sobre datos posteriores sin una revisión previa.

Las pruebas de navegador verifican contraseña incorrecta, alta inicial por QR, rechazo de código inválido, acceso con código correcto y exigencia de TOTP en una sesión nueva. Las cuentas de QA se eliminan. Evidencias sin contraseñas, códigos ni semillas: `evidence/keycloak-2fa-report.json` y `evidence/keycloak-publication-report.json`.

Referencias oficiales: https://www.keycloak.org/docs/latest/server_admin/, https://www.keycloak.org/server/hostname y https://www.keycloak.org/server/bootstrap-admin-recovery.

## Límites y evolución

Enterprise y Workspace continúan informativos. No hay pipeline automático ni registro remoto de imágenes. La política de privacidad final, el contacto, SMTP y la asignación de empresas/usuarios reales requieren datos institucionales. El inicio de sesión actual muestra la bienvenida y permite gestionar la cuenta; no implica acceso a herramientas o datos empresariales todavía no implementados.

## Bienvenida autenticada — 23 de octubre de 2026

El acceso público `/login[/]` ahora inicia el cliente confidencial `koodaria-web`.
Después de contraseña, MFA y cualquier acción de perfil requerida, Keycloak
regresa exclusivamente a `https://koodaria.com/auth/callback`. El servidor usa
Authlib con Authorization Code, PKCE S256, estado y nonce; valida el ID token
antes de mostrar `/bienvenida/`. El cliente no admite flujos implícitos,
contraseña directa ni cuentas de servicio. No se cambiaron las reglas de MFA.

La bienvenida corre en `koodaria-workspace`, un contenedor sin puerto público,
con filesystem de solo lectura y volumen de sesiones. Flask-Session guarda los
datos de sesión y el ID token en el servidor. El navegador recibe únicamente un
identificador opaco `__Host-koodaria`, Secure, HttpOnly, SameSite=Lax y sin Domain.
La sesión local dura como máximo 30 minutos; no se conservan access/refresh tokens.
El ID se regenera después de autenticar. Los datos visibles se escapan al renderizar.

El menú permite abrir la gestión nativa de cuenta o volver a la Home. Cerrar
sesión requiere POST y token CSRF; elimina la sesión local y ejecuta el cierre
OIDC de Keycloak antes de volver al inicio. La ruta autenticada y sus respuestas
usan `Cache-Control: no-store`; la política de la Home se aplica separadamente.
Los callbacks y las peticiones de logout no entran en el access log de Caddy,
para evitar registrar códigos o hints de identidad.

El alias de red `login.koodaria.com` en el gateway permite a la aplicación
consultar discovery, tokens y claves por HTTPS verificado dentro de la red de
Podman, conservando el emisor público. No se deshabilita la validación TLS.

Es una bienvenida mínima con Servicios/Módulos y menú de usuario. Todavía no
hay catálogo privado, permisos sobre recursos empresariales ni backend de
laboratorios. Las organizaciones permanecen separadas según la decisión previa;
la bienvenida no concede permisos por dominio de correo ni cambia membresías.

Referencias de implementación: [Authlib Flask](https://docs.authlib.org/en/latest/oauth2/client/web/flask.html),
[Flask-Session](https://flask-session.readthedocs.io/en/latest/config.html),
[Caddy log_skip](https://caddyserver.com/docs/caddyfile/directives/log_skip).

## Catálogo y documentación de servicios

El espacio autenticado ahora abre el catálogo de Cloud, Automatización,
Observabilidad, DevOps, SecOps, Infraestructura como código y SRE. La navegación
usa fragmentos bajo `/bienvenida/`, por lo que conserva la protección de sesión
existente sin añadir rutas públicas de datos ni cambiar el flujo OIDC.

Observabilidad contiene nueve fichas: tres herramientas de mapeo, tres niveles
de cursos y tres casos de uso (Datadog + ServiceNow, Datadog + Ansible y escenarios
de operación). Solo Mapeo de servicios está habilitado como herramienta. Los
cursos, las otras herramientas y las integraciones muestran su alcance previsto
y el estado En preparación. Las demás disciplinas tienen su entrada y estado
pendiente; no se presentan contenidos o conectores inexistentes como disponibles.

El editor inicial de Mapeo de servicios permite crear y editar hasta doce
componentes, conectar un origen con otro componente, quitar nodos, consultar
la disposición automática, ampliar/mover la vista y exportar SVG. El proyecto
JSON versionado puede descargarse y reabrirse. Se rechazan proyectos excesivos,
IDs duplicados, tipos desconocidos, referencias ausentes y ciclos. Los textos
se escapan tanto en el HTML como en SVG; las importaciones se reducen al modelo
permitido. La vista gráfica y los campos no ejecutan contenido importado.

Los proyectos viven únicamente en memoria del navegador. La interfaz lo indica
y advierte al salir con cambios sin descargar. No se envían diagramas, archivos,
nombres de servicios o credenciales a un backend; no se conserva el proyecto
tras recargar sin exportarlo. El servidor sigue almacenando solo la sesión de
identidad. La persistencia compartida, los permisos por organización y los
conectores operativos siguen siendo trabajo posterior.

La paginación del catálogo calcula filas y columnas según ancho y alto reales.
En móvil se usan un selector de contenido, vistas separadas para la ficha y
pasos del editor; la lista de componentes también se pagina. No se oculta el
scroll mediante recortes. Las secciones desplegadas explícitamente y la
ampliación de accesibilidad conservan su comportamiento nativo.

## Editor de recursos con React Flow

La tarjeta Mapeo de recursos abre directamente `#/herramientas/mapeo-recursos`.
El antiguo enlace a su ficha también resuelve a la herramienta. En esta vista se oculta
el header del catálogo y el lienzo ocupa el área de trabajo junto a la navegación
lateral. El editor previo de Mapeo de servicios se conserva por separado.

Implementación real con React 19 y `@xyflow/react` 12, compilada por esbuild en
una etapa Node de la imagen. Dependencias bloqueadas en
`app/frontend/package-lock.json`; los bundles JS/CSS se sirven desde el propio
dominio, sin CDN ni scripts externos. La atribución de React Flow se conserva.

Permite añadir recursos y grupos, arrastrar nodos, conectar puntos, editar
nombre/tipo/IP/puerto y etiquetas de conexión, agrupar y redimensionar, eliminar,
acercar/alejar y ajustar la vista. El lienzo se reajusta al cambiar de tamaño.
Las propiedades tienen una distribución compacta en ventanas bajas. Las paletas
clara y oscura siguen la preferencia de Koodaria.

Los mapas se almacenan como documentos JSONB en PostgreSQL dedicado, con UUID,
propietario OIDC, nombre, fecha y revisión. La tarjeta abre una biblioteca paginada
que adapta la cantidad de mapas al área disponible. Cada mapa puede editarse y
retomarse desde la cuenta; el guardado automático se realiza tras 900 ms sin
cambios y serializa las escrituras. La revisión evita sobrescribir cambios de otra
pestaña. Los conflictos permiten guardar una copia. Los fallos conservan el estado
en la pestaña y muestran reintento; no se promete edición offline persistente.

Las rutas `/bienvenida/api/diagrams` requieren una sesión vigente. Las escrituras
requieren CSRF, y el sujeto se toma exclusivamente de la identidad verificada.
Cada consulta restringe el propietario; PostgreSQL añade RLS forzado con identidad
local a la transacción y un rol web sin privilegios administrativos. La API no
acepta organización o propietario elegidos por el navegador. Los diagramas no se
comparten automáticamente por dominio de correo ni por membresía de empresa.

El servidor valida y reconstruye el modelo permitido: máximo 200 nodos, 500
conexiones, coordenadas/dimensiones acotadas, referencias válidas y textos con
longitud limitada. No acepta componentes React arbitrarios, HTML, estilos libres
ni URLs ejecutables. Los textos se renderizan mediante el escape de React.

La descarga es PDF del documento guardado: mapa vectorial completo más inventario
legible de recursos y conexiones, sin depender del zoom o el encuadre del editor.
La generación ocurre en el servidor, sin navegador remoto ni recursos externos.
La configuración OIDC/MFA permanece intacta. Despliegue y backups: `deployment.md`.
Referencias: https://reactflow.dev/learn,
https://www.postgresql.org/docs/17/ddl-rowsecurity.html.

## Organización en carpetas

`diagram_folders` almacena propietario, nombre, revisión y fecha. Cada mapa puede
pertenecer a una carpeta mediante una FK nullable; la eliminación de una carpeta
establece esa FK en NULL y conserva el documento. Las carpetas no cambian los
permisos de los mapas: ambos continúan privados para el sujeto OIDC.

La biblioteca muestra carpetas y mapas sin clasificar en la raíz. El filtro permite
abrir una carpeta, Todos los diagramas o Sin carpeta. La selección se limita a la
página visible y permite mover varios mapas con una única transacción. El servidor
bloquea las filas, verifica dueño/revisión y destino, y aplica todos los movimientos
o ninguno. Los mapas nuevos dentro de una carpeta heredan esa ubicación.
