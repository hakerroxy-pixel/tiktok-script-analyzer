# TikTok Script Analyzer — API Documentation

## Base URL
```
https://web-production-b34f5.up.railway.app
```

CORS habilitado para todas las rutas `/api/*`. Se puede llamar desde cualquier frontend.

## Resumen

API para transcribir videos de TikTok, analizar su guion como experto en contenido viral, generar 5 versiones adaptadas a un producto/tema, refinar guiones por chat, y hacer análisis cruzado de múltiples videos.

---

## Endpoints

### 1. Listar videos (historial)
```
GET /api/videos
```

**Response:**
```json
[
  {
    "id": 1,
    "tiktok_url": "https://www.tiktok.com/@user/video/123",
    "author": "@user",
    "created_at": "2026-04-06T10:30:00",
    "transcription": {
      "text": "Texto completo de la transcripción...",
      "duration_seconds": 45.0
    },
    "analysis": {
      "id": 1,
      "hook_text": "Si consumes omega 3 y no estás viendo resultados",
      "hook_type": "promesa",
      "hook_score": 8,
      "virality_score": 7,
      "full": { /* análisis completo JSON */ }
    },
    "adaptations": [
      {
        "id": 1,
        "product_or_topic": "Creatina",
        "version_number": 1,
        "hook_style": "pregunta directa",
        "script": "Guion completo...",
        "is_favorite": false
      }
    ]
  }
]
```

---

### 2. Detalle de un video
```
GET /api/video/<video_id>
```

**Response:** Mismo formato que un item del array de `/api/videos`.

---

### 3. Transcribir y analizar un video
```
POST /api/transcribe
Content-Type: application/json

{
  "url": "https://www.tiktok.com/@user/video/123456789"
}
```

**Response (200):**
```json
{
  "video_id": 1,
  "transcription": {
    "text": "Texto completo de la transcripción...",
    "duration_seconds": 45.0
  },
  "analysis": {
    "hook": {
      "text": "Si consumes omega 3...",
      "type": "promesa",
      "score": 8,
      "explanation": "Genera curiosidad inmediata..."
    },
    "structure": {
      "sections": [
        {"name": "Hook", "duration": "0-3s", "content": "..."},
        {"name": "Desarrollo", "duration": "3-50s", "content": "..."},
        {"name": "CTA", "duration": "50-60s", "content": "..."}
      ],
      "rhythm": "medio"
    },
    "virality_score": {
      "score": 7,
      "justification": "...",
      "positive_factors": ["info práctica", "tema popular"],
      "negative_factors": ["falta emoción"]
    },
    "persuasion_elements": [
      {"technique": "autoridad", "usage": "...", "effectiveness": "alta"}
    ]
  }
}
```

**Error (500):**
```json
{"error": "Error al transcribir: ..."}
```

**Tiempo:** 15-30 segundos (descarga audio + Whisper + GPT-4o)

---

### 4. Adaptar guion a un producto (genera 5 versiones)
```
POST /api/adapt/<analysis_id>
Content-Type: application/json

{
  "product_or_topic": "Creatina"
}
```

El `analysis_id` viene del response de `/api/transcribe` (campo `analysis.id` del video).

**Response (200):**
```json
{
  "analysis_id": 1,
  "product_or_topic": "Creatina",
  "versions": [
    {
      "adaptation_id": 1,
      "version_number": 1,
      "hook_style": "pregunta directa",
      "script": "¿Sabías que la creatina es el suplemento más estudiado del mundo?..."
    },
    {
      "adaptation_id": 2,
      "version_number": 2,
      "hook_style": "dato sorprendente",
      "script": "Más de 700 estudios científicos respaldan este suplemento..."
    },
    // ... 5 versiones total
  ]
}
```

**Tiempo:** 20-40 segundos (3 llamadas a GPT-4o: estructura + investigación + creación)

---

### 5. Refinar guion por chat
```
POST /api/chat/<adaptation_id>
Content-Type: application/json

{
  "message": "Hazlo más corto y agrega más urgencia"
}
```

**Response (200):**
```json
{
  "script": "Guion refinado completo...",
  "message_id": 5,
  "adaptation_id": 1
}
```

El campo `script` contiene el guion actualizado. Cada llamada actualiza el `current_script` de la adaptación.

**Tiempo:** 5-10 segundos

---

### 6. Marcar/desmarcar favorita
```
POST /api/adaptation/<adaptation_id>/favorite
```

No necesita body. Toggle: si es favorita la desmarca, si no es favorita la marca.

**Response (200):**
```json
{
  "adaptation_id": 1,
  "is_favorite": true
}
```

---

### 7. Análisis cruzado (patrones entre videos)
```
POST /api/cross-analyze
Content-Type: application/json

{
  "video_ids": [1, 2, 3],
  "new_urls": ["https://www.tiktok.com/@user/video/456"]
}
```

Puedes enviar `video_ids` (IDs del historial), `new_urls` (URLs de TikTok que se transcriben y analizan primero), o ambos. Mínimo 2 videos.

**Response (200):**
```json
{
  "cross_analysis_id": 1,
  "video_count": 4,
  "result": {
    "hook_patterns": {
      "most_used": "pregunta",
      "best_scoring": "dato impactante",
      "types": [{"type": "pregunta", "count": 3, "avg_score": 7.5}]
    },
    "structure_patterns": {
      "avg_hook_duration": "0-3s",
      "avg_total_duration": "45s",
      "common_rhythm": "rápido"
    },
    "persuasion_patterns": [
      {"technique": "curiosidad", "frequency": 4, "avg_effectiveness": "alta"}
    ],
    "common_themes": ["suplementos", "resultados"],
    "winning_formula": "Usa hooks de pregunta directa, mantén ritmo rápido..."
  }
}
```

---

## Flujo típico de integración

```
1. POST /api/transcribe        → obtén video_id y analysis.id
2. POST /api/adapt/{analysis_id} → obtén 5 versiones con adaptation_id
3. POST /api/chat/{adaptation_id} → refina cualquier versión
4. POST /api/adaptation/{id}/favorite → marca la mejor
5. GET /api/videos              → lista todo el historial
```

## Errores

Todos los errores devuelven JSON:
```json
{"error": "Descripción del error"}
```

Códigos HTTP: 400 (bad request), 404 (not found), 500 (server error).

## Stack técnico

- **Backend:** Python 3.12, Flask, SQLAlchemy, SQLite
- **Transcripción:** yt-dlp (descarga audio) + OpenAI Whisper API
- **Análisis/Adaptación:** OpenAI GPT-4o
- **Hosting:** Railway (web-production-b34f5.up.railway.app)
- **DB:** SQLite en volumen persistente de Railway
- **Telegram:** python-telegram-bot (polling)
- **Repo:** github.com/primesupplementspe-lab/tiktok-script-analyzer

## Variables de entorno necesarias

```
OPENAI_API_KEY=sk-proj-...
TELEGRAM_BOT_TOKEN=8624162410:...
SECRET_KEY=prime-tiktok-analyzer-prod-2026
PUBLIC_URL=https://web-production-b34f5.up.railway.app
```
