import sounddevice as sd
import numpy as np
import queue
import tempfile
from faster_whisper import WhisperModel
import wave
import os

model_size = "small"
device = "cpu"
compute_type = "int8"
sample_rate = 16000
block_size = 5

model = WhisperModel(model_size, device=device, compute_type=compute_type)
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())

with sd.InputStream(samplerate=sample_rate, channels=1, callback=audio_callback):
    print("Listening... Press Ctrl+C to stop.")
    try:
        while True:
            audio_chunk = []
            while len(audio_chunk) < sample_rate * block_size:
                data = audio_queue.get()
                audio_chunk.extend(data[:, 0])
            
            audio_np = np.array(audio_chunk, dtype=np.float32)

            # Use a temporary file without keeping it open
            tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_file.close()  # Important on Windows

            with wave.open(tmp_file.name, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())
            
            segments, info = model.transcribe(tmp_file.name, beam_size=5)
            for segment in segments:
                print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

            os.remove(tmp_file.name)  # Clean up the temp file

    except KeyboardInterrupt:
        print("Stopped listening.")
