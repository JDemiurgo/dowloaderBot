import os 
import uuid
import asyncio
import yt_dlp

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

#=============================
#CONFIG
#=============================


BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER,exist_ok=True)


#=============================
#START COMMAND
#=============================

async def start(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "mandami un link di video facebook e io lo renderò scaricabile"
    )

#=============================
#DOWNLOAD VIDEO
#=============================
async def download_video(update: Update, context:ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "facebook.com" not in url and "fb.watch" not in url:
        await update.message.reply_text(
            "Mandami un link facebook valido"
        )
        return
    
    waiting_message = await update.message.reply_text(
        "Scaricamento in corso..."
    )

    unique_name = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join(DOWNLOAD_FOLDER,unique_name)

    ydl_opts = {
        "outtmpl": output_path,
        #"format":"best[ext=mp4]",
        "format":"bestvideo+bestaudio/best",
        "merge_output_format":"mp4",
        "quiet": True,
        "noplaylist": True,
    }


    try:

        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL(ydl_opts).download([url])
        )

        if not os.path.exists(output_path):
            raise Exception("File non trovato dopo il download")

        file_size = os.path.getsize(output_path)

        # Telegram limite circa 50MB per bot standard
        if file_size > 49 * 1024 * 1024:
            await waiting_message.edit_text(
                "Video troppo grande per Telegram."
            )
            os.remove(output_path)
            return

        await waiting_message.edit_text(
            "Invio del video..."
        )

        with open(output_path, "rb") as video:
            await update.message.reply_video(video=video)

        await waiting_message.delete()

        os.remove(output_path)

    except Exception as e:

        print(e)

        await waiting_message.edit_text(
            "Errore durante il download del video."
        )

        if os.path.exists(output_path):
            os.remove(output_path)



# =========================
# MAIN
# =========================


def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, download_video)
    )

    print("Bot avviato...")

    app.run_polling()


if __name__ == "__main__":
    main()

