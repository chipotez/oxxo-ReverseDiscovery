# Validación de Fase 1

Fecha: 22 de octubre de 2026. Rama: `feature/koodaria-public-home-v1`.

## Resultados

- Compilación Python sin dependencias: correcta. Generación determinista de HTML; todos los assets son locales.
- Seis pruebas estructurales: correctas. Enlaces e IDs únicos, assets presentes, rutas privadas ausentes, catálogo íntegro sin JavaScript, escape editorial y compilación determinista.
- Chrome instalado en macOS, controlado con Playwright 1.55.0 en perfil de pruebas separado: correcto en 1440×1000, 1280×900, 1024×768, 768×1024, 390×844 y 320×740. Sin desbordamiento horizontal.
- Pestañas por clic, flechas y Home; cambio de paneles de 6 a 3 tarjetas, detalles, enlaces del footer que seleccionan grupo, aviso de contacto, menú móvil con cierre al navegar y Escape: correctos en los seis tamaños.
- Sin errores JavaScript de consola ni solicitudes fallidas. CSS, JavaScript e iconos locales cargados. Tipografía del sistema, sin CDN.
- Axe-core 4.10.3: cero incidencias en las reglas automatizadas etiquetadas WCAG 2 A/AA, 2.1 AA y 2.2 AA para los seis tamaños. El texto oscuro de botones cobre se ajustó tras detectar contraste insuficiente.
- Revisión visual de capturas de escritorio, tablet y móvil: sin superposiciones o recortes observados.
- Reflujo adicional a 640 px y preferencia de movimiento reducido: correctos. No se afirma una prueba de zoom nativo del navegador.
- JavaScript desactivado en móvil: doce tarjetas y navegación visibles; los desplegables HTML siguen siendo utilizables.
- Podman rootless: build correcto con `--format docker`, runtime UID 1000, filesystem de solo lectura, red `none`, sin puertos publicados y healthcheck correcto.
- Home, healthz, CSS, JS, favicon y licencia responden 200; `/enterprise`, `/login` y `/workspace` responden 404.
- Todos los archivos servidos del contenedor coinciden por SHA256 con `dist/` local.
- Los cinco contenedores del laboratorio siguen en ejecución. La primera instancia nueva de Koodaria quedó detenida y retenida para rollback; la revisión corregida está saludable.

La herramienta integrada de navegador no pudo iniciar su runtime. Se utilizó Chrome headless local con perfil separado, sin modificar el navegador del usuario. Las pruebas automatizadas y la inspección visual básica no certifican conformidad WCAG completa; no se evaluó con lectores de pantalla ni Safari/Firefox en esta fase.

## Evidencia

- `evidence/browser-report.json`: tamaños, incidencias de axe, consola y fallback.
- `evidence/podman-report.json`: imagen, aislamiento, estado y respuestas HTTP.
- `evidence/build-sha256.json`: checksum de todos los archivos de la salida validada.
- `evidence/desktop.png`, `evidence/mobile.png`: capturas del primer viewport; capturas completas y tablet disponibles localmente en `.artifacts/`.

## Repetir pruebas de navegador (opcional)

Estas dependencias solo sirven para QA y no forman parte de la aplicación o imagen. Se requiere Chrome instalado. El puerto local debe estar sirviendo la compilación, en otra terminal:

```sh
python3 scripts/build.py
python3 scripts/serve.py
```

En una segunda terminal:

```sh
python3 -m venv .artifacts/qa-env
.artifacts/qa-env/bin/pip install -r tests/requirements-qa.txt
python3 scripts/fetch-qa-assets.py
.artifacts/qa-env/bin/python tests/browser_qa.py
```

`fetch-qa-assets.py` descarga axe-core 4.10.3 del registro npm y verifica su SHA256. No se descarga ningún navegador. En otro sistema, indicar `KOODARIA_CHROME_PATH` con la ruta de Chrome. `KOODARIA_TEST_URL` permite indicar otro servidor de desarrollo equivalente. El runner inyecta axe mediante una ruta interceptada solo en el navegador de pruebas; no añade assets de QA al sitio ni relaja la CSP.

## Pendientes para la fase siguiente

Confirmar contacto y textos institucionales/legales, autorizar publicación y cambios de entrada, preparar pipeline y registro de imágenes, y ampliar revisión manual de accesibilidad. Enterprise, autenticación Keycloak, organización/roles y Workspace requieren su propia fase y no están habilitados.
