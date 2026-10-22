# Publicación autorizada por IP y preparación de dominio

22 de octubre de 2026. El usuario autorizó explícitamente la exposición pública y los cambios de DNS, certificado y Caddy necesarios para `koodaria.com`.

## Estado comprobado

- **http://45.80.153.100** sirve la Home y sus assets. No es todavía una URL HTTPS.
- Se reutiliza el contenedor `themike-site`, con imagen nueva `localhost/themike-site:koodaria-ip-20261022` y el runtime parcheado original. La imagen anterior se conserva.
- El artefacto de Home está en `/srv/koodaria`, separado del contenido original en `/srv`. Se añadió un host HTTP por IP al Caddyfile existente. No se crearon puertos de entrada, volúmenes o redes nuevos.
- Los volúmenes de certificados y los dos grupos de redes del gateway se conservaron. Hubo un reinicio breve del gateway para activar su nueva imagen, ya que su API administrativa está desactivada. Tras el cambio se verificaron landing, portal y OIDC de Keycloak.
- El contenedor de desarrollo `koodaria-public-home-v1-review` permanece aislado; no es el backend de producción.
- La misma batería de navegador pasó contra la IP pública en seis tamaños, sin errores de consola, solicitudes fallidas ni incidencias automáticas WCAG.

## DNS pendiente

Los servidores autoritativos son `lunar.dns-parking.com` y `solar.dns-parking.com`. El registro A de `koodaria.com` todavía devuelve `2.57.91.91`. `www` ya tiene CNAME a `koodaria.com.`. No se encontró un AAAA público.

Cambio necesario:

| Tipo | Nombre | Destino |
|---|---|---|
| A | @ | 45.80.153.100 |
| CNAME | www | koodaria.com (ya existe) |

Se deben conservar los registros de correo, TXT y otros nombres. No resetear toda la zona. No se encontró una credencial local de Hostinger disponible y se solicitó al usuario su ruta. No se debe guardar ningún token en este repositorio o pegarlo en comandos que puedan registrarlo. Una ubicación privada posible es `~/.config/hostinger/api-token` con permisos 600.

Referencia de API oficial: https://developers.hostinger.com/ . `PUT /api/dns/v1/zones/koodaria.com` permite reemplazar exclusivamente el grupo A de `@` mediante `overwrite:true`; se debe leer y respaldar la zona antes de actualizarla. El CNAME `www` no necesita cambiar si mantiene su destino actual.

## Configuración HTTPS preparada, aún no activada

`infra/edge/koodaria.caddy` define el dominio canónico, redirección permanente desde `www`, HSTS de un año sin imponerlo a otros subdominios, CSP restrictiva, nosniff, denegación de iframes, política de permisos, política de referente y eliminación de Server. Los assets no fingerprintados se revalidan con `no-cache`.

El dominio en la configuración habilita automáticamente la obtención y renovación de certificados públicos ACME gratuitos de Caddy, y su redirección HTTP→HTTPS. No requiere un certificado comprado ni un plugin DNS para estos dos nombres. La emisión debe esperar a que A/AAAA sean correctos y el dominio alcance este gateway por 80/443. Referencia: https://caddyserver.com/docs/automatic-https .

El Caddyfile completo con estos hosts se validó dentro del runtime, pero no se activó mientras el DNS señala otro servidor. Está preparado en `/home/mip/apps/koodaria-edge-20261022/edge.Caddyfile.with-domain`. Tras cambiar y verificar DNS:

1. Respaldar el gateway y Quadlets de su revisión por IP.
2. Construir otra etiqueta inmutable con el Caddyfile de dominio y el mismo `dist/`, usando `infra/edge/Containerfile`.
3. Validar el Caddyfile antes de cambiar imagen. Conservar el resto de hosts sin modificaciones.
4. Actualizar únicamente la referencia de imagen del gateway en su Quadlet activo y copia de fuente; recargar systemd de usuario y reiniciar el gateway.
5. Verificar certificado público, nombres SAN, cadena confiable, HTTP→HTTPS, www→canónico, cabeceras, assets y laboratorio. Si falla la configuración, restaurar la revisión anterior.
6. Una vez comprobado HTTPS, reemplazar la ruta HTTP de IP por una redirección a `https://koodaria.com` si se desea retirar el acceso transitorio.

## Reproducción del gateway por IP

Contexto dedicado `/home/mip/apps/koodaria-edge-20261022` con `Containerfile`, `edge.Caddyfile` y `dist/`. La receta de gateway copia únicamente los archivos estáticos nuevos y el Caddyfile ensamblado sobre la imagen base inmutable. No debe construirse con secretos en el contexto.

```sh
cd /home/mip/apps/koodaria-edge-20261022
podman build --format docker --pull=never -f Containerfile \
  -t localhost/themike-site:koodaria-ip-20261022 .
```

Los fragmentos versionados están en `infra/edge/`. El contexto ensamblado y las copias del gateway completo permanecen fuera del repositorio para evitar convertir este proyecto en la configuración propietaria de los otros hosts.

## Rollback del cambio público por IP

Como administrador del VPS, restaurar desde `/root/remediation-20261022/koodaria-publication-ip`:

- `Caddyfile` → `/home/mip/apps/themike-site/Caddyfile`.
- `quadlet.before` → `/home/mip/.config/containers/systemd/themike-site.container`.
- `source-quadlet.before` → `/home/mip/apps/themike-site/systemd/themike-site.container`.

Después, ejecutar `systemctl --user daemon-reload` y `systemctl --user restart themike-site.service` como `mip` con su entorno de usuario. Esto devuelve el gateway a `localhost/themike-site:2026-10-22-patched`, retirando únicamente la publicación de Koodaria. Los volúmenes, certificados y servicios del laboratorio se conservan. No ejecutar podman prune ni eliminar contenedores o imágenes existentes.

## Evidencia

`evidence/public-ip-publication.json` registra HTTP/cabeceras y resolución autoritativa. `evidence/public-ip-browser-report.json` registra las pruebas de navegador sobre la URL pública. HTTPS del dominio permanece pendiente; no se presenta como verificado o emitido.
