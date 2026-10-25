# Composición y documentación de recursos

## Comportamiento actual

Los cuatro bloques del estándar se mantienen. Definen los datos y relaciones
que documenta una instancia; el grafo registra las relaciones concretas.

- Identificación, capacidades y evidencia se guardan por componente. La lista
  de campos procede del mismo modelo que utiliza Estándares.
- Relaciones de arquitectura permite vincular recursos existentes y registrar
  notas o justificación por relación definida en el estándar.
- `hosts`: origen aloja/ejecuta destino. Un destino tiene un alojamiento
  principal. Se prohíben autorreferencias, ciclos y múltiples hosts principales.
- `depends`, `connected`, `storage`, `managed`, `used` y `belongs` describen
  dependencias, conectividad, consumo, gestión, uso y pertenencia lógica.
  Las dependencias admiten varios orígenes/destinos, incluso ciclos reales.
  «Forma parte de» refleja también el host de un recurso y «Utilizado por»
  refleja sus dependientes, sin almacenar vínculos inversos duplicados.
- Los componentes alojados se muestran dentro de su contenedor, en varios
  niveles. Seleccionar uno edita su nodo independiente; no duplica el recurso.
- Añadir desde el botón + del contenedor crea el recurso y `hosts`. Quitar una
  relación conserva ambos recursos. Eliminar un host conserva sus alojados.
- Relaciones paralelas entre los mismos anclajes muestran un contador para
  evitar superponer etiquetas; cada relación conserva su identidad y tipo.
- Servicio personalizado es un tipo base en Aplicaciones e integración /
  Componentes personalizados: nombre, función, responsable y tecnología.
  No es todavía un diseñador de modelos personalizados por organización.

Todo usa el documento PostgreSQL existente, sus revisiones, auditoría de edición
y permisos del diagrama. Sin tablas nuevas, migración ni cambios de acceso.

## Indicadores documentales

Son derivados, no estados de salud ni verificación de cumplimiento. Una evidencia
que documenta un control pendiente puede completar su documentación.

- Rojo/exclamación: sin iniciar o avance menor al 50 %.
- Ámbar/semicírculo: desde 50 % y menor a 100 %.
- Verde/check: todos los campos requeridos documentados.
- El tooltip incluye cantidad y porcentaje. El color nunca es la única señal.

Una política publicada usa requisitos obligatorios y condicionales; recomendados
y no aplicables quedan fuera del denominador. Los condicionales cuentan hasta
que se documenten, incluida la justificación de no aplicación. Sin política,
cuentan los campos del modelo de referencia. Un control exige estado conocido
y evidencia. Un campo de texto vacío o un «No aplica» sin motivo no se completa.
Las relaciones estructuradas completan el campo correspondiente; las notas
permiten documentar no aplicación. El guardado automático conserva borradores
incompletos y sus conflictos siguen protegidos por revisión.

## Casos comprobados

VM que aloja una base de datos y un servicio personalizado FTP; identidad de
cada componente con su propio modelo; relaciones persistentes al reabrir;
varias dependencias; rechazo de ciclos de hosting y doble alojamiento;
conservación del componente cuando se elimina su host o se retira el vínculo.

## Evolución pendiente

1. Aplicabilidad condicional evaluada por ambiente, plataforma y criticidad;
   revisión explícita con requisitos antes de publicar, sin bloquear borradores.
2. Plegado de subgrafos, búsqueda de descendientes y filtros por relación.
   La etapa actual ya muestra las cajas dentro de su contenedor en varios niveles.
3. Distinguir servicio lógico, clúster e instancia desplegada: una instancia tiene
   un host principal; un servicio o clúster puede agrupar muchas instancias.
4. Diseñador de estándares personalizados por organización, versiones,
   publicación, migraciones y excepciones aprobadas. Los campos de vista previa
   de Estándares continúan sin persistencia hasta habilitar ese flujo.
5. Fuente, fecha, confianza, evidencia e historial por relación; inventario
   compartido entre diagramas con un identificador estable de componente.
6. Edición concurrente granular y resolución de conflictos; permisos por recurso
   si se introduce un inventario compartido. Actualmente se heredan del diagrama.
