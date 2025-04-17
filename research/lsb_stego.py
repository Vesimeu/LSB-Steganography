import wave
import numpy as np
import os
import random
import string

LOG_FILE = 'steg_log.txt'  # Имя лог-файла для записей

# Функция для записи логов о модификации сэмплов
def log_sample_info(index, original_sample, cleared_lsb, new_bit, modified_sample):
    with open(LOG_FILE, 'a') as log:
        log.write(f"Index {index} - Original: {original_sample}, Cleared LSB: {cleared_lsb}, "
                  f"New bit: {new_bit}, Modified: {modified_sample}\n")

class LSBSteganography:
    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file

    def hide_message(self, input_wav_path, output_wav_path, message):
        """
        Встраивает сообщение в аудиофайл с использованием метода LSB.
        """
        # Чтение WAV-файла
        with wave.open(input_wav_path, 'rb') as wav:
            params = wav.getparams()
            
            if params.sampwidth != 2:
                raise ValueError(f"Файл {input_wav_path} не в формате 16 бит!")
            frames = wav.readframes(wav.getnframes())
            samples = np.frombuffer(frames, dtype=np.int16)

        # Проверка диапазона сэмплов

        if np.max(samples) > 32767 or np.min(samples) < -32768:
            raise ValueError(f"Сэмплы в {input_wav_path} вне диапазона int16!")

        # Подготовка сообщения
        message += '\0'  # Добавляем завершающий символ
        bits = ''.join(format(ord(char), '08b') for char in message)
        if len(bits) > len(samples):
            raise ValueError(f"Сообщение слишком длинное для файла {input_wav_path}!")

        # Очистка лог-файла перед записью
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

        # Модификация сэмплов
        modified_samples = samples.copy().astype(np.int16)
        for i, bit in enumerate(bits):
            original_sample = modified_samples[i]
            cleared_lsb = original_sample & np.int16(-2)  # -2 = 0xFFFE в int16
            new_bit = np.int16(int(bit))  # 0 или 1
            modified_sample = cleared_lsb | new_bit

            # Запись в лог-файл для первых 100 сэмплов
            if i < 100:
                log_sample_info(i, original_sample, cleared_lsb, new_bit, modified_sample)

            if modified_sample > 32767 or modified_sample < -32768:
                raise ValueError(f"Переполнение int16 на сэмпле {i}: {modified_sample}")
            modified_samples[i] = modified_sample


        # Запись результата
        with wave.open(output_wav_path, 'wb') as wav_out:
            wav_out.setparams(params)
            wav_out.writeframes(modified_samples.tobytes())

    def extract_message(self, input_wav_path):
        """
        Извлекает сообщение из аудиофайла, скрытого с использованием метода LSB.
        """
        with wave.open(input_wav_path, 'rb') as wav:
            frames = wav.readframes(wav.getnframes())
            samples = np.frombuffer(frames, dtype=np.int16)

        bits = ''
        for i in range(len(samples)):
            bits += str(samples[i] & 1)

        message = ''
        for i in range(0, len(bits), 8):
            byte = bits[i:i + 8]
            if len(byte) == 8:
                char = chr(int(byte, 2))
                if char == '\0':
                    break
                message += char
        return message
    
    def iterative_encoding(self, audio_path, output_path, max_message_length=1024):
        """
        Итеративный метод для проверки, сколько информации можно закодировать в аудиофайл.
        Выводит только результат — максимальную длину сообщения, которое можно закодировать.
        """
        for message_length in range(200000, max_message_length + 1):
            message = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation + ' ', k=message_length))

            try:
                print(message_length)
                self.hide_message(audio_path, output_path, message)
                decoded_message = self.extract_message(output_path)
                if decoded_message == message:
                    # Если сообщение успешно закодировано и извлечено, продолжаем
                    pass
                else:
                    break
            except ValueError:
                break
        else:
            # Если цикл завершился без ошибок, значит максимальная длина сообщения = max_message_length
            print(f"Максимальная длина сообщения: {max_message_length} символов")
            return max_message_length

        print(f"Максимальная длина сообщения: {message_length - 1} символов")
        return message_length - 1

# Пример использования
if __name__ == "__main__":
    # Создание экземпляра класса
    steg = LSBSteganography()

    input_path = "audio/Sample_general.wav"  # Путь к исходному WAV-файлу
    output_path = "output/Lsb.wav"  # Путь для сохранения файла с скрытым сообщением

    with open("text_message.txt", 'r', encoding='utf-8') as txt:
        message = str(txt.read())
    
    steg.hide_message(input_path, output_path, message)

    decode_message = steg.extract_message(output_path)
    print(decode_message)
    if message == decode_message:
        print("Сообщение успешно закодировано и извлечено!")
    else:
        print("Ошибка при кодировании или извлечении сообщения!")
    print(len(decode_message))
    with open("decode_message.txt", 'w', encoding='utf-8') as txt:
        txt.write(decode_message)
