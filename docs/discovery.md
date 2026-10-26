# Descubrimiento y conciliación · primera entrega

Ruta: Observabilidad → Operación → Descubrimiento y conciliación.
Operación es el filtro inicial; Capacitación, Casos de uso y Todo son explícitos.
El inicio mantiene siete áreas; los paradigmas adicionales siguen previstos dentro
de sus áreas, sin anunciar capacidades inexistentes. Topología abre la misma
biblioteca de diagramas que el acceso anterior desde Gobierno.

Datadog es el único conector habilitado. Nagios, Tanium, ServiceNow, InvGate y
Device42 se muestran como próximos. Conciliación todavía es una vista informativa:
no combina registros ni modifica estándares o diagramas.

## Contrato y datos

`006_discovery_connections.sql` crea conexiones, estado de prueba y muestra en
PostgreSQL. RLS forzado deriva el alcance de `component_model_scope()`:
organización del miembro o su identidad si aún no tiene organización. Invitados
externos no pueden listar, crear ni usar conectores. Todos los miembros del mismo
alcance comparten las conexiones; no se añade un rol de administrador nuevo.

Las dos claves se cifran con Fernet usando `DISCOVERY_ENCRYPTION_KEY`, una clave
independiente del secreto de sesión, fuera del repositorio y persistente entre
reinicios. El API nunca devuelve claves ni ciphertext. No se registran secretos,
cuerpos de respuesta ni cabeceras del proveedor en el catálogo de errores.
Reemplazar una clave o el sitio invalida la comprobación anterior. Omitir las
claves al editar conserva las guardadas. La revisión evita sobrescribir cambios
concurrentes. Eliminar requiere confirmación y borra conexión, claves y muestra.

La clave de cifrado debe conservarse mediante un respaldo privado separado de la
base. No regenerarla al desplegar: las credenciales existentes no serían legibles.
La rotación con múltiples claves y el traslado entre organizaciones quedan para
una entrega posterior; no se hace fallback a texto plano.

## Prueba por etapas

1. Conectividad HTTPS contra el sitio permitido, sin enviar credenciales.
2. Validación de API Key mediante `/api/v1/validate`.
3. Permiso efectivo de API Key + Application Key para lectura de hosts.
4. Consulta de hasta 25 hosts y sus etiquetas, con metadata de plataforma.

