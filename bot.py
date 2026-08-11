import os
import fal_client
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ["TOKEN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Kirim FOTO karakter dulu, setelah itu kirim VIDEO referensi gerakannya.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    context.user_data["photo_url"] = photo_file.file_path
    await update.message.reply_text("Foto diterima! Sekarang kirim video referensi gerakannya.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "photo_url" not in context.user_data:
        await update.message.reply_text("Kirim foto dulu ya, baru video referensi.")
        return

    video_file = await update.message.video.get_file()
    video_url = video_file.file_path
    photo_url = context.user_data["photo_url"]

    await update.message.reply_text("Sedang proses motion transfer, mohon tunggu beberapa menit...")

    try:
        result = fal_client.subscribe(
            "fal-ai/kling-video/v2.6/standard/motion-control",
            arguments={"image_url": photo_url, "video_url": video_url},
        )
        result_video_url = result["video"]["url"]
        await update.message.reply_video(result_video_url)
    except Exception as e:
        await update.message.reply_text(f"Gagal proses: {e}")

    del context.user_data["photo_url"]

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.run_polling()
