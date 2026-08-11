import os
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ["TOKEN"]
DEAPI_KEY = os.environ["DEAPI_KEY"]

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
        headers = {
            "Authorization": f"Bearer {DEAPI_KEY}",
            "Accept": "application/json",
        }
        data = {
            "model": "Wan2_2_Animate_14B_INT8",
            "video": video_url,
            "ref_image": photo_url,
        }
        resp = requests.post(
            "https://api.deapi.ai/api/v1/client/video-replacement",
            headers=headers,
            data=data,
        )
        resp.raise_for_status()
        job = resp.json()
        job_id = job.get("id") or job.get("job_id")

        result_url = None
        for _ in range(60):
            time.sleep(5)
            status_resp = requests.get(
                f"https://api.deapi.ai/api/v1/client/jobs/{job_id}",
                headers=headers,
            )
            status_data = status_resp.json()
            status = status_data.get("status")
            if status == "completed":
                result_url = status_data.get("output_url") or status_data.get("result", {}).get("url")
                break
            elif status == "failed":
                raise Exception(status_data.get("error", "Proses gagal di server"))

        if result_url:
            await update.message.reply_video(result_url)
        else:
            await update.message.reply_text("Proses terlalu lama, coba lagi nanti.")

    except Exception as e:
        await update.message.reply_text(f"Gagal proses: {e}")

    del context.user_data["photo_url"]

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.run_polling()
