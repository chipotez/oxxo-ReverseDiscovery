# Publicación con dominio y HTTPS

Completada el 22 de octubre de 2026, con autorización explícita del usuario.

## Estado actual

- **https://koodaria.com**: Home pública, HTTP 200 y certificado válido de Let’s Encrypt.
- `http://koodaria.com` → HTTPS mediante redirección 308.
- `https://www.koodaria.com` → dominio canónico mediante redirección 301.
- `http://www.koodaria.com` → HTTPS y luego al dominio canónico.
- `http://45.80.153.100` sigue sirviendo la Home como entrada transitoria. La URL recomendada es HTTPS del dominio.
- El laboratorio `themike.io`, su portal y Keycloak siguen funcionando; se comprobaron después del cambio.

El usuario cambió manualmente el registro A en Hostinger. Se verificó la respuesta autoritativa de ambos nameservers y posteriormente la de 1.1.1.1 y 8.8.8.8:

| Tipo | Nombre | Destino |
|---|---|---|
| A | @ | 45.80.153.100 |
| CNAME | www | koodaria.com |

No hay AAAA público observado. No se necesitó un token de Hostinger para esta publicación. El archivo privado reservado para un token futuro se mantiene vacío y excluido de Git, junto con `.env` y `.env.*`.

## Integración y seguridad

Se reutiliza el gateway `themike-site`, ahora con imagen `localhost/themike-site:koodaria-green-palette-20261022`. Su base es el runtime parcheado original, fijado por ID. La Home está en `/srv/koodaria`, separada de la landing del laboratorio en `/srv`. No requiere backend nuevo, redes o puertos adicionales. El contenedor de desarrollo permanece aislado y no forma parte del tráfico de producción.

Los fragmentos de configuración están en `infra/edge/`. Se ensamblaron con el Caddyfile original conservando las rutas del laboratorio. La imagen fue validada antes de actualizar el Quadlet activo y su copia de fuente. Se reinició brevemente el gateway porque su API administrativa está desactivada. Se conservaron volúmenes, identidades, redes, puertos y políticas de reinicio.

Caddy obtuvo certificados públicos separados para `koodaria.com` y `www.koodaria.com` mediante HTTP-01 de Let’s Encrypt. Se verificó confianza de la cadena y coincidencia de hostname sin desactivar validaciones TLS. Caddy gestiona su renovación automática; los certificados se guardan en el volumen persistente ya existente. Los certificados inicialmente emitidos vencen el 20 de enero de 2027; Caddy debe renovarlos antes de esa fecha.

Cabeceras verificadas en HTTPS:

- HSTS: `max-age=31536000`, sin imponerlo a otros subdominios.
- CSP restrictiva, sin scripts inline, terceros, formularios o conexiones externas, con `upgrade-insecure-requests`.
- `X-Content-Type-Options: nosniff` y `X-Frame-Options: DENY`.
- `Referrer-Policy: strict-origin-when-cross-origin`.
- Permissions-Policy deshabilitando cámara, micrófono, ubicación, pagos y USB.
- Ausencia de la cabecera Server en la Home HTTPS.
- Revalidación `no-cache` para assets sin fingerprint.

La renovación automática depende de conservar el DNS correcto, el acceso público a 80/443 y el volumen de datos de Caddy. No requiere renovar manualmente un certificado comprado ni instalar un plugin DNS. Referencia oficial: https://caddyserver.com/docs/automatic-https .

## Reproducir la imagen del gateway

Contexto del VPS: `/home/mip/apps/koodaria-edge-20261022`. Contiene `Containerfile`, `dist/` y el Caddyfile ensamblado `edge.Caddyfile`, que incluye la variante `edge.Caddyfile.with-domain`.

```sh
cd /home/mip/apps/koodaria-edge-20261022
podman build --format docker --pull=never -f Containerfile \
  -t localhost/themike-site:koodaria-https-20261022 .
```