La segunda etapa no demuestra por sí sola que la Application Key sea válida; la
tercera comprueba el acceso real. API de referencia:
[autenticación](https://docs.datadoghq.com/api/latest/authentication/) y
[hosts](https://docs.datadoghq.com/api/latest/hosts/).

Los endpoints se construyen exclusivamente desde la lista de sitios oficiales.
No se aceptan URLs arbitrarias, redirecciones ni proxies de entorno. Timeout de
conexión 3 s / lectura 6 s, respuesta máxima 1 MB y duración de lectura acotada.
Se distinguen credenciales, permisos, red, límite del proveedor y respuesta inválida
con códigos KOD-CON-001…008. Iniciar otra prueba tiene espera mínima de 5 s.
Cada etapa confirma un run ID y su posición, con bloqueo de fila; un cliente no
puede saltar etapas ni confirmar una conexión sin verificación completa.

Detener la prueba no revierte consultas ya ejecutadas; cancela la continuación,
invalida el run y conserva el registro como borrador. Guardar conexión confirma
su disponibilidad, sin escribir en Datadog. El proveedor se consulta solo por GET.
La muestra conserva ID externo, nombre, plataforma, etiquetas y fuente, junto con
fecha y total reportado; no es un inventario completo ni una sincronización.

## Límites deliberados

- 50 conexiones por alcance; muestras de 25 hosts, sin importación automática.
- Sin programación periódica, descubrimiento de servicios/APM ni reconciliación.
- Sin credenciales reales de Datadog en las pruebas: contratos HTTP simulados y
  recorrido de navegador con proveedor sintético en harness externo a la imagen.
- La comprobación contra la cuenta del cliente comienza cuando introduce sus
  claves en la aplicación; no se presupone éxito con un proveedor real.
- La organización es una frontera de acceso. Invitados de diagramas no obtienen
  acceso a conectores, muestras ni claves.

## Diagnóstico de conexión

Cada etapa conserva endpoint GET, servidor API, código HTTP, duración total de
etapa, tiempo hasta recibir cabeceras y tamaño del cuerpo consultado. El tiempo
se mide desde el servidor Koodaria; no representa latencia del navegador ni RTT.
Las etapas comprueban HTTPS con certificado válido y, cuando hay autenticación,
Content-Type JSON, objeto JSON y el contrato mínimo de la respuesta.

Solo se conservan los nombres de las cabeceras de solicitud, nunca sus valores.
De respuesta se admiten Content-Type normalizado y límites numéricos conocidos
X-RateLimit/Retry-After. Cookies y cabeceras arbitrarias quedan excluidas.
La etapa sin credenciales puede recibir 401/403 y confirmar conectividad; las
etapas autenticadas rechazan esos códigos. Permisos requiere host_list válido.

El fondo de puntos pertenece únicamente al recorrido de comprobación. La etapa
activa pulsa y el enlace entrante anima un paquete mientras espera la respuesta;
no hay progreso simulado ni afirmaciones sobre distancia o saltos de red. Se
respeta prefers-reduced-motion. El detalle se pliega inicialmente en móvil y
pantallas bajas. Pruebas anteriores requieren ejecutarse de nuevo para obtener
estos diagnósticos. Se guardan en stages JSONB sin migración adicional.

## Exploración de APIs e integración con Diagramas

Tras comprobar las credenciales, «Identificar APIs disponibles» ejecuta una
consulta mínima y secuencial por cada endpoint del catálogo. Un resultado vacío
válido también confirma acceso. 401/403 se registra como «Sin permiso»; 404/405/410
como «No disponible»; red, contrato inválido y límites como «No comprobada». Un
429 detiene el recorrido; no se presenta como falta de permisos. El catálogo es
una selección explícita, no una enumeración de todas las APIs o scopes Datadog.

| Familia | GET consultado | Datos y paginación |
| --- | --- | --- |
| Hosts | `/api/v1/hosts` | Hosts y metadata, offset/count, búsqueda remota por filtro |
| Monitores y alertas | `/api/v1/monitor` | Configuración, estados y mensajes, page/page_size |
| Dashboards | `/api/v1/dashboard` | Resúmenes, start/count; no incluye widgets |
| Logs | `/api/v2/logs/events` | Últimos 15 minutos, cursor y consulta remota |
| Eventos | `/api/v2/events` | Últimos 15 minutos, cursor y consulta remota |
| Personas | `/api/v2/users` | Usuarios, page[number]/page[size] y filtro |
| Catálogo de servicios | `/api/v2/services/definitions` | Definiciones, paginación por número |
| APM · trazas | `/api/v2/spans/events` | Spans indexados de 15 minutos, cursor y consulta |

Los campos y parámetros se contrastaron con el cliente oficial de Datadog:
[API v1](https://github.com/DataDog/datadog-api-client-python/tree/master/src/datadog_api_client/v1/api),
[API v2](https://github.com/DataDog/datadog-api-client-python/tree/master/src/datadog_api_client/v2/api).
La autorización corresponde únicamente al endpoint probado. Monitores incluye
sus mensajes de notificación, no una comprobación de todos los canales de envío.

La migración 007 guarda estado, diagnóstico y fecha por conexión/familia, con
RLS de organización y FK compuesta que impide asociar otro alcance. Cambiar la
conexión elimina estas comprobaciones. Las consultas de recursos vuelven a usar
las credenciales en servidor; los datos completos del registro se entregan solo
a miembros autorizados de ese alcance, sin persistir un nuevo inventario. Los
usuarios invitados a diagramas siguen excluidos. No se solicita gestionar claves
ni permisos administrativos de Datadog para identificar capacidades.

Un rechazo al consultar hosts ya no impide explorar otras APIs cuando la etapa
de credenciales fue satisfactoria. La fase de muestra anterior puede seguir
mostrando fallo de hosts: no se convierte en un éxito ficticio.

Diagramas abre «Integraciones / conciliaciones» sin abandonar ni modificar el
grafo. Dos paneles de igual ancho presentan consultas y registros; móvil cambia
entre APIs/Datos. Se pagina por 5 registros, o 2 en pantallas bajas, hasta recorrer
los resultados disponibles. Hosts usa la ventana predeterminada de Datadog
(2 horas recientes); no promete todos los activos históricos o apagados. El
registro seleccionado muestra íntegramente los campos devueltos por ese
endpoint, no atributos inexistentes o de otras APIs. No hay importación ni
conciliación automática en esta fase.

Las propiedades del diagrama se abren con doble clic en su título, o Enter con
el título enfocado. Los inspectores de recursos y conexiones conservan su alcance.

## Catálogo global oficial de Datadog (sustituye la selección inicial de ocho)

El registro precargado `app/datadog-api-catalog.json` se genera a partir de las
especificaciones OpenAPI v1/v2 del repositorio oficial DataDog, fijadas a revisión
`32a2d897ebc958ab96471b33eab58c2463675e50`. Incluye las 1.922 operaciones HTTP,
1.217 rutas y 166 familias presentes en esas fuentes, incluidas las marcadas
Preview/deprecated. Cada operación conserva método, ruta, familia, versión,
parámetros, permisos declarados, enlace documental y clasificación de prueba.
Los hashes SHA-256 y URLs exactas de las fuentes se guardan en el archivo.

Este catálogo es global, versionado e idéntico para todos los clientes. No se
copia ni se modifica al guardar una conexión. PostgreSQL conserva únicamente los
resultados por conexión/organización en `discovery_capabilities`. Los resultados
se aceptan solo si su revisión de catálogo coincide con la actual; una nueva
revisión exige volver a comprobar, sin borrar las evidencias anteriores.

En esta revisión:

- 163 consultas GET se pueden comprobar automáticamente sin identificadores.
- 240 consultas GET requieren parámetros; la ficha permite introducirlos y
  comprobar la operación concreta. El permiso queda asociado a los valores
  comprobados, no a todos los recursos posibles.
- 1.105 operaciones de otros métodos quedan documentadas y no se ejecutan.
  Incluye POST de búsqueda: no se asume que todo POST modifique datos, pero
  requiere un adaptador de lectura explícito antes de habilitarlo.
- 243 operaciones Preview, 112 sensibles o con autenticación incompatible y 59
  con formatos/servidores especiales se catalogan sin probar automáticamente.
  Nunca se confunden con accesos denegados por Datadog.

El usuario puede buscar por ruta/nombre, filtrar familia, mostrar todo o solo
consultas automáticas/confirmadas. El barrido aplica al filtro actual, es
secuencial, cancelable, con pausa breve entre peticiones y detención ante 429.
Los métodos de escritura se rechazan también en servidor; no basta ocultarlos
en la interfaz. No se consultan gestores de claves, tokens, credenciales ni
operaciones sensibles para inferir permisos. Los scopes publicados son una
referencia y no se usan para declarar autorizado un endpoint sin comprobarlo.

Los ocho adaptadores anteriores conservan sus IDs y búsqueda/paginación. Otros
GET usan parámetros de paginación publicados y una representación JSON genérica
para listas y objetos; el detalle conserva el registro devuelto. El límite de
respuesta sigue siendo 1 MB. Contratos, errores o formatos no compatibles quedan
sin confirmar, no como "sin permiso". No se promete ejecutar todas las operaciones
publicadas ni inferir permisos de escritura sin invocarlas.

Actualización reproducible, sin credenciales:

```
.artifacts/qa-env/bin/python scripts/update_datadog_catalog.py --revision <SHA oficial de 40 caracteres>
```

Requiere PyYAML 6.0.2 en el entorno de mantenimiento. El script usa el contenido
cacheado solo si coincide la revisión y registra sus hashes. Revisar el diff y
las clasificaciones antes de desplegar una nueva instantánea. No existe una
actualización automática que cambie rutas de proveedores en producción.

### Progressive result exploration

The explorer presents a narrow official catalog, paginated results and a selected
record summary. Host summaries use only returned identity, OS, CPU, agent, tags,
applications and status fields; opaque metadata stays in the original JSON view.
Other operations use common fields or a bounded scalar fallback. No provider
record is modified and missing properties are not inferred.

“Datos crudos” reveals a fourth pane while the catalog moves out of view and
becomes inert. Results and selection remain in place without another API request.
Mobile uses APIs / Results / Summary / JSON navigation. Reduced-motion preferences
disable the slide. No schema, stored credential or authorization changes.

Catalog entries are now single full-row buttons (including route/check details).
Selection uses a single border and an inset keyboard focus indicator. Catalog
pagination measures the space left below its filters; short landscape layouts
collapse filters into an expandable section. Long summaries paginate fields.
Original JSON uses smaller monospace text and a modal expand/restore action.

Host enrichment displays provider-reported EC2 ID, cluster/node tags and detected
Kubernetes/runtime applications when present. It does not classify a host as a
container from its installed integrations, nor infer physical/virtual/hypervisor
status from its name or CPU. Reference:
https://docs.datadoghq.com/api/latest/hosts/get-all-hosts-for-your-organization/
and https://docs.datadoghq.com/containers/kubernetes/tag/.

### Workspace composition and measured pagination

The explorer uses one context header for title/catalog counts, connection and
scan/close controls. Until a record is selected, the workspace has two useful
panes (catalog and results); selection reveals the summary. JSON keeps the
existing results/summary/raw progression. Search input and action share a baseline.

`explorer-layout.js` observes the actual list and viewport bounds. Each panel
reserves its own controls and footer, then computes the rows that fit (results
remain bounded by the API's 25-record maximum). Loading messages do not alter
list geometry. Footers keep their height during requests to avoid oscillating
capacity/refetch loops. Viewport changes may change the requested page size and
reset pagination, but opening a record preserves its detail. Long technical
content and accessibility zoom retain a scroll fallback rather than clipping.
