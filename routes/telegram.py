import re
import threading
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import Config

logger = logging.getLogger(__name__)

# Will be set by start_telegram_bot()
_flask_app = None

# Track which users are in chat mode: {user_id: adaptation_id}
_chat_sessions = {}


def _get_base_url():
    import os
    public_url = os.getenv("PUBLIC_URL")
    if public_url:
        return public_url.rstrip("/")
    local_ip = Config.get_local_ip()
    port = os.getenv("PORT", "5080")
    return f"http://{local_ip}:{port}"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "TikTok Script Analyzer\n\n"
        "Mándame un link de TikTok y te doy:\n"
        "- Transcripción del video\n"
        "- Análisis viral del guion\n"
        "- Puntuación de viralidad\n\n"
        "Comandos:\n"
        "/history — Últimos 5 análisis\n"
        "/adapt <id> <producto> — Adaptar un guion\n"
        "/cross <ids o urls> — Análisis cruzado de varios videos\n"
        "/chat <adaptation_id> — Modo chat para refinar un guion\n"
        "/exit — Salir del modo chat"
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
            api_key=Config.OPENAI_API_KEY,
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


async def cross_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: /cross <id1> <id2> [url ...]\nEj: /cross 1 2 3\nEj: /cross 1 https://tiktok.com/...")
        return

    try:
        with _flask_app.app_context():
            from models import Analysis, Video, Transcription, CrossAnalysis, db
            from services.transcriber import transcribe_tiktok
            from services.analyzer import analyze_script
            from services.cross_analyzer import cross_analyze
            import json

            video_ids = []
            tiktok_pattern = r"https?://(www\.|vm\.)?tiktok\.com/\S+"

            for arg in args:
                if re.match(tiktok_pattern, arg):
                    await update.message.reply_text(f"Procesando URL: {arg}")
                    result = transcribe_tiktok(
                        tiktok_url=arg,
                        tmp_dir=Config.TMP_DIR,
                        openai_api_key=Config.OPENAI_API_KEY,
                    )
                    analysis_data = analyze_script(
                        transcript=result["text"],
                        api_key=Config.OPENAI_API_KEY,
                    )
                    author_match = re.search(r"tiktok\.com/@([^/]+)", arg)
                    author = f"@{author_match.group(1)}" if author_match else None

                    video = Video(tiktok_url=arg, author=author)
                    db.session.add(video)
                    db.session.commit()

                    t = Transcription(video_id=video.id, text=result["text"], duration_seconds=result["duration_seconds"])
                    a = Analysis(
                        video_id=video.id,
                        hook_text=analysis_data["hook"]["text"],
                        hook_type=analysis_data["hook"]["type"],
                        hook_score=analysis_data["hook"]["score"],
                        structure=json.dumps(analysis_data["structure"], ensure_ascii=False),
                        virality_score=analysis_data["virality_score"]["score"],
                        persuasion_elements=json.dumps(analysis_data["persuasion_elements"], ensure_ascii=False),
                        full_analysis_json=json.dumps(analysis_data, ensure_ascii=False),
                    )
                    db.session.add_all([t, a])
                    db.session.commit()
                    video_ids.append(video.id)
                else:
                    try:
                        video_ids.append(int(arg))
                    except ValueError:
                        await update.message.reply_text(f"Argumento no válido: {arg}")
                        return

            transcripts = []
            analyses = []
            for vid in video_ids:
                video = Video.query.get(vid)
                if not video or not video.transcription or not video.analysis:
                    continue
                transcripts.append(video.transcription.text)
                try:
                    analyses.append(json.loads(video.analysis.full_analysis_json))
                except (json.JSONDecodeError, TypeError):
                    continue

            if len(analyses) < 2:
                await update.message.reply_text("Se necesitan al menos 2 videos con análisis.")
                return

            await update.message.reply_text("Analizando patrones cruzados...")

            result = cross_analyze(
                transcripts=transcripts,
                analyses=analyses,
                api_key=Config.OPENAI_API_KEY,
            )

            ca = CrossAnalysis(
                video_ids=json.dumps(video_ids),
                result_json=json.dumps(result, ensure_ascii=False),
            )
            db.session.add(ca)
            db.session.commit()

        base_url = _get_base_url()
        winning = result.get("winning_formula", "No se pudo determinar.")
        if isinstance(winning, dict):
            winning = json.dumps(winning, ensure_ascii=False, indent=2)

        msg = (
            f"Análisis cruzado completado ({len(analyses)} videos)\n\n"
            f"Fórmula ganadora:\n{winning}\n\n"
            f"Ver completo: {base_url}/cross/{ca.id}"
        )
        if len(msg) > 4000:
            msg = msg[:4000] + "..."
        await update.message.reply_text(msg)

    except Exception as e:
        logger.error(f"Error in cross_command: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: /chat <adaptation_id>\nEj: /chat 5")
        return

    try:
        adaptation_id = int(args[0])
    except ValueError:
        await update.message.reply_text("El ID debe ser un número.")
        return

    with _flask_app.app_context():
        from models import Adaptation
        adaptation = Adaptation.query.get(adaptation_id)
        if not adaptation:
            await update.message.reply_text(f"No se encontró adaptación con ID {adaptation_id}.")
            return

    user_id = update.effective_user.id
    _chat_sessions[user_id] = adaptation_id
    await update.message.reply_text(
        f"Modo chat activado para adaptación #{adaptation_id}.\n"
        "Mándame mensajes para refinar el guion.\n"
        "Usa /exit para salir del modo chat."
    )


