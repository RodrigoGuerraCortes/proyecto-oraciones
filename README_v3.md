1. Estado general de v3

v3 es la versión activa del pipeline de generación de video, basada en:

Configuración centralizada en BD

Resolución de comportamiento vía config_resolver

Wrappers por formato semántico

Generadores genéricos por tipo estructural

Motor v1 encapsulado (sin refactor interno)

Actualmente v3 soporta short videos con dos tipos de contenido estructural.

2. Arquitectura v3 (visión rápida)
entrypoint
   ↓
wrapper (por formato)
   ↓
generador genérico (por tipo de contenido)
   ↓
adapters v3
   ↓
motor v1 encapsulado


Principio clave:

El entrypoint y los wrappers no conocen la implementación interna
El comportamiento se define por configuración, no por código

3. Tipos de contenido soportados
3.1 plain – Texto continuo

Usado para:

Oraciones

Mensajes devocionales

Textos cortos no segmentados

Generador genérico:

generator/v3/short/generar_short_plain_generico.py


Formato activo:

short_oracion

Características:

Texto completo en uno o más bloques

Duración calculada automáticamente

TTS opcional (ratio configurable)

Música de fondo

CTA final

3.2 stanzas – Estrofas / bloques semánticos

Usado para:

Salmos

Poemas

Himnos

Cualquier texto dividido en estrofas

Generador genérico:

generator/v3/short/generar_short_stanza_generico.py


Formato activo:

short_salmo

Características:

Texto dividido por estrofas (separadas por líneas en blanco)

Un bloque visual por estrofa

Duración fija por bloque (seconds_per_block)

Máximo de bloques configurable (max_blocks)

TTS por bloques (modo blocks)

Música de fondo

CTA final

El generador no conoce el dominio (salmo).
Solo interpreta content.type = stanzas.

4. Wrappers disponibles

Los wrappers encapsulan:

Resolución de config

Resolución de paths

Generación de video_id

Llamada al generador genérico correspondiente

4.1 Oración
generator/v3/wrappers/generar_oracion.py


Usa generar_short_plain_generico

Formato: short_oracion

4.2 Salmo
generator/v3/wrappers/generar_salmo.py


Usa generar_short_stanza_generico

Formato: short_salmo

5. Entrypoint v3

Archivo:

generator/v3/entrypoint.py


Responsabilidad:

Parsear argumentos CLI

Enrutar por format

Invocar el wrapper correspondiente

El entrypoint:

❌ No conoce plain ni stanzas

❌ No conoce config interna

❌ No conoce lógica de audio o render

6. Configuración por formato (BD)

Cada formato define completamente su comportamiento:

formats.<format_code> = {
  content: { ... },
  audio: { ... },
  layout: { ... },
  cta: { ... }
}


Ejemplos activos:

short_oracion → content.type = plain

short_salmo → content.type = stanzas

Agregar un nuevo formato no requiere tocar el core.

7. Estado del soporte LONG (pendiente)

Los videos long (ej. oración guiada) aún usan v1 directamente.

Archivo base:

generator/generar_oracion_long.py


Migración a v3:

❌ No iniciada

⏳ Planificada una vez estabilizado shorts en producción

8. Estado actual del sistema (resumen)
Componente	Estado
short_oracion	✅ Migrado a v3
short_salmo	✅ Migrado a v3
generadores genéricos	✅ plain / stanzas
wrappers	✅
entrypoint	✅
scheduler	⏳ pendiente
long videos	⏳ pendiente
9. Principio rector de v3

Nunca refactorizar el motor v1.
Toda evolución ocurre en:

config

wrappers

generadores genéricos

10. Próximo hito técnico

Ejecutar short_salmo en modo completo (no test)

Validar persistencia y fingerprint

Congelar v3 (shorts)

Luego migrar scheduler