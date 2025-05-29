from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from io import BytesIO
import subprocess
import magic
import tempfile

import logging
import requests

import configparser

config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['TG']['TOKEN']
URL = config['FLSK']['URL']

logging.basicConfig(
    filename='app.log',
    filemode='a',  # 'w' - перезаписывать каждый раз
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


logger = logging.getLogger(__name__)

handler = logging.FileHandler(f"{__name__}.log", mode='a')
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info(f"Testing the custom logger for module {__name__}...")


def extract_audio_from_file(video_path: str) -> bytes:
    
    logger.info("Start converting")
    
    
    command = [
        'ffmpeg',
        '-i', video_path,           # Читаем из video_path
        '-map', 'a:0',              # Явно указываем аудиопоток
        '-vn',                      # Игнорируем видео
        '-acodec', 'pcm_s16le',     # Кодек для wav
        '-ar', '16000',             # Частота дискретизации 16 кГц
        '-ac', '1',                 # Одноканальный (моно)
        '-f', 'wav',                # Формат выходных данных
        'pipe:1'                    # Пишем в stdout
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        wav_bytes, stderr = process.communicate()        
    except Exception as e:
        logger.error(str(e))
            

    if process.returncode != 0:
        logger.error(f"Converting error: {stderr.decode()}")
        raise RuntimeError(f"Ошибка при конвертации: {stderr.decode()}")
        
    print("Конвертация успешна")
    logger.info("Converting is success")

    return wav_bytes

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот.')

# Обработчик текстовых сообщений
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)
    
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice  # Получаем объект голосового сообщения

    if voice:
        await update.message.reply_text("Получено голосовое сообщение!")        
        logger.info("Audio was received")
        # Получаем файл 
        file_id = voice.file_id
        new_file = await context.bot.get_file(file_id)

        # Скачиваем файл в оперативную память как байты
        file_bytes = await new_file.download_as_bytearray()
        
        file_io = BytesIO(file_bytes)
        
        filename = "audio"
        mime_type = ""
        # Формируем данные для multipart/form-data
        files = {
            'file': (filename, file_io, mime_type)
        }

        logger.info("Data prepared to POST")
        response = requests.post(URL+'/audiototext', files=files)           
        
        
        await update.message.reply_text(response.text)    
        
async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_note = update.message.video_note
    
    if video_note:
        await update.message.reply_text("Получено видеосообщение!")
        logger.info("Video was received")
    
        file = await context.bot.get_file(video_note.file_id)   
        
        logger.debug(f"File path: {file.file_path}")
        
        file_bytes = await file.download_as_bytearray()   
        
        logger.debug(f"Downloaded size: {len(file_bytes)}")
               
                
        try:       
            mime = magic.from_buffer(bytes(file_bytes[:2048]), mime=True)
            logger.debug(f"MIME-тип загруженного файла: {mime}")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            
        if mime != 'video/mp4':
            logger.error("Format is wrong!")
            
            
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(file_bytes)
            tmp_video_path = tmp_video.name
            
        audio_bytes = extract_audio_from_file(tmp_video_path)
        
        file_io = BytesIO(audio_bytes)
        
        logger.debug("File IO created")
        
        filename = "audio"
        mime_type = ""
        
        # Формируем данные для multipart/form-data
        files = {
            'file': (filename, file_io, mime_type)
        }
        
        logger.info("Data prepared to POST")
        
        
        response = requests.post(URL+'/audiototext', files=files)   
        
        await  update.message.reply_text(response.text)   

# Основная функция запуска бота
def main():
    logger.debug("Bot is started")
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))

    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

# Запуск
main()