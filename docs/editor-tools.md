# Organización y colaboración del lienzo

- Selección rectangular: Ctrl + arrastrar. Selección adicional: Shift + clic o Cmd + clic.
- Alinear dos o más componentes del mismo contenedor; distribuir tres o más conservando los extremos. Los componentes bloqueados se excluyen. Evitar distribuir si produciría superposiciones.
- Guías magnéticas al arrastrar un componente: extremos y centros dentro de siete píxeles de pantalla. Alt suspende el ajuste. Los componentes alojados conservan la distribución derivada del contenedor.
- Plegar conserva todos los componentes y conexiones en PostgreSQL. Oculta descendientes y conexiones que los utilizan. El contador permite desplegar. No implica eliminar ni alterar el estándar.
- Bloqueo manual de posición: `data.positionLocked`, validado en las operaciones colaborativas; no impide editar identidad. Plegado: `data.collapsed`. Ambos son metadatos de presentación, no campos de un estándar.
- Comentarios: tabla `diagram_comments`, ancla por ID de nodo o conexión, autor, menciones a participantes existentes, estado resuelto y revisión optimista. Consulta paginada y actualización cada cuatro segundos. Permisos verificados en cada petición y mediante RLS. Las menciones se muestran dentro de la discusión; esta fase no envía correo.
- Los grupos admiten hasta 100000 unidades por lado, de forma coherente en importación, redimensionado y validación. El lienzo sigue teniendo límites técnicos: 200 componentes y 500 conexiones por documento. Eliminar el límite de 3000 no convierte la capacidad en infinita.
- Insertar un diagrama copia los componentes con nuevos IDs; el original es independiente. Trasladar también los puntos manuales de las conexiones al espacio del contenedor.

Pruebas: `scripts/qa_editor_tools.py` usa datos sintéticos en la base desechable; `app/test_collaboration.py` comprueba permisos, menciones, resolución concurrente y bloqueo persistente.
