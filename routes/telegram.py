import re
import threading
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import Config

logger = logging.getLogger(__name__)

# Will be set by start_telegram_bot()
_flask_app = None


def _get_base_url():
    local_ip = Config.get_local_ip()
    return f"http://{local_ip}:5060"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "TikTok Script Analyzer\n\n"
        "Mándame un link de TikTok y te doy:\n"
        "- Transcripción del video\n"
        "- Análisis viral del guion\n"
        "- Puntuación de viralidad\n\n"
        "Comandos:\n"
        "/history — Últimos 5 análisis\n"
        "/adapt <id> <producto> — Adaptar un guion"
    )


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with _flask_app.app_context():
        from models import Video
        videos = Video.query.order_by(Video.created_at.desc()).limit(5).all()

    if not videos:
        await update.message.reply_text("No hay análisis todavía.")
        return

    base_url = _get_base_url()
    lines = []
    for v in videos:
        score = v.analysis.virality_score if v.analysis else "?"
        lines.append(f"#{v.id} {v.author or '?'} — Viralidad: {score}/10\n{base_url}/history/{v.id}")

    await update.message.reply_text("\n\n".join(lines))


async def adapt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /adapt <id> <producto>\nEj: /adapt 3 Creatina")
        return

    try:
        analysis_id = int(args[0])
    except ValueError:
        await update.message.reply_text("El ID debe ser un número.")
        return

    product = " ".join(args[1:])

    with _flask_app.app_context():
        from models import Analysis, Adaptation, db
        from services.adapter import adapt_script

        analysis = Analysis.query.get(analysis_id)
        if not analysis:
            await update.message.reply_text(f"No se encontró análisis con ID {analysis_id}.")
            return

        video = analysis.video
        transcription = video.transcription

        await update.message.reply_text(f"Adaptando guion a '{product}'...")

        analysis_summary = f"Hook: {analysis.hook_type}, Score: {analysis.hook_score}/10, Viralidad: {analysis.virality_score}/10"

        adapted = adapt_script(
            original_transcript=transcription.text,
            analysis_summary=analysis_summary,
            product_or_topic=product,
            api_key=Config.ANTHROPIC_API_KEY,
        )

        adaptation = Adaptation(
            analysis_id=analysis.id,
            product_or_topic=product,
            adapted_script=adapted,
        )
        db.session.add(adaptation)
        db.session.commit()

    # Truncate if too long for Telegram
    if len(adapted) > 3500:
        adapted = adapted[:3500] + "...\n\n(Ver completo en la web)"

    await update.message.reply_text(f"Guion adaptado para: {product}\n\n{adapted}")


async def handle_tiktok_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    tiktok_pattern = r"https?://(www\.|vm\.)?tiktok\.com/\S+"
    match = re.search(tiktok_pattern, text)

    if not match:
        await update.message.reply_text("Mándame un link de TikTok para analizarlo.")
        return

    url = match.group(0)
    await update.message.reply_text("Procesando... esto toma unos segundos.")

    try:
        with _flask_app.app_context():
            from models import Video, Transcription, Analysis, db
            from services.transcriber import transcribe_tiktok
            from services.analyzer import analyze_script
            import json

            result = transcribe_tiktok(
                tiktok_url=url,
                tmp_dir=Config.TMP_DIR,
                openai_api_key=Config.OPENAI_API_KEY,
            )

            analysis_data = analyze_script(
                transcript=result["text"],
                api_key=Config.ANTHROPIC_API_KEY,
            )

            author_match = re.search(r"tiktok\.com/@([^/]+)", url)
            author = f"@{author_match.group(1)}" if author_match else None

            video = Video(tiktok_url=url, author=author)
            db.session.add(video)
            db.session.commit()

            transcription = Transcription(
                video_id=video.id,
                text=result["text"],
                duration_seconds=result["duration_seconds"],
            )
            analysis = Analysis(
                video_id=video.id,
                hook_text=analysis_data["hook"]["text"],
                hook_type=analysis_data["hook"]["type"],
                hook_score=analysis_data["hook"]["score"],
                structure=json.dumps(analysis_data["structure"], ensure_ascii=False),
                virality_score=analysis_data["virality_score"]["score"],
                persuasion_elements=json.dumps(analysis_data["persuasion_elements"], ensure_ascii=False),
                full_analysis_json=json.dumps(analysis_data, ensure_ascii=False),
            )
            db.session.add_all([transcription, analysis])
            db.session.commit()

        base_url = _get_base_url()
        transcript_preview = result["text"][:500]
        if len(result["text"]) > 500:
            transcript_preview += "..."

        msg = (
            f"Viralidad: {analysis_data['virality_score']['score']}/10\n"
            f"Hook ({analysis_data['hook']['type']}): \"{analysis_data['hook']['text']}\"\n"
            f"Hook score: {analysis_data['hook']['score']}/10\n\n"
            f"Transcripción:\n{transcript_preview}\n\n"
            f"Ver análisis completo:\n{base_url}/history/{video.id}"
        )
        await update.message.reply_text(msg)

    except Exception as e:
        logger.error(f"Error processing TikTok URL: {e}")
        await update.message.reply_text(f"Error al procesar el video: {str(e)}")


def start_telegram_bot(flask_app):
    """Start the Telegram bot in a background thread using polling."""
    global _flask_app
    _flask_app = flask_app

    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping Telegram bot")
        return

    def run_bot():
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("history", history_command))
        app.add_handler(CommandHandler("adapt", adapt_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok_url))

        logger.info("Telegram bot started (polling)")
        app.run_polling(drop_pending_updates=True)

    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
