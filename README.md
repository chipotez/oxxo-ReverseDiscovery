# Koodaria · Home pública / Fase 1

Implementación propia de la Home de Koodaria. El ZIP recibido es **solo una referencia**, se conserva intacto y no se incorpora al sitio ni al historial. No se implementan Enterprise, login, Workspace, cursos o ejecución de laboratorios.

## Desarrollo local

Requiere Python 3.9 o superior. No necesita Node, npm, servicios de terceros ni instalación de paquetes para compilar o servir.

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
python3 scripts/serve.py
```

Abrir **http://127.0.0.1:4173**. El servidor escucha únicamente en loopback; detener con Ctrl+C. La compilación genera `dist/` (ignorado por Git). No se necesita conexión a Internet durante compilación o navegación.

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

El terminal es una demostración animada, sin ejecución real. Puede pausarse o repetirse y respeta la preferencia de movimiento reducido. Enterprise es una sección informativa con un flujo futuro; `/enterprise`, `/login` y `/workspace` devuelven 404. No hay formularios ni credenciales. El canal de contacto aún debe confirmarse.

## Vista de la implementación

[Escritorio](docs/evidence/desktop.png) · [Móvil](docs/evidence/mobile.png)

## Podman y publicación

Ver [inspección y arquitectura](docs/architecture.md), [despliegue y rollback](docs/deployment.md) y [validación](docs/validation.md).

La Home está publicada en **https://koodaria.com**, con certificado gratuito de Let’s Encrypt, renovación automática de Caddy, redirección HTTP→HTTPS y `www`→dominio canónico. Se conservan el laboratorio y Keycloak. El contenedor de desarrollo sigue aislado. El acceso por IP continúa disponible como entrada HTTP transitoria; la URL recomendada es siempre HTTPS. Véase [publicación](docs/publication.md).
