# Koodaria · Home pública / Fase 1

Implementación propia de la Home de Koodaria. El ZIP recibido es **solo una referencia**, se conserva intacto y no se incorpora al sitio ni al historial. El Login público está conectado a Keycloak mediante `login.koodaria.com`, con contraseña y 2FA obligatorio. Incluye un catálogo privado y un editor inicial para documentar servicios mediante diagramas. Enterprise, cursos y ejecución de laboratorios siguen fuera del alcance actual.

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

El terminal es una demostración animada, sin ejecución real. Se repite automáticamente, se pausa al enfocar el terminal y respeta la preferencia de movimiento reducido. Enterprise es una sección informativa con un flujo futuro; `/enterprise` y `/workspace` devuelven 404. En producción, `/login/` inicia el acceso mediante Keycloak y termina en `/bienvenida/`. La primera autenticación exige vincular una aplicación autenticadora; las siguientes exigen contraseña y TOTP. Las contraseñas se introducen únicamente en Keycloak. La Home no guarda credenciales ni tokens. En el servidor local, la página de Login ofrece un enlace al servicio publicado. El canal de contacto aún debe confirmarse.

## Vista de la implementación

[Escritorio](docs/evidence/desktop.png) · [Móvil](docs/evidence/mobile.png)

## Podman y publicación

Ver [inspección y arquitectura](docs/architecture.md), [despliegue y rollback](docs/deployment.md) y [validación](docs/validation.md).

La Home está publicada en **https://koodaria.com**, con certificado gratuito de Let’s Encrypt, renovación automática de Caddy, redirección HTTP→HTTPS y `www`→dominio canónico. Se conservan el laboratorio y Keycloak. El contenedor de desarrollo sigue aislado. El acceso por IP continúa disponible como entrada HTTP transitoria; la URL recomendada es siempre HTTPS. Véase [publicación](docs/publication.md).

## Identidad

Realm independiente `koodaria`, temas propios en `infra/keycloak/themes/koodaria`. Existen `Kyndryl` y `Koodaria`; esta última contiene la cuenta propietaria. Cada empresa cliente tiene su organización; el buzón SMTP es global e independiente. El dominio del correo no concede membresía automáticamente. El destino tras autenticar es el catálogo privado de disciplinas, con Servicios/Módulos y menú personal. Observabilidad reúne Diagramas, cursos por nivel y casos de uso. Diagramas abre una biblioteca única con Mis diagramas / Compartidos conmigo, grupos e invitaciones. Puedes comenzar en blanco o con una de cinco plantillas, añadir componentes desde un panel flotante por categorías y editarlos en React Flow. El guardado es automático en PostgreSQL y la descarga es PDF. Los enlaces antiguos de mapeo abren esta misma biblioteca. Los demás contenidos están identificados como En preparación. La gestión de cuenta sigue disponible desde ese menú. Los invitados externos solo pueden utilizar Observabilidad > Diagramas y editar los diagramas compartidos explícitamente, sin crear otros. La organización no concede acceso implícito a diagramas. Las invitaciones verifican correo, perfil, contraseña y MFA; la recuperación de contraseña no elimina el segundo factor.

`scripts/provision_keycloak.py` y `scripts/configure_keycloak.py` validan sin cambios por defecto. La aplicación requiere `--apply --credentials-file RUTA`, con una cuenta de servicio autorizada y archivo privado 600. No hay credenciales administrativas activas en el repositorio. La prueba `tests/keycloak_live_qa.py --credentials-file RUTA` usa Playwright y crea/elimina una cuenta desechable; debe ejecutarse solo con autorización administrativa.

## Catálogo de componentes y estándares

El inicio autenticado muestra **Tu espacio de trabajo**, con una tarjeta y un
icono por área. Estándares y Diagramas comparten `component-catalog.json`:
12 categorías y 110 tipos de componente, más tres elementos de organización
visual exclusivos del editor. Proveedor y tecnología son atributos y filtros,
sin duplicar un tipo por cada fabricante. Se conservan los identificadores de
los recursos y plantillas anteriores.

El árbol permite recorrer categorías, familias y tipos. Cada tipo expone
Identificación de entidad, Capacidades y controles, Evidencia operativa y
Relaciones de arquitectura. Bases de datos incluye conexiones y consultas,
bloqueos, replicación, protección y capacidad en sus controles. Los valores
reales se documentan en el recurso; completar una referencia no demuestra
cumplimiento ni instala agentes.