La receta versionada es `infra/edge/Containerfile`; los hosts nuevos están en `koodaria.caddy` y `koodaria-ip.caddy`. No introducir secretos en el contexto. El gateway completo de los otros hosts y sus respaldos permanecen fuera de este repositorio.

## Rollback de HTTPS hacia la revisión por IP

Como administrador, restaurar desde `/root/remediation-20261022/koodaria-publication-https`:

- `Caddyfile.before` → `/home/mip/apps/themike-site/Caddyfile`.
- `quadlet.before` → `/home/mip/.config/containers/systemd/themike-site.container`.
- `source-quadlet.before` → `/home/mip/apps/themike-site/systemd/themike-site.container`.

Ejecutar `systemctl --user daemon-reload` y `systemctl --user restart themike-site.service` como `mip`, con su entorno de usuario. Esto devuelve a `localhost/themike-site:koodaria-ip-20261022`. Conserva volúmenes y certificados; el dominio dejaría de servirse hasta restaurar la revisión HTTPS.

Para retirar también Koodaria por IP y volver al gateway original, usar el respaldo `/root/remediation-20261022/koodaria-publication-ip`: `Caddyfile`, `quadlet.before` y `source-quadlet.before` hacia los mismos destinos. La imagen resultante será `localhost/themike-site:2026-10-22-patched`.

No es necesario borrar contenedores, imágenes, certificados, volúmenes o redes. No usar comandos globales de limpieza. La zona DNS no fue modificada por el agente; cualquier rollback de DNS debe decidirse separadamente.

## Evidencia

- `evidence/https-publication.json`: certificados, vencimientos, cabeceras, redirects, rutas y laboratorio.
- `evidence/https-browser-report.json`: pruebas de navegador contra la URL HTTPS.
- `evidence/public-ip-publication.json` y `public-ip-browser-report.json`: evidencia histórica de la primera publicación por IP, anterior al cambio DNS.

Las rutas futuras `/enterprise`, `/login` y `/workspace` continúan devolviendo 404. La publicación no incorpora autenticación real a Koodaria ni modifica la del laboratorio.

## Actualización de contenido: retirar secciones 05 y 06

Se retiraron Desafíos técnicos y Recursos a petición del usuario, incluidos los enlaces de navegación y footer hacia esas secciones. Las secciones Inicio y 01–04 se mantienen. Imagen activa: `localhost/themike-site:koodaria-without-05-06-20261022`; contexto: `/home/mip/apps/koodaria-without-05-06`. Para revertir solo este cambio, restaurar `quadlet.before` y `source-quadlet.before` de `/root/remediation-20261022/koodaria-remove-05-06` a sus destinos habituales, recargar systemd de usuario y reiniciar el gateway. La imagen HTTPS anterior queda retenida.

## Revisión de lectura y contenido

Nueva imagen activa: `localhost/themike-site:koodaria-readable-20261022`, contexto `/home/mip/apps/koodaria-readable-20261022`. Se aligeraron los pesos de letra, se aumentaron los textos de lectura y se eliminaron la numeración de secciones y las etiquetas repetidas de las tarjetas. Los títulos se colocaron junto a iconos de 32–34 px, con trazo 1.4. Se simplificaron los textos, la presentación de Enterprise y el footer. El enlace empresarial dice «Para empresas» porque aún no existe un login de Koodaria.

El terminal utiliza una animación finita y local de escritura; no ejecuta comandos ni realiza conexiones. Admite pausa, continuación y repetición. Con movimiento reducido o JavaScript desactivado muestra el ejemplo completo. El lector de pantalla recibe el texto completo, sin anunciar cada carácter. Se corrigió además la visibilidad del enlace de salto bajo movimiento reducido.

Pruebas: seis comprobaciones estructurales, navegador a 320/390/768/1024/1280/1440 px y pruebas de animación. Evidencia de navegador: `evidence/readability-browser-report.json`. `tests/terminal_qa.py` permite repetir las pruebas de animación con Playwright. Se comprobaron los archivos desplegados contra `dist/` y el funcionamiento del laboratorio.

