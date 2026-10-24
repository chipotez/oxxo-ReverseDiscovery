# Desarrollo aislado, despliegue y rollback

## Estado de esta fase

El contenedor rootless `koodaria-public-home-v1-review` vive en `yard-hostinger`, usuario `mip`, con red `none`, sin `-p`, sin volúmenes, sin capacidades y con filesystem de solo lectura. Imagen `localhost/koodaria-public-home:v1-dev-review`. Contexto en `/home/mip/apps/koodaria-dev/public-home-v1-review`. No está conectado con los servicios existentes. La primera revisión `koodaria-public-home-v1-dev` se conserva detenida, con su imagen, como punto de rollback. Solo se detuvo este contenedor creado durante la tarea; no se detuvo ninguno de los cinco contenedores previos. El proceso tiene reinicio `on-failure:3`, límites de 128 MiB / 64 procesos y logs de hasta 10 MB. No se instala un servicio de arranque para este experimento.

No hay URL pública de desarrollo. La URL de revisión local es `http://127.0.0.1:4173`, ejecutando `python3 scripts/serve.py` en el Mac. La dirección `127.0.0.1:8080` dentro del contenedor solo sirve para sus propias comprobaciones; no es un puerto publicado del VPS.

## Construcción reproducible

Desde la raíz del checkout:

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
```

En el VPS, como `mip`, copiar `dist/`, `infra/Containerfile` e `infra/Caddyfile` a un directorio nuevo dedicado. El build solo incluye esos archivos según `.containerignore` (no copiar el ZIP, Git, archivos de QA o credenciales). El perfil actual requiere que esté disponible esta imagen base exacta:

```text
sha256:5e2c5b4f65129fb9467fd15a9754d93cdede8590b79a1b5e9f35a5008b91dff8
```

```sh
podman build --format docker --pull=never -f infra/Containerfile \
  -t localhost/koodaria-public-home:v1-dev-review .
```

`--format docker` conserva HEALTHCHECK en la imagen (OCI lo descarta). No usar `latest` ni actualizar implícitamente la base. Para otro host, exportar/importar la base exacta con `podman save`/`podman load` y comprobar ID, o proporcionar una base compatible mediante `--build-arg BASE_IMAGE=...` y volver a validarla. La receta no depende de que un registro público conserve una etiqueta mutable. Este perfil no sustituye una receta independiente de reconstrucción del runtime de seguridad, que pertenece a la administración del VPS.

Para una instancia nueva, `sh infra/dev-start.sh` desde la raíz, como propietario de Podman. Rechaza un contenedor del mismo nombre y no elimina recursos. Si el contexto remoto solo contiene los tres archivos de build, usar el equivalente:

```sh
podman run -d --name koodaria-public-home-v1-review --network none \
  --read-only --cap-drop all --security-opt no-new-privileges \
  --memory 128m --pids-limit 64 --restart on-failure:3 \
  --log-opt max-size=10mb --label app=koodaria \
  --label environment=development --label phase=public-home-v1 \
  localhost/koodaria-public-home:v1-dev-review