async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in _chat_sessions:
        del _chat_sessions[user_id]
        await update.message.reply_text("Modo chat desactivado.")
    else:
        await update.message.reply_text("No estás en modo chat.")


async def handle_tiktok_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Check chat mode first
    if user_id in _chat_sessions:
        adaptation_id = _chat_sessions[user_id]
        try:
            with _flask_app.app_context():
                from models import Adaptation, ChatMessage, db
                from services.chat import chat_refine

                adaptation = Adaptation.query.get(adaptation_id)
                if not adaptation:
                    del _chat_sessions[user_id]
                    await update.message.reply_text("Adaptación no encontrada. Modo chat desactivado.")
                    return

                analysis = adaptation.analysis
                video = analysis.video
                transcription = video.transcription

                analysis_summary = f"Hook: {analysis.hook_type}, Score: {analysis.hook_score}/10, Viralidad: {analysis.virality_score}/10"

                chat_history = [
                    {"role": m.role, "content": m.content}
                    for m in ChatMessage.query.filter_by(adaptation_id=adaptation_id)
                        .order_by(ChatMessage.created_at).all()
                ]

                current_script = adaptation.current_script or adaptation.adapted_script

                refined = chat_refine(
                    original_transcript=transcription.text,
                    analysis_summary=analysis_summary,
                    current_script=current_script,
                    chat_history=chat_history,
                    user_message=text,
                    api_key=Config.OPENAI_API_KEY,
                )

                user_msg = ChatMessage(adaptation_id=adaptation_id, role="user", content=text)
                assistant_msg = ChatMessage(adaptation_id=adaptation_id, role="assistant", content=refined)
                db.session.add_all([user_msg, assistant_msg])

                adaptation.current_script = refined
                db.session.commit()

            reply = refined
            if len(reply) > 3500:
                reply = reply[:3500] + "...\n\n(Ver completo en la web)"
            await update.message.reply_text(f"Guion actualizado:\n\n{reply}")

        except Exception as e:
            logger.error(f"Error in chat mode: {e}")
            await update.message.reply_text(f"Error: {str(e)}")
        return

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
                api_key=Config.OPENAI_API_KEY,
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
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def start_polling():
            app = Application.builder().token(token).build()
            app.add_handler(CommandHandler("start", start_command))
            app.add_handler(CommandHandler("history", history_command))
            app.add_handler(CommandHandler("adapt", adapt_command))
            app.add_handler(CommandHandler("cross", cross_command))
            app.add_handler(CommandHandler("chat", chat_command))
            app.add_handler(CommandHandler("exit", exit_command))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok_url))

            logger.info("Telegram bot started (polling)")
            await app.initialize()
            await app.updater.start_polling(drop_pending_updates=True)
            await app.start()

            # Keep running
            import signal
            stop_event = asyncio.Event()
            await stop_event.wait()

        loop.run_until_complete(start_polling())

    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
