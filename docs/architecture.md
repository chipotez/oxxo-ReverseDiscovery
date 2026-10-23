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

## Límites y evolución

No se conectó Koodaria con el realm o los usuarios existentes. El esquema Público → Enterprise → Keycloak → Workspace es solo informativo. Las futuras rutas pueden implementarse como aplicaciones separadas bajo el proxy existente, con autenticación del lado servidor y controles por organización. Esta decisión se deberá revisar en la fase de Enterprise.

No hay pipeline automático, registro de imágenes ni publicación de dominio aún. Se propone validar cada commit, etiquetar imágenes inmutables, conservar la anterior y promover únicamente con autorización para modificar producción. La política de privacidad final y el contacto necesitan datos institucionales confirmados antes de un lanzamiento público.

## Integración de identidad preparada (23 de octubre de 2026)

Keycloak instalado: 26.8.1. El acceso administrativo probado exige completar `CONFIGURE_TOTP` (Mobile Authenticator Setup). No se crearon realms, organizaciones ni usuarios; Login público continúa sin autenticación real. No se alteró el laboratorio ni se intentó eludir MFA.

`infra/keycloak/koodaria-realm.json` prepara un realm independiente, con organizaciones, español, HTTPS obligatorio, protección contra intentos repetidos y sin registro público. Recuperación de contraseña permanece deshabilitada hasta disponer de correo saliente. `scripts/provision_keycloak.py` valida sin modificar nada por defecto; `--apply --credentials-file RUTA` requiere una cuenta de servicio administrativa de master y un archivo privado (600) con `client_id` y `client_secret`. No utiliza la contraseña de una persona. Si el realm ya existe, no lo sobrescribe. No genera usuarios ni membresías automáticamente.

Propuesta pendiente de elección: una organización Kyndryl admite miembros de varios dominios cuando comparten un mismo ámbito de acceso. Para clientes que requieren separación, usar organizaciones distintas por empresa dentro de koodaria. No asumir organizaciones anidadas: la relación comercial Kyndryl–cliente y los permisos cruzados deben modelarse explícitamente en la aplicación. El dominio de correo ayuda al enrutamiento de identidad; no concede acceso por sí solo. La aplicación deberá validar membresía y permisos en cada recurso privado.

La publicación de Login queda pendiente de acceso administrativo válido. La autenticación se delegará en Keycloak (OpenID Connect), sin capturar contraseñas desde la Home. El destino inicial propuesto es la cuenta del usuario; una sesión para un futuro workspace requiere su propia integración OIDC y autorización, y todavía no está implementada.

Referencia: https://www.keycloak.org/docs/latest/server_admin/ (Organizations).