```

## Verificación, logs, parada y reanudación

```sh
podman healthcheck run koodaria-public-home-v1-review
podman inspect --format '{{.State.Health.Status}}' koodaria-public-home-v1-review
podman exec koodaria-public-home-v1-review curl -fsSI http://127.0.0.1:8080/
podman exec koodaria-public-home-v1-review curl -fsS http://127.0.0.1:8080/healthz
podman port koodaria-public-home-v1-review
podman logs --tail 30 koodaria-public-home-v1-review
podman stop koodaria-public-home-v1-review
podman start koodaria-public-home-v1-review
```

`podman port` debe devolver salida vacía. Los accesos y errores salen a stdout/stderr; no se crean volúmenes. No usar comandos globales `prune`, `stop --all` o `rm --all`.

## Rollback

Para retirar esta fase del servidor, detener únicamente `koodaria-public-home-v1-review`. El contenedor, imagen y contexto quedan retenidos; los cinco servicios anteriores no necesitan restauración porque no se modificaron.

Para probar una revisión posterior, construir otra etiqueta por commit y crear otro nombre dedicado, conservando la instancia previa. Cambiar la instancia activa solo después de pruebas. Si falla, detener la nueva y reanudar la anterior. En Git, volver al commit de aplicación anterior en otro checkout; no hacer reset destructivo sobre archivos del usuario.

## Publicación del dominio — completada

El usuario autorizó después de Fase 1 publicar por IP y configurar dominio/HTTPS. Tras su cambio manual del DNS, se activó **https://koodaria.com** en el Caddy existente. Los certificados de dominio y `www` fueron emitidos por Let’s Encrypt y están administrados por Caddy. No fue necesario utilizar un token de Hostinger. Ver `publication.md` para estado, integración aplicada y rollback del gateway.

Dado que esta fase produce archivos estáticos, la integración aplicada incorpora `dist/` en `/srv/koodaria` de una nueva revisión de la imagen del gateway existente. No requiere otra red ni backend. El virtual host de dominio mantendrá TLS y controles de entrada en ese mismo proxy. Para futuros servicios dinámicos, una red dedicada puede conectar únicamente el backend con ese gateway. No publicar directamente el puerto 8080 del nuevo contenedor. Para operación permanente, preparar su propio Quadlet rootless y probar arranque/rollback antes de promoverlo. No copiar definiciones del laboratorio ni reutilizar sus volúmenes.

## Aplicación de bienvenida

- Fuente: `app/`; imagen `localhost/koodaria-workspace:diagrams-postgres-20261023`.
- Construcción reproducible con `app/requirements.lock`; rangos de mantenimiento
  en `app/requirements.txt`. Gunicorn escucha solo dentro de la red de Podman.
- Unidad: `infra/koodaria-workspace.container`; montada en systemd de mip.
- Entorno privado: `/home/mip/.config/koodaria/workspace.env`, permisos 600.
  Copia local ignorada: `.secrets/koodaria-workspace.env`. No incorporar al build.
- Volumen privado: `koodaria-workspace-sessions`. Conserva sesiones entre reinicios.
  Para retirar una sesión local se requiere invalidarla, no solo borrar su cookie.
- Proxy: `infra/edge/koodaria-welcome.caddy` sustituye el bloque de koodaria.com,
  conservando todos los demás dominios y volúmenes de Caddy.
- Gateway requiere `NetworkAlias=login.koodaria.com` en `themike-auth.network`.
- Pruebas de servidor: `SESSION_DIR=/tmp/koodaria-tests python -m unittest test_server -v`
  dentro del contenedor; nunca apuntar las pruebas al almacén real de sesiones.
- Rollback: restaurar la unidad y Caddyfile de
  `/home/mip/backups/koodaria-20261023/welcome-edge/` y reiniciar el gateway con
  la imagen anterior `localhost/themike-site:koodaria-identity-20261023`.
  La base previa está en `before-welcome.dump`, pero no restaurarla sobre cambios
  posteriores sin revisión. El cliente nuevo puede deshabilitarse independientemente.

## Compilación del editor React Flow

La imagen de la aplicación compila `app/frontend/` con Node 22, `npm ci` y
esbuild; copia solamente los bundles finales al runtime Python. No se necesita
Node en producción durante la ejecución. Los bundles generados están ignorados
en Git y la imagen los reconstruye a partir del lock. La QA actual de React Flow usa `scripts/qa_diagrams_online.py`, contra una
instancia de prueba y PostgreSQL desechable accesibles solo a través de SSH. No
requiere inyectar identidades en producción ni usa la cuenta real del usuario.

## Diagramas de recursos en PostgreSQL

La herramienta usa `/bienvenida/api/diagrams` detrás de la misma sesión OIDC.
La tarjeta abre **Mis diagramas**; cada mapa se crea con UUID, nombre y revisión.
El editor guarda automáticamente y permite exportar únicamente PDF. El antiguo
formato JSON local ya no es el mecanismo de guardado de Mapeo de recursos.

- PostgreSQL 17 dedicado: `koodaria-diagrams-db`, imagen fijada por digest en
  `infra/koodaria-diagrams-db.container`; volumen `koodaria-diagrams-data`.
- Red interna `koodaria-data`, sin puertos publicados. Solo el backend se conecta
  tanto a esta red como al gateway. No reutiliza la base ni los usuarios de Keycloak.
- Entornos privados (600): `diagrams-db.env` y `diagrams-app.env`, dentro de
  `/home/mip/.config/koodaria/`. No copiarlos al repositorio ni a imágenes.
- Migración inicial: `app/migrations/001_resource_diagrams.sql`, ejecutada como
  propietario de la base. El rol web `koodaria_app` no es superusuario y solo
  tiene permisos CRUD; RLS forzado aplica la identidad OIDC en cada transacción.
- Cada diagrama es privado para su usuario. No hay compartición implícita por
  correo/dominio ni entre miembros de una organización.
- Las escrituras exigen CSRF y revisión vigente. Un conflicto devuelve 409;
  el navegador conserva sus cambios y ofrece guardar una copia.
- Datos: máximo 200 recursos/500 conexiones por mapa, validación del modelo en
  servidor, sin ejecución de HTML ni carga de URLs desde el documento.
- Los fallos de guardado se muestran; no se anuncian como guardados. Al salir con
  cambios pendientes se avisa. No hay edición offline persistente.
- Backup diario UTC: `koodaria-diagrams-backup.timer`, 14 dumps recientes con
  permisos privados en `/home/mip/backups/koodaria-diagrams/`. Son copias locales
  al VPS; una copia externa de recuperación requiere otro destino.
- Restauración: detener solo la aplicación, conservar dump previo, restaurar un
  dump verificado con `pg_restore` como propietario en una base nueva y comprobar
  RLS/permisos antes de cambiar la conexión privada. Nunca restaurar sobre la base
  de identidad. Conservar el volumen al hacer rollback de la aplicación.
- QA: base separada `koodaria_diagrams_qa`, cuentas sintéticas; ejecutar
  `test_server` y `test_diagrams` con `DIAGRAM_TEST_DATABASE=disposable` y URL
  que termine en esa base. El arnés de navegador solo vive en un contenedor de
  prueba enlazado a loopback; su ruta sintética no forma parte de la imagen.

Publicación del almacenamiento online: 23 de octubre de 2026. Imagen verificada
`e8322c5d04daf3aa515263d79ee948c283684f294bf155527b622438bd2355f7`.
Unidad previa para rollback:
`/home/mip/backups/koodaria-20261023/diagrams-online/koodaria-workspace.container`.
Restaurar solo esa unidad y reiniciar `koodaria-workspace.service` revierte la UI;
no borrar el volumen PostgreSQL ni restaurar un dump anterior sobre mapas nuevos.
El gateway y Keycloak no se reconstruyeron ni reiniciaron en este cambio.

## Recuperación de sesión en herramientas

La sesión local tiene un límite de 2 horas durante las pruebas; una pestaña abierta no equivale
por sí sola a una sesión válida. Si la API responde 401 y no hay cambios pendientes,
la herramienta inicia OIDC con un destino local validado y vuelve a Mapeo de recursos.
Si hay cambios pendientes, mantiene el editor abierto y ofrece acceso en otra pestaña.
Al continuar, `/auth/session` comprueba vigencia, renueva el CSRF del cliente y exige
la misma identidad que abrió el editor antes de reintentar el guardado. Un 403 por
rotación de CSRF permite un único reintento con una sesión verificada. La recuperación respeta el vencimiento absoluto de la sesión y no modifica MFA.

Imagen: `localhost/koodaria-workspace:session-recovery-20261023`.
Rollback de unidad en `/home/mip/backups/koodaria-20261023/session-recovery/`.
Pruebas: 17 pruebas de servidor contra base desechable, más
`scripts/qa_session_recovery.py` (respuestas sintéticas en el navegador).

## Carpetas de diagramas

Imagen actual: `localhost/koodaria-workspace:folders-20261023`.
Migración aditiva `app/migrations/002_diagram_folders.sql`: crea carpetas privadas,
añade `folder_id` nullable y mantiene intactos los documentos existentes. Ejecutar
como propietario en la base de aplicación antes de promover esta imagen; también
en la base desechable antes de QA. La versión anterior es compatible con la columna
nueva, por lo que un rollback de la aplicación no requiere revertir la migración.

- Raíz: carpetas y diagramas sin clasificar, con paginación adaptable al viewport.
- Ubicaciones: Todos los diagramas, Sin carpeta o una carpeta concreta.
- Un nivel de carpetas; hasta 200 por cuenta, nombres únicos sin distinguir mayúsculas.
- Nueva carpeta, renombrar, mover un mapa o una selección de la página.
- El movimiento de varios mapas es atómico y comprueba sus revisiones.
- Eliminar una carpeta conserva sus diagramas en Sin carpeta.
- RLS forzado y verificación de propietario también para carpetas/asignaciones;
  las cuentas no pueden utilizar carpetas ajenas aunque conozcan su UUID.
- Backups de la base incluyen carpetas y relaciones automáticamente.
- QA: `scripts/qa_diagram_folders.py`, con arnés desechable y base de prueba.

Carpetas publicadas el 23 de octubre de 2026; imagen
`122be568878bdd87de70edb8ffe10f189e63310dd60922d80bd7b9b552509775`.
Unidad previa en `/home/mip/backups/koodaria-20261023/folders/`.
No revertir la migración al hacer rollback de UI: conservar carpetas y relaciones.

## Sesión de pruebas de dos horas

Imagen actual: `localhost/koodaria-workspace:session-2h-20261023`.
La aplicación fija 7200 segundos desde el login, sin prórroga por actividad. La
cookie autenticada es persistente, Secure, HttpOnly y SameSite=Lax. Las sesiones
vigentes de la política anterior se actualizan una sola vez, conservando su hora
original de autenticación; las vencidas no se reactivan. Para sesiones nuevas se
marca explícitamente la persistencia después de regenerar la sesión de login.

Se conserva el volumen `koodaria-workspace-sessions` y la clave privada existente
entre despliegues. El cierre manual invalida la sesión. No se aumentó la duración
del access token de Keycloak ni se modificaron MFA o el realm del laboratorio.
Verificación: 21 pruebas de servidor y `scripts/qa_session_durability.py`, que
recrea dos contenedores aislados con la misma cookie/volumen sintéticos.

## Biblioteca compartida e invitaciones — 23 de octubre de 2026

Imagen desplegada: `localhost/koodaria-workspace:sharing-20261023`, ID
`a7f53474fde57e708a8d9b6a0459436cde3fb495ba3dc7db20f1fe744756043f`.
Migración aditiva `003_diagram_sharing.sql`, aplicada una vez como propietario tras
backup. Conserva los propietarios existentes como miembros; identidades nuevas
entran como invitados. La aplicación no puede elevar ese nivel. PostgreSQL aplica
RLS a grupos, documentos, directorio de identidades y accesos compartidos.

- Mis diagramas / Compartidos conmigo; Nuevo grupo, filtros y selección compactos,
  iconos de colección/topología, acciones secundarias en menú y bordes suaves.
- Un invitado puede leer, editar y exportar PDF exclusivamente de los mapas con
  una concesión activa. No crea, elimina, mueve, agrupa ni vuelve a compartir.
- Las invitaciones pendientes se activan tras OIDC, con sujeto y correo verificado
  coincidentes. Nunca se concede acceso por dominio ni por organización solamente.
- Revocación inmediata para nuevas lecturas y escrituras; edición con revisión
  optimista y registro de acciones. Límite 10 invitaciones/minuto por propietario,
  60 segundos entre reenvíos y 100 personas por mapa. Invitación pendiente: siete
  días; enlace de alta de Keycloak: 24 horas. Una entrega fallida no activa acceso.

`/home/mip/.config/koodaria/invitation-service.env` contiene SMTP y el secreto del
cliente `koodaria-invitations`, con permisos 600 y fuera de imágenes/Git. El cliente
es de servicio, sin login interactivo ni grant de contraseña; sus roles son
manage-users, query-users, view-users, manage-organizations y query-organizations
solo en el realm Koodaria. No tiene realm-admin ni permisos de master.

SMTP global autenticado con el buzón `admin@koodaria.com`, independiente de las
organizaciones. `SMTP_VERIFIED=true` se añadió después de verificar TLS/autenticación.
Un alias futuro `no-reply@koodaria.com` solo cambia el remitente después de crearlo y
validar envío; no sustituye el usuario de autenticación ni exige otra organización.
La organización Koodaria corresponde a la cuenta propietaria de la aplicación.
Las cuentas nuevas invitadas se incorporan a la organización explícita del propietario;
si no hay exactamente una, la invitación falla antes de crear la cuenta.

Alta: correo verificado, perfil, contraseña, TOTP y códigos de recuperación. Reenviar
un alta pendiente conserva los pasos restantes. Compartir con cuentas existentes
no cambia sus contraseñas ni su MFA. La recuperación por correo restablece únicamente
la contraseña; se deshabilitó reset-otp en el flujo de recuperación. Para pérdida del
segundo factor se usa un código de recuperación previamente guardado o asistencia
administrativa con comprobación de identidad. No hay bypass de MFA por email.

El segundo factor tiene un subflujo OTP REQUIRED dentro de una alternativa, junto a
Recovery Authentication Code. Así los usuarios sin OTP pueden matricularlo y los ya
configurados pueden usar un código válido de recuperación. Se comprobó en un realm
desechable: configuración inicial, siguiente login con OTP, recuperación y rechazo
al reutilizar el mismo código. No se eliminaron credenciales MFA humanas.

El tema de correo propio usa el logo textual y verdes de Koodaria. La configuración
de códigos de recuperación presenta instrucciones, códigos paginados y confirmación
nativa en pasos; no recorta ni escala el formulario. Los códigos/QR no forman parte
de capturas ni evidencias. Los correos de prueba se dirigieron solo al buzón propio;
la identidad desechable de la invitación y su enlace se invalidaron tras la prueba.

Validación: 30 pruebas de servidor, PostgreSQL desechable y pruebas de navegador en
16 estados (ocho viewports, dos temas), siete auditorías WCAG AA sin incidencias,
edición/revocación real entre propietario e invitado. Evidencia:
`docs/evidence/sharing-workspace-report.json` y `recovery-enrollment-report.json`.
Sesiones de dos horas, clave de aplicación y volumen de sesiones conservados.
Rollback UI: unidad previa en `/home/mip/backups/koodaria-20261023/sharing/`.
No revertir la migración ni borrar concesiones/datos al revertir una imagen.

## Ajustes visuales de MFA — 24 de octubre de 2026

El tema agrega `auth-polish-v1.css` y dos SVG locales: traducción y cambio de
cuenta. El campo OTP usa un solo borde continuo de 2 px para el foco, sin outline
ni sombra duplicados; el resto de controles conserva su foco de teclado. Código
centrado, números monoespaciados, teclado numérico móvil y etiqueta «Código de
verificación» / «Verification code». El selector de idioma conserva su menú nativo
con nombre accesible; cambiar de cuenta conserva el enlace nativo de Keycloak.

Solo presentación y mensajes: no cambia validación, credenciales, flujo MFA ni
sesiones. Copia previa del manifiesto y mensajes en
`/home/mip/backups/koodaria-20261024/otp-polish/`. Se reinició únicamente Keycloak
para invalidar la caché del tema. QA de la presentación OTP con markup nativo
reconstruido y usuario sintético, usando el shell público real: ocho viewports por
cada preferencia de color, foco único y botones visibles, sin scroll. No se usó
la cuenta real ni se capturaron códigos. Ver `otp-polish-report.json`. La pantalla
de login y los recursos publicados se verificaron también por HTTPS.

## Diagramas unificados — 24 de octubre de 2026

Release `localhost/koodaria-workspace:unified-diagrams-20261024`. No requiere
migración de esquema ni cambios en Keycloak, SMTP, Caddy o sesiones.

El catálogo de Observabilidad tiene una sola herramienta, Diagramas. La ruta
canónica es `/bienvenida/#/herramientas/diagramas`; los enlaces anteriores a
Mapeo de recursos, servicios y dependencias abren la misma biblioteca online.
Se retira el editor local de servicios de las rutas y del JavaScript servido.
Los diagramas ya almacenados, grupos, revisiones y concesiones siguen en sus
mismas tablas e identificadores. No se convierte ningún archivo JSON descargado
anteriormente por el editor local.