7. Reglas semánticas configurables: «se ejecuta en» frente a «forma parte de»;
   límites de tipos; detección de inconsistencias y validación automática.
8. Tratamiento de relaciones paralelas en PDF y exportación con más detalle.
   El PDF ya conserva la composición anidada y el inventario de conexiones.

## Segunda etapa: cajas anidadas

La relación `hosts` gobierna también la contención visual en React Flow.
El contenedor crece según los descendientes; cada componente interno mantiene
sus cuatro secciones, selección, edición y puntos de conexión. Los hijos siguen
una disposición automática, se desplazan junto al contenedor y no se arrastran
individualmente dentro de él. Se conservan coordenadas absolutas en el documento,
sin introducir una segunda jerarquía persistida que pueda contradecir `hosts`.
Eliminar el contenedor conserva sus componentes. El PDF refleja esa composición.

La documentación usa tres estados: rojo por debajo de 50% (incluido vacío),
amarillo desde 50% y verde completo; el símbolo mantiene la distinción sin
depender solo del color. La cabecera muestra tipo una vez, nombre y hasta tres
valores de contexto, priorizando los campos canónicos del estándar. IP/puerto
siguen siendo atributos del recurso del diagrama; no se presentan como evidencia
ni como controles. Los tipos de estándar conservan su esquema propio.

## Tercera etapa: navegación documental

1. Mapa: estado agregado del recurso, tonos por profundidad, cinta de cuatro
   secciones solo en el recurso seleccionado y junto a su nombre.
2. Resumen: cantidades por sección del recurso seleccionado y acceso a sus
   formularios. La apertura reserva espacio junto al nodo y permite volver al mapa.
3. Comparación: matriz de todos los recursos del diagrama, ordenada por jerarquía
   de alojamiento. Usa los mismos contadores que el resumen. Búsqueda, paginación
   ajustada al viewport y presentación de filas compactas en móvil. Cada celda
   abre los campos del recurso/sección exactos; «Volver al mapa» conserva el contexto.

Los formularios siguen usando el guardado existente en PostgreSQL. No hay nuevas
tablas ni permisos. Cada estándar conserva sus propios campos y denominadores;
compartir cuatro apartados no implica medir productos distintos con iguales requisitos.
Los colores y fracciones se derivan, no se persisten como un estado operativo.

## Puntos de conexión y densidad

Los anclajes se mantienen montados para conservar la geometría de las conexiones,
pero son transparentes y no interactivos mientras el recurso no está seleccionado.
Durante un arrastre de conexión, entrar en el recurso destino lo selecciona y
habilita sus anclajes; al terminar solo ese recurso conserva los puntos visibles.
Hacer clic en el lienzo limpia la selección. Las líneas guardadas siguen visibles.

Ancho base de 320 px, margen horizontal de anidación de 10 px y separación
vertical de 8 px. La altura base depende de las líneas de contexto realmente
visibles, sin repetir como subtítulo un tipo idéntico al nombre del recurso.
Se conserva el tamaño de la tipografía; no se usa zoom CSS para compactar.

## Revisión del contrato de datos y propiedades

- El botón «Diagrama» edita el documento. La conexión edita extremos, etiqueta y representación. Las relaciones
  de arquitectura se gestionan desde su sección explícita. El doble clic en un recurso abre únicamente las secciones
  de su esquema. Ya no hay un formulario paralelo de atributos ni selector de
  tipo sobre una instancia existente. El servidor también rechaza reutilizar
  un ID existente con otro tipo, evitando mezclar estándares o descartar datos.
- ID técnico del nodo/conexión y CI de inventario tienen propósitos distintos.
  El ID técnico es metadata persistente del grafo; CI es un dato del estándar.
  Al copiar un grafo se regeneran IDs técnicos y se remapean todos los extremos
  y grupos. Los CI documentados se conservan: copiar una vista no crea por sí
  mismo un nuevo activo físico en un inventario corporativo.
- `resource_diagrams.document` es un grafo JSONB guardado atómicamente en
  PostgreSQL, no un inventario independiente de activos. El servidor valida
  IDs únicos en el documento, extremos existentes, tipos, campos, alojamiento
  sin ciclos/segundo padre, revisión concurrente y autorización/RLS. Las
  dependencias admiten relaciones muchos-a-muchos. Los colores no alteran la
  semántica de esas relaciones ni representan salud operativa.