Rollback de esta revisión: restaurar `quadlet.before` y `source-quadlet.before` desde `/root/remediation-20261022/koodaria-readable`, recargar systemd de usuario y reiniciar `themike-site.service`. La revisión previa conserva HTTPS y el contenido anterior sin secciones 05/06. No se modificaron DNS, certificados o rutas del gateway.

## Terminal en ciclo continuo

La demostración ahora se repite automáticamente con una pausa de lectura entre ciclos, sin botones visibles. Se detiene fuera de pantalla, con la pestaña oculta o al enfocar el terminal; con movimiento reducido muestra el contenido completo sin animación. Se comprobaron dos reinicios automáticos consecutivos, ausencia de botones, pausa por foco y movimiento reducido mediante `tests/terminal_qa.py`. Imagen activa: `localhost/themike-site:koodaria-terminal-loop-20261022`, contexto `/home/mip/apps/koodaria-terminal-loop`. El respaldo de Quadlets de la revisión anterior está en `/root/remediation-20261022/koodaria-terminal-loop`.

## Ajuste de altura de la introducción

Se compactó únicamente el hero de escritorio (desde 901 px): márgenes verticales, espacios internos del panel y alto reservado del terminal. Se conservan los tamaños de lectura y la disposición móvil. No se utiliza zoom ni escalado de la página. Se verificó el hero completo a zoom normal en 1440×768, 1366×680, 1280×720 y 1024×768; sin desbordamiento horizontal en móvil. Evidencia: `evidence/compact-hero-report.json`. Imagen activa: `localhost/themike-site:koodaria-compact-hero-20261022`, contexto `/home/mip/apps/koodaria-compact-hero`; respaldo de Quadlets de la revisión previa en `/root/remediation-20261022/koodaria-compact-hero`.

## Altura adaptable al navegador

El hero ahora usa `100dvh` (con fallback `100vh`) menos la altura real del encabezado. Una cuadrícula distribuye el contenido y mantiene «Áreas de trabajo» en el borde inferior del fondo. ResizeObserver actualiza la medida del encabezado cuando cambia su distribución o se abre el menú móvil; CSS responde al ancho, alto y orientación sin identificar marcas de navegador ni depender de la resolución física del monitor. No se aplica zoom, escala global, recorte ni altura máxima al contenido.

Se probaron veinte combinaciones de viewport y densidad de píxel (1×/2×), incluyendo redimensionado sin recargar y apertura/cierre del menú. En escritorios de 1024×768 a 1920×1080 el fondo termina exactamente al final del viewport. En móvil, tablet vertical o ventanas muy bajas se permite que el contenido crezca y se recorra: no se fuerza toda la composición a una pantalla a costa de la lectura. Evidencia: `evidence/viewport-hero-report.json`.

Imagen activa: `localhost/themike-site:koodaria-viewport-hero-20261022`, contexto `/home/mip/apps/koodaria-viewport-hero`. El respaldo de Quadlets para volver a la revisión anterior está en `/root/remediation-20261022/koodaria-viewport-hero`.

## Simplificación del hero y centrado del menú

Se retiraron la franja «Áreas de trabajo», la nota de demostración, el pie del panel y «Un caso sencillo». Se corrigió el nombre accesible de la figura al retirar su figcaption. El hero conserva el fondo a altura de viewport con una sola fila de contenido. En escritorio, el logo, el menú de secciones y las acciones ocupan tres columnas: el menú queda centrado respecto al ancho de la ventana. En móvil se conserva el menú desplegable. Por petición explícita del usuario se cambió la etiqueta «Para empresas» a «Login»; mantiene su destino informativo en Enterprise, sin implementar autenticación nueva.

Imagen activa: `localhost/themike-site:koodaria-clean-header-20261022`, contexto `/home/mip/apps/koodaria-clean-header`. Respaldo de Quadlets para rollback: `/root/remediation-20261022/koodaria-clean-header`. Pruebas estructurales y revisión publicada a seis tamaños; evidencia `evidence/clean-header-report.json`.

