# Colaboración temporal

El Home es `#/catalogo` («Tu espacio de trabajo»). Se elimina el acceso duplicado Aplicaciones. Asistente, Biblioteca, Aprendizaje, Favoritos y Consola quedan deshabilitados; Inicio, Estándares, Diagramas y los controles existentes de cuenta siguen disponibles.

El propietario abre Compartir → Enlace de una hora, define una contraseña de al menos 14 caracteres y copia el enlace. La URL se muestra solo al crearla: únicamente su SHA-256 se almacena. El secreto viaja en el fragmento de la URL (no se envía en la URL de las solicitudes ni en sus registros de acceso); el formulario lo envía por POST. La contraseña se almacena con scrypt, nunca en claro. La vigencia es una hora desde la creación, no desde cada visita. El propietario puede revocarlo y consultar participantes y horas de ingreso.

El visitante ingresa nombre, correo y contraseña en `/bienvenida/colaborar/#<token>`. Nombre y correo son declaraciones no verificadas: no constituyen prueba de identidad ni crean una cuenta Keycloak. La interfaz identifica explícitamente esa condición. La sesión de visitante queda en el servidor, ligada a la cookie HttpOnly, al UUID de visita y a un único diagrama. Se preserva cualquier sesión OIDC previa del navegador.

Cada operación comprueba cookie, CSRF, visita, diagrama, revocación y vencimiento; PostgreSQL RLS comprueba nuevamente el permiso. El visitante usa el mismo protocolo de colaboración, revisiones, conflictos, reservas por recurso y auditoría que los usuarios habituales. No accede a otros mapas, biblioteca, credenciales, integraciones, permisos ni edición de estándares. No puede eliminar el diagrama ni extender el enlace. Al revocar o vencer, el siguiente sondeo bloquea nuevas ediciones y el servidor rechaza cualquier operación posterior.

Tablas: `diagram_links`, `diagram_link_visits`, `diagram_link_attempts` (migración 010). Los participantes persisten con el diagrama para auditoría. El historial de operaciones registra el actor temporal y su nombre; visitas conserva su correo declarado. El enlace admite múltiples visitantes; no es de un solo uso. Los intentos fallidos tienen límite por enlace y origen de conexión; un ingreso válido limpia el contador. Se conserva el límite general de recursos y el resto de validaciones del editor.

La revocación impide consultas y cambios futuros; no retira información ya vista o descargada. Nunca se interpreta el correo declarado como permiso permanente.
