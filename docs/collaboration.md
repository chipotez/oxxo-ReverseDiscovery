# Colaboración de diagramas — primera versión

Cada pestaña mantiene un identificador efímero de cliente; cada lote de cambios
lleva un UUID de operación. PostgreSQL conserva el documento canónico, revisión,
operaciones, presencia y eliminaciones recuperables. La migración 008 es aditiva.
Los campos del estándar siguen ligados a una versión inmutable: publicar una
versión nueva no migra instancias existentes. La actualización requiere una acción
explícita en el resumen y confirmación; los valores se vuelven a validar.

## Contrato y transporte

- `POST /<id>/collaboration/sync`: presencia, permiso actual, reserva y documento
  solo si la revisión cambió. Consulta automática cada 1,8 segundos, sin WebSockets
  ni servicios externos en esta primera versión. No es edición offline.
- `POST /<id>/collaboration/operations`: lote atómico de precondiciones y valores
  por campo (arrays atómicos), validación de estándares y relaciones, confirmación
  después del commit. Reintentos con el mismo UUID no duplican efectos. Reutilizar
  un UUID con contenido distinto se rechaza.
- Las operaciones, reservas, escrituras antiguas, eliminación del mapa y cambios
  de permisos usan el mismo bloqueo transaccional por diagrama. Permisos/RLS se
  revisan con identidad verificada en cada petición. Una pestaña antigua no puede
  sobrescribir el documento durante una sesión colaborativa activa.
- Reserva por recurso seleccionado: renovación con presencia, caducidad de 20 s.
  Otro usuario puede leerlo pero no modificarlo ni eliminar sus padres. No se
  bloquea todo el mapa. La reserva es de recurso, no de campo, en esta versión.
- Al desconectar se pausa la edición. Los cambios pendientes permanecen en memoria
  de esa pestaña. Al reconectar se confirma la operación incierta o se reevalúan
  precondiciones contra el estado remoto; nunca se confirma solo por tener red.
- Ante conflictos se conservan los valores locales; el usuario puede esperar si
  existe una reserva o elegir explícitamente la versión compartida / guardar una
  copia si tiene permiso. Los conflictos de contenido no se fuerzan al reintentar.
- Deshacer/Rehacer registra solo operaciones locales y verifica precondiciones;
  conserva cambios independientes ajenos y rechaza deshacer un campo ya modificado
  por otra persona. No es un snapshot que sobrescribe todo el diagrama.

## Acceso, actividad y recuperación

El propietario puede cambiar un acceso activo a Solo lectura en Compartir.
El lector sigue recibiendo el mapa pero no puede enviar operaciones. La revocación
se rechaza en la siguiente petición y detiene recepción/edición (hasta el siguiente
ciclo de 1,8 s en la interfaz). No puede borrar información ya vista en un navegador.
El propietario conserva control de compartir y restaurar. La bitácora persistente
incluye actor, fecha, revisión, UUID y cambios antes/después. La interfaz muestra
actividad y sesiones, sin exponer los identificadores internos de otras cuentas.

La papelera conserva nodos y conexiones eliminadas. Restaurar requiere propiedad,
no encontrar colisiones de identificadores y no tener recursos afectados en edición. No se
recrean conexiones a extremos inexistentes. Se valida de nuevo el grafo completo.
Las filas se eliminan al borrar definitivamente el diagrama; no hay purga automática
ni límites de retención de operaciones todavía. Antes de habilitar grandes equipos
conviene definir retención, límites por organización y hacer pruebas de carga.

## Verificación

Pruebas de servidor sobre PostgreSQL desechable: permisos, versiones, precondiciones,
reservas, borrado de padres, restauración, idempotencia y atomicidad; regresión de
almacenamiento, modelos y compartir. Pruebas de navegador con propietario/invitado
en contextos aislados: cambios independientes, reserva, desconexión, degradación
a lector y revocación. Solo datos sintéticos. Ver `docs/evidence/collaboration-qa.json`.
