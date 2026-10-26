# Edición de conexiones y reutilización de componentes

Los recorridos ortogonales automáticos comparan rutas simples, respetan el lado del
puerto y penalizan atravesar recursos próximos. Se consideran hasta 32 obstáculos
cercanos por conexión para acotar el coste de renderizado. No es un enrutador global
que garantice eliminar todos los cruces en un grafo complejo.

Seleccionar una conexión muestra manejadores en los centros de sus tramos. Arrastrar
mueve ambos vértices del tramo; los extremos permanecen unidos. Al soltar se eliminan
puntos duplicados o colineales. Los recorridos manuales se guardan en `routePoints`
(0 = automático; de 2 a 64 puntos), dentro del documento PostgreSQL existente.
Las curvas conservan sus tres ajustes Bézier. Optimizar retira ajustes manuales y
recalcula rutas; puede deshacerse. Las rutas antiguas conservan compatibilidad.

Copiar/pegar usa el portapapeles explícito del navegador. Incluye descendientes y
conexiones internas; excluye conexiones hacia recursos no copiados. Renueva todos
los IDs y referencias internas. Respeta la edición nativa de campos de texto.
Pegar en otro diagrama requiere permisos y modelos visibles para esa cuenta.
No se almacena el contenido del portapapeles en localStorage.

Insertar crea una copia independiente agrupada de un diagrama accesible en la
biblioteca propia. Conserva grupos internos y relaciones; no crea vínculos vivos
hacia el original. Los grupos no pueden formar ciclos. Se mantienen los límites
actuales: 200 nodos, 500 conexiones y grupos de 3000 × 3000.

Cambiar clasificación reinicia Tipo/Subtipo al cambiar su categoría superior.
La vista previa pide confirmar valores incompatibles. Conserva ID, conexiones,
alojamiento y campos con igual identificador y formato; exige un modelo publicado
visible al usuario y permiso de miembro. La operación sustituye los datos del nodo
atómicamente: una edición concurrente incompatible provoca conflicto.

Los datos visibles antiguos (dirección, puerto, tecnología, proveedor, ubicación)
pueden incorporarse explícitamente a Identidad. Se publica una nueva versión del
modelo con los campos faltantes, se transfieren los valores y se limpian sus copias
antiguas. Los demás nodos siguen fijados a su versión anterior. Los controles son
capacidades del tipo de recurso; pueden cubrirse mediante agentes, APIs o mecanismos
nativos. La definición de cada campo sigue gobernada por su estándar.

Verificación: 81 pruebas de servidor, 9 recorridos de edición en navegador y
9 recorridos de regresión colaborativa. Los recorridos usan exclusivamente datos
sintéticos. Ver `docs/evidence/graph-editing-qa.json`.
