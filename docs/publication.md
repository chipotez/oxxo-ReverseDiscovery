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

Se reutiliza el gateway `themike-site`, ahora con imagen `localhost/themike-site:koodaria-identity-20261023`. Su base es el runtime parcheado original, fijado por ID. La Home está en `/srv/koodaria`, separada de la landing del laboratorio en `/srv`. No requiere backend nuevo, redes o puertos adicionales. El contenedor de desarrollo permanece aislado y no forma parte del tráfico de producción.

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

## Logo consistente entre Home y Login

Login reutiliza la geometría del encabezado y la tipografía de Home, incluidos sus puntos de adaptación. Publicado con `localhost/themike-site:koodaria-logo-parity-20261022`. Respaldo de las unidades en `/root/remediation-20261022/koodaria-logo-parity`.

Se compararon las coordenadas y dimensiones reales del logo en producción para nueve tamaños de pantalla (320–1920 px), con densidades 1 y 2: las 18 comparaciones coinciden, sin desbordamiento horizontal. Evidencia: `evidence/logo-parity-report.json`. Las siete pruebas estructurales siguen pasando.

## Mayor separación vertical en la introducción

En escritorios de al menos 800 px de alto, el texto dispone de mayor separación entre encabezado, título, descripción y acciones. Los espacios se adaptan a la altura disponible; los equipos con menos altura conservan la distribución compacta. Imagen: `localhost/themike-site:koodaria-hero-spacing-20261022`. Respaldo: `/root/remediation-20261022/koodaria-hero-spacing`. Verificación en cinco tamaños de pantalla y siete pruebas estructurales correctas. Evidencia: `evidence/hero-spacing-report.json`.

## Mensaje de desarrollo de competencias

Descripción principal orientada a las habilidades necesarias en las organizaciones y a los recursos de Koodaria. Publicada con `localhost/themike-site:koodaria-business-copy-20261022`; respaldo `/root/remediation-20261022/koodaria-business-copy`. Texto confirmado en producción, siete pruebas estructurales correctas y distribución verificada en cinco tamaños de pantalla (`evidence/business-copy-report.json`).

## Título principal aprobado

“Potencia tus habilidades. Convierte conocimiento en experiencia.” Publicado con `localhost/themike-site:koodaria-skills-title-20261022`. Respaldo: `/root/remediation-20261022/koodaria-skills-title`. Texto confirmado en producción; siete pruebas estructurales y cinco tamaños de pantalla correctos (`evidence/skills-title-report.json`).

## Consola sin etiqueta

Retirada la etiqueta visible “Ejemplo animado”. Publicado con `localhost/themike-site:koodaria-no-label-20261022` y verificado en el HTML público. Respaldo: `/root/remediation-20261022/koodaria-no-label`.

## Keycloak y primer acceso con 2FA — 23 de octubre de 2026

DNS A de `login.koodaria.com` confirmado en 1.1.1.1 y 8.8.8.8. Certificado válido de Let’s Encrypt y renovación automática con el almacenamiento persistente de Caddy. `/login/` redirige al servicio de identidad de Koodaria. Gateway activo: `localhost/themike-site:koodaria-identity-20261023`.

Realm `koodaria`, organización `Kyndryl` vacía y temas de Login/cuenta propios. Cada empresa cliente tendrá una organización independiente. Primer acceso: contraseña correcta → QR e instrucciones → validación TOTP. Siguientes accesos desde una sesión nueva: contraseña + TOTP. No se crearon usuarios reales ni se importaron cuentas del laboratorio. El destino actual es la gestión de cuenta nativa, no un Workspace.

Se utilizó el procedimiento oficial de recuperación con una cuenta de servicio temporal y respaldo previo de Postgres; no se retiró el MFA del administrador. Copias de unidades y Caddyfile en `/root/remediation-20261023/koodaria-identity`. Informe funcional: `evidence/keycloak-2fa-report.json`; HTTPS, dominio, administración y vistas móviles: `evidence/keycloak-publication-report.json`.

La cuenta administrativa temporal fue eliminada y una solicitud posterior con su secreto devolvió HTTP 401. El archivo local del secreto se retiró. Confirmación de configuración sin secretos: `evidence/keycloak-config-report.json`. El MFA del administrador humano sigue pendiente de su propia vinculación y no fue eliminado.

Se verificó también que el logo conserva posición y tamaño frente a Home en escritorio y móvil, y que axe no detecta infracciones WCAG A/AA en las tres vistas revisadas (`evidence/keycloak-accessibility-report.json`).