`app/frontend/src/diagram-catalog.json` es el catálogo compartido por UI y backend:
23 tipos de recurso en cinco categorías y cinco plantillas (en blanco,
infraestructura, servicio de negocio, dependencias y clúster Oracle). El build
copia el mismo JSON a la imagen Python. `diagram_catalog.py` genera identificadores
nuevos por instancia y el servidor valida y guarda todo el documento en una única
transacción durante POST, usando un `template_id` permitido. No acepta rutas de
plantillas ni contenido externo. Elegir una plantilla no limita la edición posterior.

Añadir abre un panel flotante izquierdo con categorías, búsqueda y paginación
según el espacio disponible. Clic/tap inserta un nodo con nombre editable; en
pantallas pequeñas se cierra el panel para dejar el lienzo visible. El arrastre
nativo de escritorio convierte coordenadas de pantalla a coordenadas React Flow,
respetando el zoom. En dispositivos táctiles se usa la alternativa de toque.
Notas y etiquetas usan los mismos documentos validados; los grupos visuales
conservan contención padre/hijo. La exportación sigue siendo PDF, con las etiquetas
del mismo catálogo para todos los tipos nuevos.

Se mantienen RLS, revisión optimista, CSRF, límites de documentos, invitaciones y
permisos de invitados. Un invitado puede añadir recursos al documento concedido,
pero no crear un diagrama, ni siquiera mediante POST directo con una plantilla.

