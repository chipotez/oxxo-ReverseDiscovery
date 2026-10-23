# Koodaria · Home pública / Fase 1

Implementación propia de la Home de Koodaria. El ZIP recibido es **solo una referencia**, se conserva intacto y no se incorpora al sitio ni al historial. El Login público está conectado a Keycloak mediante `login.koodaria.com`, con contraseña y 2FA obligatorio. Enterprise, Workspace, cursos y ejecución de laboratorios siguen fuera del alcance actual.

## Desarrollo local

Requiere Python 3.9 o superior. No necesita Node, npm, servicios de terceros ni instalación de paquetes para compilar o servir.

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
python3 scripts/serve.py
```

Abrir **http://127.0.0.1:4173**. El servidor escucha únicamente en loopback; detener con Ctrl+C. La compilación genera `dist/` (ignorado por Git). La Home puede compilarse y navegarse sin Internet; el inicio de sesión requiere el Keycloak publicado.

## Organización

- `src/index.html`: composición de la Home y secciones editoriales.
- `src/content/es.json`: navegación, catálogo y tecnologías; preparado para separar idiomas.
- `scripts/build.py`: componentes de catálogo, tarjetas, iconos y enlaces; escape HTML y generación determinista.
- `src/assets/styles.css`: tokens Mineral Intelligence, componentes y adaptaciones responsive.
- `src/assets/app.js`: módulos nativos del navegador, pestañas accesibles y menú móvil; sin APIs ni lógica de negocio.
- `src/assets/icons/`: SVG locales oficiales de Tabler con trazo de 1.4; licencia MIT en `docs/tabler-LICENSE.txt`, también distribuida en assets.
- `infra/`: configuración exclusiva del servicio nuevo; no reemplaza el proxy global.
- `tests/`: validación estructural y pruebas opcionales de navegador.
- `docs/`: inspección técnica, decisiones, despliegue, rollback y resultados.

Se usa la tipografía del sistema; no hay descarga de fuentes. Los nombres de tecnologías no sugieren afiliaciones. AWS, Azure y GCP utilizan iconos genéricos de cloud, no marcas recreadas.

## Interacciones reales

Las pestañas cambian entre módulos, rutas y especializaciones; admiten flechas, Home/End y foco visible. Las tarjetas despliegan sus temas. Los enlaces del footer seleccionan un grupo existente. El menú móvil admite Escape, cierra al navegar y comunica su estado. La navegación funciona sin JavaScript, mostrando entonces todos los grupos.

El terminal es una demostración animada, sin ejecución real. Se repite automáticamente, se pausa al enfocar el terminal y respeta la preferencia de movimiento reducido. Enterprise es una sección informativa con un flujo futuro; `/enterprise` y `/workspace` devuelven 404. En producción, `/login/` redirige a la cuenta de Koodaria en Keycloak. La primera autenticación exige vincular una aplicación autenticadora; las siguientes exigen contraseña y TOTP. Las contraseñas se introducen únicamente en Keycloak. La Home no guarda credenciales ni tokens. En el servidor local, la página de Login ofrece un enlace al servicio publicado. El canal de contacto aún debe confirmarse.

## Vista de la implementación

[Escritorio](docs/evidence/desktop.png) · [Móvil](docs/evidence/mobile.png)

## Podman y publicación

Ver [inspección y arquitectura](docs/architecture.md), [despliegue y rollback](docs/deployment.md) y [validación](docs/validation.md).

La Home está publicada en **https://koodaria.com**, con certificado gratuito de Let’s Encrypt, renovación automática de Caddy, redirección HTTP→HTTPS y `www`→dominio canónico. Se conservan el laboratorio y Keycloak. El contenedor de desarrollo sigue aislado. El acceso por IP continúa disponible como entrada HTTP transitoria; la URL recomendada es siempre HTTPS. Véase [publicación](docs/publication.md).

## Identidad

Realm independiente `koodaria`, temas propios en `infra/keycloak/themes/koodaria`. La organización `Kyndryl` está creada sin usuarios; cada empresa cliente tendrá otra organización. El dominio del correo no concede membresía automáticamente. El destino tras autenticar es la gestión de cuenta, no un Workspace privado. La autorización de datos por organización se implementará junto con esa aplicación.

`scripts/provision_keycloak.py` y `scripts/configure_keycloak.py` validan sin cambios por defecto. La aplicación requiere `--apply --credentials-file RUTA`, con una cuenta de servicio autorizada y archivo privado 600. No hay credenciales administrativas activas en el repositorio. La prueba `tests/keycloak_live_qa.py --credentials-file RUTA` usa Playwright y crea/elimina una cuenta desechable; debe ejecutarse solo con autorización administrativa.
