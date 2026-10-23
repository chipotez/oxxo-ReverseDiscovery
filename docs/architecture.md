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

`/login` y `/login/` en koodaria.com redirigen a `https://login.koodaria.com/realms/koodaria/account/`. El cliente público nativo `account-console` usa Authorization Code con PKCE S256 y devuelve al usuario a su gestión de cuenta. La Home no recibe contraseñas, secretos de cliente ni tokens. No hay aún una sesión ni un backend de Workspace.

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

Enterprise y Workspace continúan informativos. No hay pipeline automático ni registro remoto de imágenes. La política de privacidad final, el contacto, SMTP y la asignación de empresas/usuarios reales requieren datos institucionales. El inicio de sesión actual permite gestionar la cuenta; no implica acceso a herramientas o datos empresariales todavía no implementados.
