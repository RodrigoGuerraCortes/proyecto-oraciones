 📌 Automated Catholic Video Publishing System

**Status:** Scheduler, Publishing Workers & Cron Automation — **COMPLETE and VALIDATED**  
**Date:** December 2025

---

## 1. Overview

This project implements a **production-grade, scalable and idempotent automation platform** for generating, scheduling, and publishing Catholic video content (Prayers and Psalms) across multiple social platforms.

The system covers the full lifecycle:
- Video generation
- Editorial scheduling
- Platform-specific publishing
- Failure handling and retries
- Sandbox and production API compliance

It is designed to be:
- Safe to re-run daily
- Legacy-compatible
- Platform-aware
- Ready for horizontal scaling (VPS / workers)

---

## 2. Supported Content

### Video Types
- `oracion` (Prayer)
- `salmo` (Psalm)

### Editorial Generation Flow (OSO)
```
Oración → Salmo → Oración
```

Each generated video:
- Has a UUID as primary identifier
- Uses a unique filename format:
```
{uuid_short}__{slug}.mp4
```
- Is stored once as **editorial inventory**
- Can be reused across platforms under exposure rules

---

## 3. Architecture Summary

### Core Tables

#### `videos` — Editorial Inventory
Source of truth for all publishable content.

Key fields:
- `id`
- `channel_id`
- `tipo`
- `archivo`
- `texto_base`
- `fecha_generado`

Videos are **never deleted nor consumed**.  
They are reused under editorial and platform constraints.

---

#### `platform_schedules`
Defines **daily publishing capacity per platform**.

Examples:
- YouTube → 3 slots/day
- Facebook → 2 slots/day
- Instagram → 2 slots/day
- TikTok → 2 slots/day

Each row represents a valid publishing slot.

---

#### `publications`
Final publication agenda.

States:
- `scheduled`
- `publishing`
- `published`
- `failed`

Only **live states** block capacity:
```
scheduled, publishing, published
```

---

## 4. Scheduler Logic

The scheduler:
1. Reads platform schedules
2. Calculates daily capacity per platform
3. Reads editorial inventory
4. For each day and platform:
   - Counts legacy and current publications
   - Avoids slot collisions
   - Applies editorial exposure rules
   - Creates only missing publications

---

## 5. Editorial Exposure Rules

| Platform   | Window | Max repetitions |
|-----------|--------|-----------------|
| YouTube   | 60 days | 1               |
| Facebook  | 30 days | 3               |
| Instagram | 30 days | 3               |
| TikTok    | 7 days  | Unlimited       |

---

## 6. Platform Publishers

Implemented publishers:
- YouTube Shorts
- Facebook Reels
- Instagram Reels (cron-based)
- TikTok Sandbox (API validated)

Each publisher supports:
- Dry-run
- Forced execution
- Error rollback
- External ID persistence

---

## 7. Cron Automation (Instagram)

Instagram publishing uses controlled execution windows:

```
12:00–13:00
20:00–21:00
```

Executed via cron to avoid constant polling.

---

## 8. TikTok Sandbox Notes

- Sandbox uploads return valid publish IDs
- Push notifications are delivered
- Videos do NOT appear in drafts or feed
- This is expected behavior per TikTok documentation

Sandbox is used exclusively for:
- API validation
- App review
- End-to-end demo recording

---

## 9. Current Status

### Completed
- Generation pipeline
- Scheduler
- Publishers
- Cron automation
- TikTok Sandbox integration
- Logging & observability

### Next
- TikTok Production approval
- VPS deployment
- Horizontal scaling

---

## 10. Conclusion

This system is a **production-ready editorial automation platform**:
- Deterministic
- Idempotent
- Platform-compliant
- Scalable



▶️ Publicar videos en YouTube (worker de publicación)
.venv/bin/python -m generator.cli.publish_youtube

Variantes útiles
🔍 Modo simulación (no publica, solo muestra qué haría)
.venv/bin/python -m generator.cli.publish_youtube --dry-run

🕒 Forzar publicación inmediata (ignora publish_at)
.venv/bin/python -m generator.cli.publish_youtube --force-now

Flujo completo típico (recordatorio mental)
# 1) Generar videos
.venv/bin/python -m generator.entrypoint 1 oso

# 1) Generar video long
.venv/bin/python -m generator.entrypoint 1 long

# 2) Crear publicaciones (scheduler)
.venv/bin/python -m generator.publications.run_scheduler

# 3) Publicar en YouTube
.venv/bin/python -m generator.cli.publish_youtube

# 4) Fijar comentario (bot)
.venv/bin/python -m generator.bots.pin_comments.worker


# Ejecución de test para version 2
.venv/bin/pytest


PYTHONPATH=. .venv/bin/pytest generator/v3/long/test_runner.py::test_runner