QA: 33 pruebas de servidor; `scripts/qa_unified_diagrams.py` comprueba plantillas
persistidas/reabiertas/PDF, enlaces antiguos, arrastre, toque, edición de invitado
y bloqueo de creación. Verifica dimensiones reales de documento, diálogo y panel
en ocho viewports y dos temas, además del paso de nombre y resultados de búsqueda.
Evidencia en `docs/evidence/unified-diagrams-report.json`. Sustituye las pruebas
históricas del editor local (`qa_catalog_functional.py` / `qa_resource_flow.py`).

Backup de unidad previa: `/home/mip/backups/koodaria-20261024/unified-diagrams/`.
Se guarda un dump antes de promover la imagen. Conservar el volumen de sesiones
además de PostgreSQL y las claves privadas existentes. Un rollback a imágenes
anteriores no entiende todos los tipos nuevos de recurso; después de guardar
tipos nuevos, preferir una corrección compatible hacia adelante. Nunca restaurar
un dump antiguo encima de diagramas nuevos para revertir la interfaz.

Imagen publicada y verificada:
`f07506dff72673844d918f0d5a56b11f785963e2eb5aa4823bb7ea35f9d789a1`.
Resultado: 33 pruebas de servidor, 56 estados responsive, ocho auditorías WCAG AA
sin incidencias y vista previa del clúster dentro de sus límites. Se compararon
los hashes públicos de JavaScript/CSS con los archivos del contenedor activo.

