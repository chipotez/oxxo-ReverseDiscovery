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
