import wave
import numpy as np
import os

INPUT_DIR = "template/input"
OUTPUT_DIR = "template/output"


def hide_message(input_wav_path, output_wav_path, message):
    # Чтение WAV-файла
    with wave.open(input_wav_path, 'rb') as wav:
        params = wav.getparams()
        print(f"Параметры файла {input_wav_path}: {params}")
        if params.sampwidth != 2:
            raise ValueError(f"Файл {input_wav_path} не в формате 16 бит!")
        frames = wav.readframes(wav.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16)

    # Проверка диапазона сэмплов
    print(f"Исходные сэмплы: min={np.min(samples)}, max={np.max(samples)}")
    if np.max(samples) > 32767 or np.min(samples) < -32768:
        raise ValueError(f"Сэмплы в {input_wav_path} вне диапазона int16!")

    # Подготовка сообщения
    message += '\0'  # Добавляем завершающий символ
    bits = ''.join(format(ord(char), '08b') for char in message)
    if len(bits) > len(samples):
        raise ValueError(f"Сообщение слишком длинное для файла {input_wav_path}!")

    # Модификация сэмплов
    modified_samples = samples.copy().astype(np.int16)
    for i, bit in enumerate(bits):
        original_sample = modified_samples[i]
        # Обнуляем младший бит с помощью знаковой маски
        cleared_lsb = original_sample & np.int16(-2)  # -2 = 0xFFFE в int16
        # Добавляем новый бит
        new_bit = np.int16(int(bit))  # 0 или 1
        modified_sample = cleared_lsb | new_bit

        # Отладочная информация для первых 5 сэмплов
        if i < 5:
            print(f"Сэмпл {i}: исходное={original_sample}, cleared_lsb={cleared_lsb}, bit={new_bit}, результат={modified_sample}")

        # Проверка на переполнение
        if modified_sample > 32767 or modified_sample < -32768:
            raise ValueError(f"Переполнение int16 на сэмпле {i}: {modified_sample}")
        modified_samples[i] = modified_sample

    print(f"Изменённые сэмплы: min={np.min(modified_samples)}, max={np.max(modified_samples)}")

    # Запись результата
    with wave.open(output_wav_path, 'wb') as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(modified_samples.tobytes())

def extract_message(input_wav_path):
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


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    secret_message = "Hello, this is a secret!"

    print("Шифрование сообщения в WAV-файлы...")
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".wav"):
            input_wav_path = os.path.join(INPUT_DIR, filename)
            output_wav_path = os.path.join(OUTPUT_DIR, f"encoded_{filename}")
            try:
                hide_message(input_wav_path, output_wav_path, secret_message)
                print(f"Сообщение спрятано в {output_wav_path}")
            except Exception as e:
                print(f"Ошибка при обработке {filename}: {e}")

    print("\nИзвлечение сообщения из WAV-файлов...")
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(".wav"):
            wav_path = os.path.join(OUTPUT_DIR, filename)
            try:
                extracted = extract_message(wav_path)
                print(f"Извлечённое сообщение из {filename}: {extracted}")
            except Exception as e:
                print(f"Ошибка при извлечении из {filename}: {e}")


if __name__ == "__main__":
    main()