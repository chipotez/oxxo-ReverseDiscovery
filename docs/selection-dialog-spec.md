# Modales de selección de Koodaria

Los nuevos selectores jerárquicos deben reutilizar `app/frontend/src/selection-dialog.jsx` y los estilos `selection-dialog` de `resource-flow.css`. No copiar su estructura ni introducir dimensiones independientes en cada pantalla.

## Estructura

Cabecera con título, contexto y cierre accesible; cuerpo flexible; pie fijo con acción secundaria y primaria. Selección y revisión conservan el mismo marco. La variante amplia mide hasta 1080 × 680 px, limitada por el viewport con 16 px de margen; la compacta tiene un ancho máximo de 520 px. Usar tokens forest, sage, superficie y texto del tema. Bordes finos, radio de 22 px y sombra suave. La selección tiene un único borde forest; el foco de teclado permanece visible.

## Clasificación

Tres paneles: Familia → Subfamilia → Subtipo. Estos nombres corresponden a category, subcategory y kind del catálogo existente; no crean otra jerarquía de datos. Cada opción muestra nombre y descripción o ejemplos. Mostrar la ruta actual y la propuesta. Cambiar familia limpia subfamilia y subtipo; cambiar subfamilia limpia subtipo. No seleccionar automáticamente el primer descendiente.

Revisar cambio carga el modelo del estándar y presenta campos incompatibles antes de confirmar. Cancelar no modifica el recurso. Confirmar conserva ID, conexiones, componentes alojados y datos compatibles; los valores incompatibles requieren revisión explícita. El selector no sustituye las validaciones del servidor.

## Adaptación y accesibilidad

En escritorio se ven tres columnas. En móvil se apilan los tres paneles, conservando su orden y etiquetas. Las listas paginan según la altura disponible. Los botones del pie deben permanecer accesibles. A zoom elevado se permite desplazamiento como alternativa; nunca recortar validaciones o aplicar CSS zoom.

Usar dialog nativo con nombre accesible, foco contenido, Escape para cancelar y restauración del foco al cerrar. Opciones mediante botones con aria-pressed; Enter y Espacio seleccionan. Indicar estados vacíos, carga y acciones deshabilitadas. La X es útil en selectores extensos; en confirmaciones cortas con Cancelar puede omitirse para evitar redundancia.

## Validación

Comprobar escritorio, tablet, móvil y paisaje de poca altura, temas claro y oscuro; medir overflow real y visibilidad de acciones. Verificar limpieza de descendientes, selección actual, cancelación sin escritura y confirmación con preservación de identificadores. Usar datos sintéticos en pruebas y capturas.
