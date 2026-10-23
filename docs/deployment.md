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

- Fuente: `app/`; imagen `localhost/koodaria-workspace:sidebar-20261023`.
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