## Tema de acceso y alta de 2FA refinado — 23 de octubre de 2026

Tema `koodaria-v3.css`: panel blanco de bordes redondeados y sombra suave, aviso de alta en verde mineral con icono Tabler, aplicaciones autenticadoras en etiquetas, QR y formulario en columnas en escritorio y apilados en móvil. Se conserva la geometría del logo. El selector de idioma ocupa su propia fila para evitar solaparse con el título. Los errores conservan una presentación distinta del aviso informativo.

Solo se modificaron recursos del tema montado en Keycloak; no se cambiaron el flujo de autenticación, usuarios, contraseñas ni autenticadores. Respaldo del tema anterior: `/home/mip/backups/koodaria-20261023/theme-before-premium.tar.gz`. La versión nueva del archivo CSS evita reutilizar la caché del estilo anterior. El gateway continúa en `localhost/themike-site:koodaria-identity-20261023`.

Evidencia de navegación y accesibilidad: `evidence/premium-mfa-report.json`. Las capturas de revisión locales ocultan el QR y la clave de configuración; no se enviaron formularios de alta de MFA durante la revisión.

Los recursos públicos del tema deben quedar con directorios 755 y archivos 644 para que el UID no privilegiado del contenedor pueda leerlos. El respaldo permanece privado (600); no aplicar su umask a los archivos que sirve el tema.

## Alta de 2FA adaptada al alto y ancho visibles — 23 de octubre de 2026

Tema `koodaria-v4.css` y mejora progresiva `responsive-enrollment-v2.js`. La tarjeta completa usa una distribución más compacta en escritorio. Bajo 800 px de ancho o 700 px de alto, la configuración se divide en aplicación, vinculación y verificación. La densidad se ajusta a la altura disponible, incluidos cambios de `visualViewport`. En vistas muy bajas el selector de idioma se sitúa en la cabecera. Los campos y el botón nativo de envío se conservan; el código no lee contraseñas ni códigos, no usa almacenamiento ni envía solicitudes.

Se conserva la tarea activa y el contenido de los campos al cambiar el tamaño de la ventana. La configuración manual mantiene sus parámetros nativos en un desplegable dentro del paso de vinculación. Si la mejora progresiva no carga, el formulario nativo continúa disponible; no se oculta contenido mediante un overflow global ni se aplica zoom o escala a la página.

Validación en producción de 11 tamaños de pantalla, 23 estados y densidades 1/2: sin scroll horizontal o vertical en las vistas verificadas, con envío visible y accesible. Se comprobaron navegación por teclado, retroceso, configuración manual, preservación de campos y un envío real de TOTP únicamente con una cuenta desechable. axe no encontró infracciones WCAG A/AA en los estados analizados. La cuenta de QA y la cuenta de servicio administrativa temporal se eliminaron; el acceso temporal devuelve 401. La cuenta personal y su autenticador no se modificaron. Evidencia: `evidence/responsive-enrollment-report.json`.

Respaldo del tema anterior: `/home/mip/backups/koodaria-20261023/theme-before-responsive.tar.gz`. Solo se sustituyó el tema de Keycloak; el gateway permanece en la misma imagen.

## Perfil y consola de cuenta coherentes con Koodaria — 23 de octubre de 2026

Publicado `koodaria-v6.css` para las acciones de acceso y `account-v4.css` con
`account-brand-v2.js` para la consola nativa. Corregida la mezcla de tokens de
modo oscuro con fondos claros (`darkMode=false`). Logo con la tipografía y la
alineación de Home, navegación verde salvia, campos claros, bordes redondeados,
sombras suaves y estados de foco visibles. Título de pestaña propio de Koodaria.

La verificación de perfil adapta sus columnas y espaciados al ancho y alto.
La información personal se divide en dos pasos en ventanas pequeñas. Los métodos
de acceso usan pestañas cuando falta espacio; los metadatos secundarios de las
sesiones quedan desplegables. Los formularios y controles de seguridad nativos
siguen operativos. La regla para futuras vistas está en `../AGENTS.md` y
`design-system.md`; nunca recortar contenido ni aplicar zoom CSS para ocultar
scroll. Se conserva desplazamiento accesible para ampliación extrema, teclado
virtual, colecciones largas o detalles abiertos explícitamente.

Verificados 32 estados en escritorio, tablet, móvil y horizontal, sin overflow
del documento ni de los paneles en las vistas predeterminadas. Diez auditorías
axe A/AA en las cinco secciones con preferencias de sistema clara y oscura, sin
infracciones detectadas. Se probó guardado real y persistencia tras recarga,
además de conservar campos sin guardar al redimensionar, solo con identidades
desechables. Contraste calculado: texto principal 11,24:1; secundario 5,82:1;
texto blanco en botón 6,73:1; borde de campo 3,58:1.