- `resource_standards` y `resource_standard_versions` guardan políticas y
  publicaciones. La taxonomía y las bases iniciales siguen siendo archivos compartidos.
  Los campos publicados viven ahora en `component_models` y
  `component_model_versions`; `resource_schema` se resuelve en el servidor,
  nunca se confía en un esquema arbitrario enviado por el navegador.
- «Agregar campo» publica una versión inmutable del modelo en PostgreSQL.
  El alcance se deriva de la organización del miembro autenticado (o su
  cuenta si todavía no tiene organización). Los invitados no publican modelos.
  Cada nodo conserva `model_ref.id/version`; actualizar campos es explícito,
  conservando valores compatibles. El servidor rechaza campos desconocidos,
  tipos incorrectos y cambiar un modelo existente por otro de distinto alcance.
  Un editor invitado puede rellenar el modelo fijado del diagrama compartido.
  Los campos opcionales no reducen el porcentaje de documentación; los obligatorios
  sí. Un número cero o un valor «No» son respuestas documentadas.
  Crear categorías/tipos nuevos o editar/eliminar campos publicados no está
  incluido: este primer registro permite añadir campos a los tipos actuales.
- No se crea una tabla por servidor o tipo. Si se decide reutilizar el mismo
  activo entre diagramas, hará falta un registro de recursos independiente y
  separar referencias al activo de su representación en cada diagrama. En la
  etapa actual cada diagrama conserva sus instancias; no se impone unicidad
  global de CI ni se fusionan recursos por hostname.

La prueba de persistencia confirma extremos/IDs y campos canónicos después de
cerrar y reabrir. Un guardado inválido no modifica la revisión ni reemplaza el
último documento válido. La exportación PDF aún no replica los estilos nuevos
ni todos los detalles de formularios: pendiente explícito, no validado por una
captura del editor. El motivo exacto del rechazo original del usuario tampoco
se atribuye a una causa sin contar con la solicitud que falló.

Se corrigió asimismo una discrepancia de metadata: `resource_schema` del servidor
incluía el bloque de controles con `fields: []`, aunque formulario/validación ya
consumían las 16 capacidades. El modelo autoritativo y el renderer ahora expanden
ese mismo catálogo; la metadata guardada refleja los campos realmente aceptados.
Las políticas publicadas mantienen su versión y exigencias; no se inventa una
nueva versión de política ni se sobrescriben estados declarados de controles.

## Conexiones, alojamiento y recuperación

Una línea dibujada representa «Conectado a». Editar su etiqueta, origen, destino
o estilo no cambia el alojamiento. «Aloja / ejecuta» sigue siendo una relación
explícita desde Relaciones de arquitectura o el botón de añadir dentro de un
recurso. No se desanidan automáticamente relaciones históricas que podrían ser
válidas; se pueden quitar desde esa sección. Los cuatro puertos tienen IDs
norte/sur/este/oeste; el avance de arrastre sigue al puntero, y el grafo guarda
los puertos elegidos, además de IDs y extremos de la conexión.

Deshacer/Rehacer conserva hasta 50 estados del documento en la pestaña actual;
Ctrl/⌘ Z, Ctrl/⌘ Shift Z y Ctrl Y. Los campos de texto conservan su deshacer nativo.
La navegación/selección no crea pasos; un nuevo cambio después de deshacer abre
una rama nueva. El resultado se guarda con el mismo control de revisión del grafo.
No es un historial durable entre sesiones ni una resolución de conflictos multiusuario.

El catálogo inicial de errores está en `app/frontend/src/error-catalog.json`,
compartido con el servidor y consultable en `/bienvenida/api/catalog/errors` con
sesión. Cada fallo API lleva `error_code`, `reference` y `action`; la misma
referencia aparece en logs estructurados sin valores de campos, tokens ni correos.
El diálogo permite copiar código/referencia y mantiene abierto el formulario.
Un error de validación no sobrescribe el último documento válido. Conflictos de
revisión requieren recuperar o guardar como copia; no se reintenta sobre datos ajenos.