## Estándares operativos — 24 de octubre de 2026

Imagen `localhost/koodaria-workspace:standards-20261024`. Aplicar una vez la
migración aditiva `004_resource_standards.sql` como propietario, primero en QA y
luego en producción, tras backup. Crea borradores y versiones publicadas, sin
alterar diagramas existentes. Las publicaciones tienen permiso SELECT/INSERT
para la aplicación y carecen de UPDATE/DELETE. Ambas tablas fuerzan RLS.

API privada `/bienvenida/api/standards`: sesión y CSRF, acceso solo a miembros,
propiedad por sujeto OIDC y límites de 200 definiciones / 100 versiones por
definición. El API no ofrece borrar publicaciones. Los nodos pueden referirse a
una publicación propia o a una copia ya presente en el diagrama autorizado;
ningún sujeto puede obtener un catálogo ajeno mediante esa referencia.

La incorporación de nodos pasa por la validación de documentos existente. Los
estados admitidos son Sin verificar, Configurado, Pendiente y No aplica; la fuente
se fija en `declared` y el servidor registra fecha de cambio. El verde significa
una declaración de configuración, no una comprobación técnica del agente.
No se modifican el realm, SMTP, Caddy, contraseñas ni la política de sesión de 2h.

El contenedor debe conservar las mismas claves privadas y el volumen de sesiones.
Los backups habituales de PostgreSQL incluyen las tablas nuevas automáticamente.
No restaurar datos antiguos para revertir la interfaz. Una imagen anterior a esta
función desconoce las referencias de estándares; después de guardar cobertura,
preferir una corrección compatible hacia adelante en lugar de una imagen que
pueda descartar metadatos al editar.

QA: `test_standards` junto con servidor, diagramas e invitaciones en la base
`koodaria_diagrams_qa`; `scripts/qa_resource_standards.py` prueba el flujo real de
borrador, publicación, inserción, cobertura manual, actualización explícita y
adaptación de formularios en ocho viewports y ambos temas. Las identidades y
evidencias de QA son sintéticas; no se envían correos ni se usa MFA de personas.