## Composición de ventanas en cascada

Se redistribuyeron las columnas de texto y panel y se añadieron dos ventanas decorativas detrás del ejemplo principal, con desplazamientos, bordes y sombras suaves en la paleta existente. El panel animado sigue delante y completamente accesible. Las ventanas traseras están marcadas `aria-hidden`, no reciben foco ni eventos de puntero; en móvil sus desplazamientos son menores. La portada mantiene la altura de viewport en escritorio y el contenido crece naturalmente en móvil.

Se verificaron ocho tamaños, ausencia de desbordamiento y el ciclo de animación, con evidencia en `evidence/cascade-report.json`. Imagen activa: `localhost/themike-site:koodaria-cascade-20261022`, contexto `/home/mip/apps/koodaria-cascade`. Respaldo de Quadlets para volver a la revisión anterior: `/root/remediation-20261022/koodaria-cascade`.

## Etiqueta ejecutiva y página de inicio de sesión

La portada cambia su etiqueta a «Gestión, continuidad y resiliencia» y elimina el guion decorativo. El enlace Login ahora lleva a `/login/`, una página independiente con la misma identidad visual, enlaces para volver al inicio y acceso a privacidad. Caddy sirve el nuevo directorio estático y normaliza `/login` a `/login/`. La publicación de esta página responde a la ampliación explícita del alcance solicitada por el usuario.

Se solicitó aclaración sobre la conexión real a Keycloak. Hasta definirla, la página es visual: comunica que el acceso aún no está habilitado; el fieldset está deshabilitado, no tiene acción de envío ni JavaScript, no recoge ni valida contraseñas y no simula sesiones. No se modificaron realms, usuarios, clientes OIDC o contenedores de identidad del laboratorio. `/enterprise` y `/workspace` siguen fuera de esta fase; `/login/` ya es una ruta pública.

Pruebas: siete comprobaciones estructurales y navegación desde el Login de Home hacia la nueva página a cinco tamaños, con comprobación de accesibilidad, ausencia de desbordamiento y campos deshabilitados. Evidencia: `evidence/login-page-report.json`. Imagen activa: `localhost/themike-site:koodaria-login-page-20261022`, contexto `/home/mip/apps/koodaria-login-page`; respaldo de Quadlets para rollback en `/root/remediation-20261022/koodaria-login-page`.

## Login centrado según referencia visual

Se adaptó la composición de la referencia proporcionada por el usuario al logo, tipografía y paleta de Koodaria: formulario de una columna centrada, fondo limpio, título centrado y enlace de cierre arriba a la derecha. Se retiraron el bloque lateral y la tarjeta exterior. La pantalla sigue siendo visual, con campos deshabilitados y aviso de disponibilidad; no se añaden proveedores de identidad o enlaces de registro inexistentes.

Pruebas estructurales, accesibilidad local y revisión publicada a cinco tamaños, incluido el cierre hacia la Home. Evidencia: `evidence/centered-login-report.json`. Imagen activa: `localhost/themike-site:koodaria-centered-login-20261022`, contexto `/home/mip/apps/koodaria-centered-login`; respaldo de Quadlets para rollback en `/root/remediation-20261022/koodaria-centered-login`.

## Paleta verde

A petición del usuario se sustituyeron los acentos cobre y marrones por variantes minerales y salvia en Home y login. Se actualizaron botones, estados hover y foco, títulos, subrayados, fondos, punto del logo y favicon. Los tokens de color se denominan ahora `--accent`, `--accent-ink` y `--line-soft`. Los botones principales usan blanco sobre verde bosque; se comprobaron contraste y accesibilidad en ambas páginas a tamaños de escritorio y móvil. Evidencia: `evidence/green-palette-report.json`.

Imagen activa: `localhost/themike-site:koodaria-green-palette-20261022`, contexto `/home/mip/apps/koodaria-green-palette`; respaldo de Quadlets para rollback en `/root/remediation-20261022/koodaria-green-palette`.