Eliminadas tres cuentas de QA y el cliente administrativo temporal; su secreto
ya devuelve 401 y los archivos privados de prueba fueron retirados. No se tocó
la cuenta personal ni su MFA. Respaldo privado del tema previo:
`/home/mip/backups/koodaria-20261023/before-account-style.tar.gz`. El gateway
conserva la imagen anterior; solo se actualizó el tema montado en Keycloak.
Evidencias: `evidence/account-responsive-theme-report.json` y
`evidence/account-color-contrast.json`.

## Bienvenida privada después del acceso — 23 de octubre de 2026

La Home conserva su diseño. Login ahora inicia `koodaria-web` y termina en
`https://koodaria.com/bienvenida/` después de las verificaciones de Keycloak.
La nueva vista usa una barra flotante, Servicios/Módulos, configuración y menú
personal con Mi cuenta, Volver al inicio y Cerrar sesión. El nombre y las
iniciales proceden de la identidad validada; no están escritos en el frontend.
El contenido se mantiene mínimo para la siguiente fase de servicios.

Aplicación: `localhost/koodaria-workspace:welcome-20261023`. Gateway:
`localhost/themike-site:koodaria-welcome-20261023`. Se conserva el resto del
laboratorio. La regla CSP del espacio privado permite el formulario local y
exclusivamente el endpoint de salida de Keycloak; la Home conserva su política
anterior. Las rutas privadas tienen no-store separado de los encabezados públicos.

Cliente OIDC confidencial con callback exacto y PKCE S256; sesión opaca en cookie
Secure/HttpOnly/SameSite=Lax y datos de sesión en volumen privado. La aplicación
no publica puertos. Las credenciales se transfirieron por stdin a un archivo 600
fuera del repositorio desplegado. No se cambió el MFA ni la cuenta personal.

Verificación final: contraseña → alta TOTP → bienvenida, identidad real en menú,
protección de acceso anónimo, cookie opaca segura, no-store, rechazo de cierre
con CSRF inválido y cierre efectivo de sesión local + SSO. Ocho resoluciones con
menú abierto/cerrado (16 estados sin scroll), seis auditorías axe A/AA en
preferencias claras/oscuras sin incidencias, ocho pruebas de backend y siete de
la Home. Evidencia: `evidence/welcome-flow-report.json`. Se retiraron el usuario
desechable y el cliente administrativo temporal; sus credenciales ya devuelven
401. Se conservan únicamente las credenciales operativas de la aplicación en
archivos privados ignorados. La cuenta personal y su autenticador no se tocaron.

## Header compacto y navegación lateral — 23 de octubre de 2026

Publicado `localhost/koodaria-workspace:sidebar-20261023`. Header limitado a
1100 px en escritorio y aproximadamente 68 px de alto; adaptación en dos filas
en pantallas estrechas. Se retiraron el saludo, la etiqueta superior y el nombre
de sección del centro visible. El título accesible de la vista se conserva.

Barra lateral con monograma, inicio, asistente, aplicaciones, biblioteca,
aprendizaje, crear y favoritos; preferencias, apariencia, configuración,
consola y perfil al pie. Bordes suaves, trazos finos y verdes de Koodaria.
Las secciones por ahora seleccionan el estado de navegación sobre un lienzo
vacío: no se incorporaron servicios ni acciones de creación. Cuenta e idioma
abren la gestión real de cuenta. Apariencia alterna una paleta mineral clara u
oscura y guarda únicamente la preferencia local, sin datos de autenticación.

Verificados 32 estados (ocho tamaños, dos temas, menú abierto/cerrado), todos con
controles laterales visibles y sin overflow. Auditorías axe A/AA en escritorio y
móvil sin incidencias. Ocho pruebas de servidor y siete de Home correctas.
La revisión visual usa el template real con identidad sintética interceptada
solo dentro del navegador de QA; no se desplegó ningún acceso de prueba ni se
crearon usuarios administrativos. Los recursos publicados coinciden con fuente.
Evidencia: `evidence/sidebar-layout-report.json`.

No se cambiaron el flujo OIDC, el MFA, secretos, sesiones ni el gateway. El
volumen de sesiones permanece montado. Respaldo de la unidad anterior en
`/home/mip/backups/koodaria-20261023/sidebar/`; rollback con la imagen
`localhost/koodaria-workspace:welcome-20261023`.
