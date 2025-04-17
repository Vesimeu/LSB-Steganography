import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate
import os


class EchoHidingSteganography:
    def __init__(self, delay_0=100, delay_1=200, attenuation=0.6):
        self.delay_0 = delay_0
        self.delay_1 = delay_1
        self.attenuation = attenuation

    def _text_to_bits(self, text):
        return ''.join(f'{ord(c):08b}' for c in text)

    def _bits_to_text(self, bits):
        chars = [chr(int(bits[i:i + 8], 2)) for i in range(0, len(bits), 8)]
        return ''.join(chars)

    def encode(self, input_wav_path, output_wav_path, message):
        rate, data = wavfile.read(input_wav_path)

        if data.ndim > 1:
            data = data[:, 0]  # Только один канал

        message_bits = self._text_to_bits(message)
        frame_size = int(len(data) / len(message_bits))
        encoded = np.copy(data)

        for i, bit in enumerate(message_bits):
            start = i * frame_size
            end = start + frame_size
            delay = self.delay_0 if bit == '0' else self.delay_1

            if end - start <= delay:
                continue  # Фрейм слишком маленький для эха

            frame = encoded[start:end]
            echo = np.zeros_like(frame)
            echo[delay:] = frame[:-delay] * self.attenuation
            encoded[start:end] = frame + echo

        os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
        wavfile.write(output_wav_path, rate, encoded.astype(np.int16))
        print(f"[+] Echo-скрытие завершено. Файл сохранён как: {output_wav_path}")

    def decode(self, encoded_wav_path, message_length):
        rate, data = wavfile.read(encoded_wav_path)

        if data.ndim > 1:
            data = data[:, 0]

        total_bits = message_length * 8
        frame_size = int(len(data) / total_bits)
        decoded_bits = ''

        for i in range(total_bits):
            start = i * frame_size
            end = start + frame_size
            frame = data[start:end]

            if end - start <= max(self.delay_0, self.delay_1):
                decoded_bits += '0'
                continue

            # Создаем опозданные версии сигнала
            frame_0 = frame[:-self.delay_0]
            delayed_0 = frame[self.delay_0:]

            frame_1 = frame[:-self.delay_1]
            delayed_1 = frame[self.delay_1:]

            # Корреляция между оригиналом и задержанным сигналом
            corr_0 = np.corrcoef(frame_0, delayed_0)[0, 1]
            corr_1 = np.corrcoef(frame_1, delayed_1)[0, 1]

            decoded_bits += '0' if corr_0 > corr_1 else '1'

        return self._bits_to_text(decoded_bits)


if __name__ == "__main__":
    input_wav = "audio/Sample_general.wav"
    output_wav = "output/Echo.wav"
    message = "hello"

    stego = EchoHidingSteganography()
    stego.encode(input_wav, output_wav, message)

    decoded = stego.decode(output_wav, message_length=len(message))
    print("Decoded message:", decoded)
