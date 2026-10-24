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
