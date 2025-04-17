import numpy as np
import wave
from scipy.fftpack import fft, ifft

class PhaseSteganography:
    def __init__(self, segment_size=4096):
        self.N = segment_size  # длина сегмента для встраивания/извлечения

    def _stereo_to_mono(self, audio_data, n_channels):
        if n_channels == 1:
            return audio_data
        return audio_data.reshape(-1, n_channels).mean(axis=1)

    def _normalize(self, audio):
        return audio / np.max(np.abs(audio))

    def _denormalize(self, audio, dtype=np.int16):
        max_val = np.iinfo(dtype).max
        return (audio * max_val).astype(dtype)

    def _text_to_bits(self, text):
        return ''.join(f'{ord(c):08b}' for c in text)

    def _bits_to_text(self, bits):
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            if len(byte) < 8:
                break
            chars.append(chr(int(byte, 2)))
        return ''.join(chars)

    def encode_message(self, audio_path, output_path, message):
        with wave.open(audio_path, 'rb') as wav:
            params = wav.getparams()
            n_channels, sampwidth, framerate, nframes, comptype, compname = params
            frames = wav.readframes(nframes)

        audio = np.frombuffer(frames, dtype=np.int16)
        audio = self._stereo_to_mono(audio, n_channels)
        audio = self._normalize(audio)

        message += "###"
        bits = self._text_to_bits(message)

        if len(audio) < self.N:
            raise ValueError("Файл слишком короткий")

        if len(bits) > self.N // 2:
            raise ValueError("Сообщение слишком длинное для выбранного сегмента.")

        segment = audio[:self.N]
        spectrum = fft(segment)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)

        for i, bit in enumerate(bits):
            phase[i + 1] = 0 if bit == '0' else np.pi
            phase[-(i + 1)] = -phase[i + 1]

        modified = np.real(ifft(magnitude * np.exp(1j * phase)))
        new_audio = np.copy(audio)
        new_audio[:self.N] = modified

        output_int16 = self._denormalize(new_audio)

        with wave.open(output_path, 'wb') as out_wav:
            out_wav.setparams((1, 2, framerate, len(output_int16), 'NONE', 'not compressed'))
            out_wav.writeframes(output_int16.tobytes())

        print("[✓] Сообщение закодировано!")

    def decode_message(self, audio_path):
        with wave.open(audio_path, 'rb') as wav:
            n_channels, sampwidth, framerate, nframes, comptype, compname = wav.getparams()
            frames = wav.readframes(nframes)

        audio = np.frombuffer(frames, dtype=np.int16)
        audio = self._stereo_to_mono(audio, n_channels)
        audio = self._normalize(audio)

        if len(audio) < self.N:
            raise ValueError("Файл слишком короткий для извлечения")

        segment = audio[:self.N]
        spectrum = fft(segment)
        phase = np.angle(spectrum)

        bits = ''
        for i in range(1, self.N // 2):
            bits += '0' if abs(phase[i]) < np.pi / 2 else '1'

        text = self._bits_to_text(bits)
        end_idx = text.find("###")
        return text[:end_idx] if end_idx != -1 else None

    def iterative_encoding(self, audio_path, output_path, max_message_length=1024):
        """
        Итеративный метод для проверки, сколько информации можно закодировать в аудиофайл.
        Выводит только результат — максимальную длину сообщения, которое можно закодировать.
        """
        for message_length in range(1, max_message_length + 1):
            message = "A" * message_length  # Пример простого сообщения из 'A'

            try:
                self.encode_message(audio_path, output_path, message)
                decoded_message = self.decode_message(output_path)
                if decoded_message == message:
                    # Если сообщение успешно закодировано и извлечено, выводим длину
                    print(f"Максимальная длина сообщения: {message_length} символов")
                else:
                    break
            except ValueError:
                break


# === Пример использования ===
if __name__ == "__main__":
    steg = PhaseSteganography(segment_size=4096)

    input_path = "audio/Sample_general.wav"
    output_path = "output/phaze_output.wav"

    # Запускаем итеративное скрытие сообщений
    steg.iterative_encoding(input_path, output_path)
