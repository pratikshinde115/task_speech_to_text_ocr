import argparse
import os
import numpy as np
import queue
import whisper
import torch
import sounddevice as sd
import noisereduce as nr
import soundfile as sf
from datetime import datetime, timedelta
from time import sleep
from sys import platform

class RealTimeTranscriber:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self._setup_arguments()
        self.args = self.parser.parse_args()
        
        self.model = whisper.load_model("base.en")
        self.sample_rate = 16000
        self.audio_queue = queue.Queue()
        self.noise_profile = None
        self.stream = None
        self.transcription = ['']
        self.last_phrase_time = None
        self.phrase_timeout = self.args.phrase_timeout
        
        self._setup_microphone()
        print("Base model loaded.\n")

    def _setup_arguments(self):
        self.parser.add_argument("--energy_threshold", default=1000,
                               help="Energy level for mic to detect.", type=int)
        self.parser.add_argument("--record_timeout", default=2,
                               help="How real time the recording is in seconds.", type=float)
        self.parser.add_argument("--phrase_timeout", default=3,
                               help="How much empty space between recordings before we "
                                    "consider it a new line in the transcription.", type=float)
        if 'linux' in platform:
            self.parser.add_argument("--default_microphone", default='pulse',
                                    help="Default microphone name for SpeechRecognition. "
                                         "Run this with 'list' to view available Microphones.", type=str)

    def _setup_microphone(self):
        """Initialize microphone using sounddevice"""
        devices = sd.query_devices()
        input_devices = [i for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
        
        if not input_devices:
            raise ValueError("No input devices found")
            
        print("Available input devices:")
        for i in input_devices:
            print(f"{i}: {devices[i]['name']}")
            
        if 'linux' in platform and hasattr(self.args, 'default_microphone'):
            if self.args.default_microphone == 'list':
                return
            for i in input_devices:
                if self.args.default_microphone in devices[i]['name']:
                    self.device_index = i
                    break
        else:
            self.device_index = input_devices[0]  # Use first available
            
        print(f"\nUsing input device: {devices[self.device_index]['name']}")

    def _audio_callback(self, indata, frames, time, status):
        """Called for each audio block"""
        if status:
            print(f"Audio error: {status}")
        if np.any(indata):
            self.audio_queue.put(indata.copy())

    def _capture_noise_profile(self):
        """Record 1 second of ambient noise for noise reduction"""
        print("Capturing noise profile... (please stay silent)")
        with sd.InputStream(device=self.device_index,
                          samplerate=self.sample_rate,
                          channels=1,
                          dtype='float32') as stream:
            noise = stream.read(int(self.sample_rate * 1))[0]  # 1 second
            self.noise_profile = noise.flatten()
        print("Noise profile captured")

    def _process_audio(self, audio):
        """Clean and normalize audio chunk"""
        # Noise reduction
        if self.noise_profile is not None:
            audio = nr.reduce_noise(y=audio,
                                  y_noise=self.noise_profile,
                                  sr=self.sample_rate,
                                  stationary=True,
                                  prop_decrease=0.8)
        
        # Normalize audio
        max_amp = np.max(np.abs(audio))
        if max_amp > 0:
            audio = 0.9 * audio / max_amp
            
        return audio

    def _transcribe_audio(self, audio):
        """Transcribe audio using Whisper"""
        try:
            result = self.model.transcribe(
                audio=audio,
                fp16=torch.cuda.is_available(),
                language='en',
                temperature=0.0
            )
            return result['text'].strip()
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def _update_transcription(self, text):
        """Manage transcription lines with phrase timeout"""
        now = datetime.now()
        phrase_complete = False
        
        if self.last_phrase_time and (now - self.last_phrase_time).total_seconds() > self.phrase_timeout:
            phrase_complete = True
            
        self.last_phrase_time = now
        
        if phrase_complete:
            self.transcription.append(text)
        else:
            self.transcription[-1] = text

    def _clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def run(self):
        """Main processing loop"""
        self._capture_noise_profile()
        
        # Start audio stream
        self.stream = sd.InputStream(
            device=self.device_index,
            samplerate=self.sample_rate,
            blocksize=1024,
            channels=1,
            dtype='float32',
            callback=self._audio_callback
        )
        
        print("\n🎤 Listening... (Press Ctrl+C to stop)")
        
        buffer = np.array([], dtype=np.float32)
        
        with self.stream:
            while True:
                # Process all available audio chunks
                while not self.audio_queue.empty():
                    chunk = self.audio_queue.get().flatten()
                    buffer = np.concatenate((buffer, chunk))

                # Process when we have enough audio (2 seconds)
                if len(buffer) >= self.sample_rate * self.args.record_timeout:
                    # Extract chunk to process
                    process_chunk = buffer[:int(self.sample_rate * self.args.record_timeout)]
                    buffer = buffer[int(self.sample_rate * 1):]  # Keep 1 second overlap

                    # Process audio
                    clean_audio = self._process_audio(process_chunk)
                    
                    # Transcribe
                    text = self._transcribe_audio(clean_audio)
                    if text:
                        self._update_transcription(text)
                        self._clear_screen()
                        for line in self.transcription:
                            print(line)
                        print('', end='', flush=True)

                sleep(0.1)  # Prevent CPU overload

if __name__ == "__main__":
    transcriber = RealTimeTranscriber()
    try:
        transcriber.run()
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        if transcriber.stream:
            transcriber.stream.close()
        
        print("\n\nFinal Transcription:")
        for line in transcriber.transcription:
            print(line)