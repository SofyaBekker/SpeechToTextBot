from flask import Flask
from flask import request
import subprocess
import magic

import Reg_Auth
import model
import logging

app = Flask(__name__)

reg = Reg_Auth.Reg_Auth()

whisp = model.WhisperRussian()

logging.basicConfig(
    filename='app1.log',
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

def convert_ogg_to_wav_16k(data: bytes, ogg=True) -> bytes:
    """
    Конвертирует OGG в WAV 16kHz в оперативной памяти
    :param ogg_data: исходный файл в виде байтов
    :return: конвертированный WAV-файл в виде байтов
    """
    
    command = [
        'ffmpeg',
        '-i', 'pipe:0',             # Читаем из stdin
        '-ar', '16000',             # Частота дискретизации 16 кГц
        '-ac', '1',                 # Одноканальный (моно)
        '-f', 'wav',                # Формат вывода — WAV
        'pipe:1'                    # Пишем в stdout
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    wav_bytes, stderr = process.communicate(input=data)

    if process.returncode != 0:
        logger.error(f"Converting error: {stderr.decode()}")
        raise RuntimeError(f"Ошибка при конвертации: {stderr.decode()}")
        
    logger.info("Converting is success")

    return wav_bytes


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/audiototext", methods=["POST"])
def audiototext():
    
    if 'file' not in request.files:
        return 'Файл не загружен', 400

    file = request.files['file']  # Получаем файл

    # Если имя файла пустое
    if file.filename == '':
        return 'Файл не выбран', 400
        
    # Читаем содержимое файла как байты
    file_bytes = file.read()
    
    mime = magic.from_buffer(file_bytes[:2048], mime=True)
    logger.info(f"MIME-type loaded file:  {mime}")
    
    if mime == 'audio/x-wav':
        audio_bytes = convert_ogg_to_wav_16k(file_bytes)
    else:
        audio_bytes = file_bytes
    
    mime = magic.from_buffer(audio_bytes[:2048], mime=True)
    logger.info(f"MIME-type converted file: {mime}")
    
    try:
        ans = whisp.bytes_to_text(audio_bytes)
        return ans
    except Exception as e:
        logger.error(str(e))
