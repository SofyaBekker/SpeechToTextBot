#import torch
import torchaudio        
import subprocess
from io import BytesIO
from typing import BinaryIO
import logging

from transformers import WhisperForConditionalGeneration, WhisperProcessor, pipeline

logging.basicConfig(
    filename='app2.log',
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


class WhisperRussian():
    def __init__(self, whisp_version="antony66/whisper-large-v3-russian", device="cpu"):
        self.kwargs = {"language": "russian", "max_new_tokens": 256}
        print("Model is loading")
        logger.info("Model is loading")
        self.modelWhisp = WhisperForConditionalGeneration.from_pretrained(
                whisp_version, use_safetensors=True) #torch_dtype=torch_dtype, low_cpu_mem_usage=True,
        
        print("Preprocessor is loading")
        logger.info("Preprocessor is loading")
        self.preprocessor_Wisp = WhisperProcessor.from_pretrained(whisp_version)
        
        print("Creating pipeline")    
        logger.info("Creating pipeline")
        self.pipeline = pipeline(
            'automatic-speech-recognition', 
            model=whisp_version, 
            device=device,
            generate_kwargs=self.kwargs, 
            return_timestamps=False
            )

        print("Configuring done!")
        logger.info("Configuring done!")
        
    # def file_to_text(self, file_path):
        
    #     new_file_path = 'E:\\PProject\\tests\\audio1.wav'
    #     subprocess.call(["ffmpeg", "-i", file_path, "-ar", "16000", "-ac", "1", new_file_path])
        
    #     with open(new_file_path, 'rb')  as f:
    #         y, rb = torchaudio.load(f)
            
    #     print("File is loaded!")        
        
        
    #     ars = self.pipeline(y[0].numpy(), generate_kwargs=self.kwargs, return_timestamps=False)
        
    #     return ars['text']
    
    def bytes_to_text(self, audio_bytes : bytes):
        
        binary_io: BinaryIO = BytesIO(audio_bytes)
        
        binary_io.seek(0)
        
        waveform, rb = torchaudio.load(binary_io)
        print("File is loaded!") 
        logger.info("File is loaded!")
        
        segment_dur = 20  # seconds
        segment_len = segment_dur * rb
        
        num_sampels = waveform.size(1)
        
        segments = []
        
        for start in range(0, num_sampels, segment_len):
            end = start + segment_len
            segment = waveform[:, start:end]
            segments.append(segment)
        
        logger.info("Segments is done")
        logger.debug(f"Segments num: {len(segments)}")
        
        result = ''
        
        for segment in segments:
            ars = self.pipeline(segment[0].numpy(), generate_kwargs=self.kwargs, return_timestamps=False)
            logger.debug(f"segment result: {ars['text']}")
            result += ars['text']
        
        return result
        
        

# path = 'E:\\PProject\\tests\\audio1.wav' #'E:\\PProject\\tests\\test1.wav'    
# whisp = WhisperRussian()

# with open(path, 'rb') as f:
#     data_bytes = f.read()

# #ans = whisp.file_to_text(path)
# ans = whisp.bytes_to_text(data_bytes)

# print(ans) 