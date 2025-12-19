# 📌 Automated Catholic Video Publishing System

**Status:** Scheduler & Editorial Logic — **COMPLETE and VALIDATED**  
**Date:** December 2025

---

## 1. Overview

This project implements a **professional, scalable, and idempotent pipeline** for generating and scheduling Catholic video content (Prayers and Psalms) across multiple social platforms.

The system is designed to:
- Generate short Catholic videos automatically
- Prevent content repetition and SEO penalties
- Schedule publications per platform with different daily capacities
- Be **safe to re-run every day** (idempotent)
- Coexist with legacy publications without conflicts
- Scale to multiple channels and platforms

---

## 2. Supported Content

### Video Types
- `oracion` (Prayer)
- `salmo` (Psalm)

### Generation Flow (OSO)
```
Oración → Salmo → Oración
```

Each generated video:
- Has a UUID as primary identifier
- Uses a unique filename format:
```
{uuid_short}__{slug}.mp4
```
- Is stored once in the database as **editorial inventory**

---

## 3. Architecture Summary

### Core Tables

#### `videos` (Editorial Inventory)
Source of truth for all publishable content.

Key fields:
- `id`
- `channel_id`
- `tipo`
- `archivo`
- `texto_base`
- `fecha_generado`

Videos are **never consumed or deleted**, only reused under rules.

---

#### `platform_schedules`
Defines **daily publishing capacity per platform**.

Example:
- YouTube → 3 slots/day
- Facebook → 2 slots/day
- Instagram → 2 slots/day
- TikTok → 2 slots/day

> The number of rows per platform equals its daily capacity.

---

#### `publications`
Final publication agenda.

States:
- `scheduled`
- `publishing`
- `published`
- `failed`

Only **live states** block slots:
```
scheduled, publishing, published
```

---

## 4. Scheduler Logic (crear_publications)

The scheduler:
1. Reads platform schedules
2. Calculates daily capacity per platform
3. Reads video inventory
4. For each day and platform:
   - Counts already scheduled/published content (legacy-safe)
   - Creates publications only if capacity is available
   - Avoids exact slot duplication
   - Applies technical and editorial rules

### Key Properties
- Idempotent (safe to run repeatedly)
- Legacy-compatible
- Platform-aware
- Editorially controlled

---

## 5. Technical Rules

### Slot Uniqueness
A publication cannot exist with the same:
```
(channel_id, platform_id, publicar_en)
```

---

### Collision Prevention (per platform)
- **Slug collision:** avoids repeating similar titles too close in time
- **Text collision:** avoids repeating the same content text

Different windows apply for:
- Prayers
- Psalms

---

## 6. Editorial Rules (Exposure Control)

Defined per platform:

| Platform   | Window | Max repetitions |
|-----------|--------|-----------------|
| YouTube   | 60 days | 1               |
| Facebook  | 30 days | 3               |
| Instagram | 30 days | 3               |
| TikTok    | 7 days  | Unlimited       |

A video:
- **May appear on multiple platforms**
- **Is limited per platform** according to these rules

---

## 7. Legacy Compatibility

- Legacy publications with old schedules are respected
- They count toward daily capacity
- The scheduler never overwrites historical data
- The system can evolve without breaking past content

---

## 8. Execution Commands

### Generate Videos (OSO Flow)
```bash
.venv/bin/python -m generator.entrypoint 1 oso
```

### Run the Scheduler (Create Publications)
```bash
.venv/bin/python -m generator.publications.run_scheduler
```

Expected output example:
```
[SCHEDULER] channel=7 publicaciones_creadas=54
```

### Safe Re-run Behavior
- Re-running the scheduler does **not** duplicate publications
- Only missing slots or failed publications may be refilled

---

## 9. Failure Handling

If a publication fails:
- Its state becomes `failed`
- Failed publications do **not** block capacity
- Scheduler can create a replacement on next run

---

## 10. Current Status

### ✅ Completed
- Video generation pipeline
- Editorial inventory
- Multi-platform scheduler
- Technical collision rules
- Editorial exposure rules
- Legacy-safe behavior
- Idempotent scheduling

### 🚀 Next Step
Implement **platform-specific publishing workers**:
- One worker per platform
- Consumes `scheduled` publications
- Handles publishing, retries, errors, and `external_id`

---

## 11. Conclusion

This system is no longer a script — it is a **production-grade editorial automation platform**.

The scheduling layer is:
- Robust
- Scalable
- Auditable
- Ready for asynchronous workers

You can safely move forward to the publishing phase.



.venv/bin/python -m generator.cli.publish_facebook --dry-run --preview-2d