Las referencias nuevas son un catálogo compartido de consulta. Agregar campo
continúa como vista previa temporal, sin persistencia. Las definiciones y
publicaciones existentes de Linux/Windows se conservan en PostgreSQL; los
accesos Definiciones y Criterios siguen retirados por decisión del usuario.
Sus versiones ligadas a diagramas no cambian retroactivamente. Los invitados
solo pueden editar mapas compartidos explícitamente; no acceden al catálogo
privado de estándares ni pueden crear diagramas nuevos.

El editor usa los mismos componentes y permite guardar proveedor, tecnología
/ versión y ubicación / región junto a cada nodo, en el documento JSONB.
El servidor valida estos campos y los conserva cuando un cliente antiguo los
omite. El guardado online, los grupos y la descarga PDF se mantienen.

### Instancias de servidor en el diagrama

Servidor físico y Máquina virtual muestran cuatro bloques del modelo de
Estándares. Una fila de cuatro iconos abre la captura por bloque. El nombre de cada
sección aparece al pasar el mouse o enfocar el icono con el teclado. Los valores de identificación, evidencia y relaciones,
y los estados declarados de los controles se guardan con el diagrama en
PostgreSQL (`server_instance`, dentro del documento JSONB). No modifican la
política ni crean una nueva definición.

El servidor asigna `resource_schema` desde el modelo compartido y registra la
versión estructural en cada nodo; ignora esquemas enviados por el navegador. Si hay una
única publicación compatible se vincula al añadir el servidor. Sin ella se
utiliza la estructura base de Servidores, sin inventar una política publicada.
La selección de una publicación sigue disponible en Propiedades. Los clientes
anteriores que omiten los datos de instancia no los borran al guardar.

Los cuatro bloques abren el mismo panel flotante compacto junto al nodo. El encuadre reserva
espacio para el nodo sin mover sus coordenadas; al cerrar se restaura la vista.
Los campos se paginan según el tamaño del panel. Hay guardado automático,
acción Guardar y marca decorativa «sync» solo tras confirmar el guardado.
Los conectores norte/sur conservan sus anclajes al guardar y reabrir el mapa.

Ambiente y Criticidad son campos independientes del modelo canónico (v2). El
campo combinado anterior se elimina del documento activo; queda únicamente
en el backup previo al ajuste. Las reglas de
ese campo en borradores anteriores se adaptan a los dos campos nuevos, sin
modificar publicaciones históricas. La tabla de Estándares y el inspector usan
las mismas etiquetas y conjuntos de campos. Los campos añadidos en la vista
previa de Estándares siguen siendo temporales.

Al seleccionar una conexión, Propiedades permite elegir Recta, Curva, Esquinas
redondeadas o Ángulos rectos. El trazo se conserva en el documento online. La
marca de la esquina del lienzo se oculta con la opción documentada
[`proOptions.hideAttribution`](https://reactflow.dev/api-reference/types/pro-options);
los avisos MIT de la dependencia permanecen en el código distribuido.

### Documentación y componentes alojados

El mapa muestra un estado documental discreto por recurso y tonos suaves según
la profundidad de anidación. Solo el recurso seleccionado muestra la cinta de
cuatro accesos junto al nombre. La cinta abre su resumen; cada sección del resumen
abre sus campos canónicos. «Comparar recursos» (o «Cobertura» en la barra) abre
la matriz del diagrama con búsqueda y paginación. Una celda abre la sección del
recurso correspondiente; cada fila se calcula contra su propio estándar.

El semáforo y los conteos describen documentación, no salud del servicio.
El guardado sigue aceptando borradores incompletos. Un control requiere un
estado declarado y evidencia para completar su documentación.

El botón + de cada nodo añade un componente dentro de su caja. El recurso
conserva su identificador y sus propios cuatro bloques, incluso en varios niveles. La
relación «Aloja / ejecuta» se guarda en el mismo grafo. Relaciones de arquitectura
permite vincular recursos existentes y agregar dependencias sin duplicarlos.
Servicio personalizado está en Aplicaciones e integración / Componentes
personalizados, con cuatro campos de identidad como punto de partida.

Al quitar una relación o eliminar el host, los componentes alojados se conservan.
Se impiden ciclos de alojamiento y un segundo host principal, mientras las
relaciones de dependencia admiten varios recursos. Diseño, reglas y próximos
casos: [composición](docs/roadmap/composition.md).