Publicado y verificado con imagen
`d07e143d0415024573c1f1412b485b31f24ad4689b0ea222adf03ae3f70634b4`.
38 pruebas de servidor, 144 estados responsive y ocho auditorías WCAG AA sin
incidencias. Se probó además que un invitado puede reutilizar una definición ya
copiada en su diagrama compartido, conservando el bloqueo del catálogo privado.
JavaScript/CSS públicos coinciden con el contenedor desplegado; ambos API privados
responden 401 sin sesión. Unidad anterior en
`/home/mip/backups/koodaria-20261024/resource-standards/`.

## Subsección Diagramas — 24 de octubre de 2026

Publicada `localhost/koodaria-workspace:diagrams-hub-20261024`
(`b0af36ffdc464abba3f48fb0655b4126ca7072212918a493e27b4abe3fa3c60b`).
Observabilidad → Diagramas abre dos tarjetas: Estándares y Diagramas.
Ambas vistas regresan a esta subsección; los invitados mantienen bloqueado
el catálogo privado de estándares. Sin cambios de esquema ni de sesiones.
Verificación: navegación, restricciones de invitado, 16 estados responsive
y auditorías WCAG AA; evidencia en `evidence/diagrams-hub-report.json`.
Los assets públicos coinciden con el contenedor. Unidad anterior respaldada en
`/home/mip/backups/koodaria-20261024/diagrams-hub/`.

## Gobierno en Observabilidad — 24 de octubre de 2026

Imagen `localhost/koodaria-workspace:governance-hub-20261024`
(`133fb26053c193abc8dc5c5064be0eb5c72fd9bc11473517e191303e9f79bb92`).
La sección Gobierno reúne Estándares, Diagramas y Blueprints. El catálogo
de Blueprints está identificado como en preparación; no implementa CRUD.
La ruta anterior de la subsección Diagramas redirige a Gobierno.
Permisos de invitados sin cambios. Navegación, retornos, Blueprints y 16 estados
responsive verificados; evidencia `evidence/governance-hub-report.json`.

## Catálogo de infraestructura y salida de edición — 24 de octubre de 2026

Imagen `localhost/koodaria-workspace:infrastructure-catalog-20261024`
(`8c5ccbf87e59fe9d08de33f98e9417c8a02d3e0dd72281c24997bcf9aa4bbdb2`).
Estándares → Infraestructura incorpora ocho categorías, subcategorías y tipos
de recurso paginados. Las definiciones editables existentes se conservan bajo
Cómputo → Servidores; los otros tipos identifican su definición operativa como
en preparación. No hay migración de base de datos ni nuevas autorizaciones.

Salir de una definición con cambios abre un diálogo Koodaria con Seguir editando,
Salir sin guardar y Guardar y salir, tanto en la flecha de retorno como al
cambiar de sección. Un fallo al guardar mantiene abierto el diálogo y conserva
los cambios. Cerrar o recargar la pestaña conserva la protección nativa del navegador.

Verificados 96 estados responsive, ocho auditorías WCAG AA y todos los niveles
del catálogo con cuentas sintéticas. Evidencias: `infrastructure-catalog-report.json`
y `infrastructure-accessibility-report.json` en `docs/evidence/`; script
`scripts/qa_infrastructure_catalog.py` usa el harness descartable en localhost.
Unidad anterior respaldada en `/home/mip/backups/koodaria-20261024/infrastructure-catalog/`.

## Modelo de servidor — 24 de octubre de 2026

Imagen `localhost/koodaria-workspace:server-model-20261024`
(`e71c9a3bb30a679e050bfdb6adc8b1a1c6849dd708daee5ec0c2ec4f52986e40`).
Servidores abre cuatro bloques: Identificación de entidad, Capacidades y
controles, Evidencia operativa y Relaciones de arquitectura. Criterios incluye
las reglas de interpretación del modelo. Definiciones conserva las bases y
publicaciones Linux/Windows. Estructura edita la exigencia y regla esperada
de 17 campos; Requisitos admite controles Condicionales y su condición.

El nuevo `server_model` es opcional en el JSONB del borrador/publicación.
La validación exige todos los campos conocidos, sin duplicados, y límites de
longitud. Los clientes antiguos que omiten el modelo o la condición no borran
esos datos. Las publicaciones históricas no se reescriben; el diagrama conserva
la versión y copia canónica del estándar que ya usa. No se registran valores
observados ni se afirma cumplimiento por completar el estándar.
Sin migración SQL ni cambios de permisos, identidad o duración de sesión.

40 pruebas de servidor y 256 estados responsive, con cuatro auditorías WCAG AA.
Evidencia: `docs/evidence/server-model-report.json`; script
`scripts/qa_server_model.py`. Se comprobó guardar, publicar, reabrir, conservar
versiones anteriores y usar el modelo en la copia del estándar dentro del diagrama.
Backup de la base completado antes de publicar. Unidad anterior en
`/home/mip/backups/koodaria-20261024/server-model/`. Assets públicos verificados
contra el contenedor; el API de estándares sigue respondiendo 401 sin sesión.

