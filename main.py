import os
import asyncio
import logging
from telethon import TelegramClient, events
from telegram import Bot
import google.generativeai as genai
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SOURCE_CHANNEL = os.environ.get("SOURCE_CHANNEL")
MIDDLE_CHANNEL = os.environ.get("MIDDLE_CHANNEL")
DEST_CHANNEL = os.environ.get("DEST_CHANNEL")
SESSION_STRING = os.environ.get("SESSION_STRING")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def translate_to_persian(text):
    if not text or not text.strip():
        return None
    try:
        response = model.generate_content(
            f"Translate the following text to Persian (Farsi). Only return the translation, nothing else:\n\n{text}"
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

async def main():
    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient.StringSession(SESSION_STRING) if SESSION_STRING else TelegramClient('session', API_ID, API_HASH)
    await client.start()
    logger.info("Telethon client started")

    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def handler(event):
        try:
            msg = event.message
            translated_text = translate_to_persian(msg.text) if msg.text else None
            caption = translate_to_persian(msg.message) if msg.message else None

            if msg.photo:
                photo = await client.download_media(msg.photo, file=tempfile.mktemp(suffix=".jpg"))
                await bot.send_photo(chat_id=DEST_CHANNEL, photo=open(photo, "rb"), caption=caption)
                os.remove(photo)
            elif msg.video:
                video = await client.download_media(msg.video, file=tempfile.mktemp(suffix=".mp4"))
                await bot.send_video(chat_id=DEST_CHANNEL, video=open(video, "rb"), caption=caption)
                os.remove(video)
            elif msg.audio or msg.voice:
                media = msg.audio or msg.voice
                audio = await client.download_media(media, file=tempfile.mktemp(suffix=".ogg"))
                await bot.send_audio(chat_id=DEST_CHANNEL, audio=open(audio, "rb"), caption=caption)
                os.remove(audio)
            elif msg.document:
                doc = await client.download_media(msg.document, file=tempfile.mktemp())
                await bot.send_document(chat_id=DEST_CHANNEL, document=open(doc, "rb"), caption=caption)
                os.remove(doc)
            elif translated_text:
                await bot.send_message(chat_id=DEST_CHANNEL, text=translated_text)

            logger.info("Message processed and sent")
        except Exception as e:
            logger.error(f"Error: {e}")

    logger.info(f"Listening to {SOURCE_CHANNEL}...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
