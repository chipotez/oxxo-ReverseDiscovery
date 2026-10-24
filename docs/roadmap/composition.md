# Composición y documentación de recursos

## Primera etapa implementada

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
- Los componentes alojados se muestran en una lista expandible de tres por
  página. Seleccionar uno enfoca su nodo independiente; no duplica el recurso.
- Añadir desde esa lista crea el recurso y la relación `hosts`. Quitar una
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

- Gris/círculo: sin iniciar o sin requisitos obligatorios.
- Rojo/exclamación: avance mayor que cero y menor al 50 %.
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
2. Contenedores visuales que expanden subgrafos, disposición de varios niveles,
   búsqueda de descendientes y filtros por relación. La etapa actual es una
   composición lógica con lista, no un lienzo recursivo dentro de cada caja.
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
8. Exportación visual de la composición expandida y tratamiento de relaciones
   paralelas en PDF. El PDF actual conserva nodos y conexiones como inventario.