## Tablas de referencia del servidor — 24 de octubre de 2026

Publicada `localhost/koodaria-workspace:reference-tables-20261024`
(`15da79270c12bba806b30045e0893fc54aa9097e2f568f96d21646ff06271359`).
Los cuatro bloques de referencia muestran tablas con nombre, explicación y
formato, con paginación según el viewport y adaptación móvil. Agregar campo
abre un formulario de vista previa en memoria; no persiste ni modifica
definiciones, publicaciones o la base de datos. Los campos temporales se
descartan al salir de la vista y la interfaz lo indica.
72 estados responsive y ocho auditorías WCAG AA en el preview local; comprobadas
la validación de duplicados y ausencia de escrituras API. Evidencia en
`docs/evidence/reference-tables-report.json`. Assets públicos coinciden con
el contenedor y API privado conserva 401 sin sesión. Sin migración SQL.
Unidad anterior en `/home/mip/backups/koodaria-20261024/reference-tables/`.

## Navegación de estándares en dos paneles — 24 de octubre de 2026

Imagen `localhost/koodaria-workspace:standards-split-20261024`
(`f78eebb9ba0aae6314d1a285bddb39f91a5a3ef35779831c577cc2bf885aa7b7`).
Estándares abre directamente Infraestructura: selector a la izquierda y
categorías/subcategorías a la derecha. En móvil se apilan. Las vistas de
recurso y tablas conservan el ancho completo. No se añadieron dominios nuevos
ni se cambiaron datos, permisos o la persistencia temporal de Agregar campo.
48 estados responsive del navegador de categorías, 72 de las tablas y diez
auditorías WCAG AA. Evidencia `docs/evidence/standards-split-report.json`.
Assets públicos coinciden con el contenedor. Unidad anterior en
`/home/mip/backups/koodaria-20261024/standards-split/`.

## Árbol de navegación de estándares — 24 de octubre de 2026

Imagen `localhost/koodaria-workspace:standards-tree-20261024`
(`986a0a843cafa83d42d757dc8dc796d7095f6daccbceaaa39af72e07771cedf1`).
El panel izquierdo conserva Infraestructura → categoría → subcategoría y,
en Servidores, sus cuatro bloques, Definiciones y Criterios. Los ancestros se
expanden al navegar; las flechas contraen sin cambiar el contenido y cada
etiqueta permite saltar directamente a ese nivel. El panel se mantiene en las
tablas y al editar; los cambios sin guardar mantienen el diálogo de protección.
Las opciones del panel derecho son compactas y la paginación usa su tamaño real.
En móvil, un botón en la cabecera abre la misma navegación en un diálogo, con
cierre por Escape, retorno del foco y acceso a Gobierno.

Verificados 80 estados del árbol, 72 de tablas y 80 del editor; doce auditorías
WCAG AA en total. Fixtures locales sintéticas, sin modificar datos de usuarios.
Evidencia `docs/evidence/standards-tree-report.json`. Sin cambios de base de
datos, permisos, catálogo ni persistencia de campos temporales. Unidad anterior
en `/home/mip/backups/koodaria-20261024/standards-tree/`.

## Retirar accesos de Definiciones y Criterios — 24 de octubre de 2026

Publicada `localhost/koodaria-workspace:standards-four-blocks-20261024`
(`ad7f9c262823f8abfd10fd2cc0f0cdcc2899c3cce39825b9634e1a101f99cfb2`).
Se quitaron los dos accesos del árbol y de la cabecera. Permanecen los cuatro
bloques de Servidores. Sin borrar estándares, versiones ni datos. Compilación
y navegación verificadas en escritorio y móvil; bundle público coincide con
el contenedor. Unidad anterior en
`/home/mip/backups/koodaria-20261024/standards-four-blocks/`.

## Catálogo compartido de componentes — 24 de octubre de 2026

Publicada `localhost/koodaria-workspace:component-catalog-20261024`
(`7b9d28466fd147d36209ee37cdf2f39e4fb40c1f6c1379e76a665d7e0666d690`).
El inicio del workspace muestra «Tu espacio de trabajo», tarjetas compactas y
un icono por área. Estándares y el editor comparten 12 categorías y 110 tipos
de componentes desde `component-catalog.json`. Proveedor y tecnología son
atributos y filtros; no crean copias del tipo de recurso. Cada tipo ofrece
cuatro bloques de referencia. Se conservan los estándares publicados de
servidores y permanecen ocultos los accesos Definiciones y Criterios.

Los nodos guardan proveedor, tecnología y ubicación en el documento existente.
Clientes anteriores que omiten esos campos conservan sus valores. No hubo
migración SQL ni modificación de permisos. Agregar campos sigue siendo una
vista previa temporal; las referencias de otros tipos no se presentan como
políticas publicadas.

Validación: 42 pruebas de servidor, 144 estados responsive, seis auditorías
WCAG AA y guardado real con datos sintéticos en la base QA. Assets públicos
comparados con el contenedor y APIs sin sesión responden 401. Evidencia:
`docs/evidence/component-catalog-report.json`. Backup de base completado antes
del reinicio y unidad anterior en
`/home/mip/backups/koodaria-20261024/component-catalog/`.

Para revertir después de utilizar tipos nuevos, conservar un catálogo compatible:
las versiones anteriores no reconocen esos identificadores al editar. No
restaurar la base de datos sobre cambios posteriores de los usuarios.

## Navegación compacta de recursos — 24 de octubre de 2026

Publicada `localhost/koodaria-workspace:catalog-tree-20261024`
(`25149ad1f1f6721231aee3699038d9d2cedcc99b126285681fd88a094508a8d2`).
La paginación de estándares mide tarjetas, espacios y filtros renderizados,
sin el límite anterior de cuatro filas. La biblioteca del editor muestra
categorías y subcategorías desplegables en lista, con búsqueda, arrastre y
paginación según la altura del panel. Servidores conservan la selección de
su estándar publicado.

Persona reúne identidad corporativa, correo, roles, organización y estado.
Origen y Rol dejan de ofrecerse en los catálogos nuevos; sus identificadores
siguen siendo compatibles con diagramas guardados. Sin migración ni borrado
de datos. Validación: 42 pruebas de servidor, 144 estados responsive, seis
auditorías AA y comprobación específica de llenado de pantalla, Persona y
árbol de recursos (`scripts/qa_catalog_navigation.py`). Backup previo y unidad
anterior en `/home/mip/backups/koodaria-20261024/catalog-tree/`.

## Instancias de servidor con cuatro bloques — 24 de octubre de 2026

Imagen `localhost/koodaria-workspace:server-instances-20261024`
(`ea74ddd8ae2483046b27624137489b99b135d78f43751ffbd76c5b7d3361e618`).
Servidor físico y Máquina virtual se insertan directamente con los cuatro
bloques de Estándares. «Ver campos» muestra las etiquetas y valores dentro
del nodo; cada cabecera abre captura por campo, con instrucciones y paginación.
Controles conservan sus estados declarados, sin presentarse como verificados.

`resource_schema` es asignado por el servidor desde el modelo compartido;
los valores son `server_instance` en el documento PostgreSQL JSONB. El backend
valida secciones, identificadores, estados y límites, ignora esquemas enviados
por el cliente y conserva los valores omitidos por clientes anteriores.
Una única publicación compatible se vincula automáticamente; sin ella se usa
la estructura base, sin atribuirle una política publicada. Una publicación
puede seleccionarse en Propiedades. No hubo migración SQL ni cambios de
identidad, sesiones o permisos.

Validación: 43 pruebas de servidor y 64 estados de captura de los cuatro
bloques, en dos temas y ocho tamaños. Reapertura y guardado online con datos
sintéticos en la base QA. Evidencia `docs/evidence/server-instances-report.json`.
Backup previo y unidad anterior en
`/home/mip/backups/koodaria-20261024/server-instances/`.

## Fila de iconos del estándar — 24 de octubre de 2026

Publicada `localhost/koodaria-workspace:server-icon-row-20261024`
(`2385b23b5721c194ddebf705c9a7de96a933817a168eda86dc5e4d5dffc97531`).
Los cuatro bloques del nodo se sustituyen por una fila horizontal de iconos,
con nombre al pasar el mouse o enfocar por teclado. Cada botón conserva el
acceso al bloque de captura correspondiente. Sin cambios de datos, esquema ni
permisos. Verificados los cuatro accesos en cinco tamaños y ambos temas,
incluidos tooltip y foco; assets públicos comparados con el contenedor.
Evidencia `docs/evidence/server-icon-row-report.json`. Unidad anterior en
`/home/mip/backups/koodaria-20261024/server-icon-row/`.

## Inspector de identidad y conectores cardinales — 24 de octubre de 2026

Publicada `localhost/koodaria-workspace:server-inspector-20261024`
(`f5bd60d70d81baece8d7d53f3317914e5b93ce60f334f7fca7b06902e6f00514`).
Nodo con sombras suaves y fondos minerales en la fila de iconos. Se añaden
conectores norte/sur, guardados como `sourceHandle` y `targetHandle`; la
validación limita sus identificadores y tipos de recurso. Las conexiones
anteriores izquierda/derecha siguen usando los anclajes originales. Guardados
de clientes anteriores conservan los anclajes si omiten sus atributos.

Identificación abre un panel flotante con campos, explicaciones y paginación
según la altura disponible. El encuadre reserva espacio a la izquierda sin
alterar coordenadas del documento. Al cerrar se restaura el encuadre anterior.
Guardado automático, acción Guardar e indicador decorativo «sync» únicamente
en estado guardado; errores y estados pendientes conservan texto legible.
En móviles y vistas bajas el panel aprovecha la altura del viewport.

44 pruebas de servidor, conexión vertical real en navegador con reapertura,
captura y guardado de los siete campos y 16 estados de tamaño/tema. Auditorías
WCAG AA del panel en ambos temas sin infracciones. Assets públicos comparados
con la imagen. Evidencia `docs/evidence/server-inspector-report.json` y script
`scripts/qa_server_inspector.py`. Sin migración SQL ni cambios de permisos.
Backup previo y unidad anterior en
`/home/mip/backups/koodaria-20261024/server-inspector/`.
