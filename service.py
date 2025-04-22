import wave
import numpy as np
import os

INPUT_DIR = "template/input"
OUTPUT_DIR = "template/output"
LOG_FILE = "log_simple.txt"


def log_sample_info(i, original_sample, cleared_bits, new_bits, modified_sample):
    """Запись информации о сэмплах в лог-файл."""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(
            f"Сэмпл {i}: исходное={original_sample}, cleared_bits={cleared_bits}, new_bits={new_bits}, результат={modified_sample}\n")


def read_txt_file(txt_path):
    """Чтение текста из .txt файла."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Ошибка при чтении файла {txt_path}: {e}")


def hide_message(input_wav_path, output_wav_path, message, num_bits=1):
    """Шифрование сообщения в WAV-файл с заменой num_bits младших битов."""
    if not 1 <= num_bits <= 8:
        raise ValueError("num_bits должен быть от 1 до 8!")

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
    if np.max(np.abs(samples)) > 32767:
        raise ValueError(f"Сэмплы в {input_wav_path} вне диапазона int16!")

    # Подготовка сообщения
    message += '\0'
    bits = ''.join(format(ord(char), '08b') for char in message)
    required_samples = len(bits) // num_bits + (1 if len(bits) % num_bits else 0)

    # Проверка доступного количества символов
    available_chars = (len(samples) * num_bits) // 8
    if len(message) > available_chars:
        raise ValueError(f"Сообщение слишком длинное! Максимум {available_chars} символов для {num_bits} битов.")

    if required_samples > len(samples):
        raise ValueError(f"Сообщение слишком длинное для файла {input_wav_path} с {num_bits} битами на сэмпл!")

    # Очистка лог-файла
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    # Модификация сэмплов
    modified_samples = samples.copy().astype(np.int16)
    bit_index = 0
    changed_samples = 0
    for i in range(len(modified_samples)):
        if bit_index >= len(bits):
            break
        original_sample = modified_samples[i]
        mask = np.int16(~((1 << num_bits) - 1))
        cleared_bits = original_sample & mask
        new_bits = 0
        for j in range(num_bits - 1, -1, -1):
            if bit_index < len(bits):
                new_bits |= (int(bits[bit_index]) << j)
                bit_index += 1
            else:
                break
        new_bits = np.int16(new_bits)
        modified_sample = cleared_bits | new_bits

        if i < 100:
            log_sample_info(i, original_sample, cleared_bits, new_bits, modified_sample)

        if modified_sample != original_sample:
            changed_samples += 1
        if modified_sample > 32767 or modified_sample < -32768:
            raise ValueError(f"Переполнение int16 на сэмпле {i}: {modified_sample}")
        modified_samples[i] = modified_sample

    print(f"Изменённые сэмплы: min={np.min(modified_samples)}, max={np.max(modified_samples)}")

    # Запись результата
    with wave.open(output_wav_path, 'wb') as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(modified_samples.tobytes())

    # Анализ разницы
    max_diff = np.max(np.abs(modified_samples - samples))
    mean_diff = np.mean(np.abs(modified_samples - samples))
    signal_power = np.mean(samples.astype(np.float64) ** 2)
    noise_power = np.mean((modified_samples - samples).astype(np.float64) ** 2)
    snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')
    changed_percent = (changed_samples / len(samples)) * 100 if len(samples) > 0 else 0

    return {
        "max_diff": max_diff,
        "mean_diff": mean_diff,
        "snr": snr,
        "changed_samples": changed_samples,
        "changed_percent": changed_percent,
        "available_chars": available_chars
    }


def extract_message(input_wav_path, num_bits=1):
    """Извлечение сообщения из WAV-файла с учётом num_bits."""
    if not 1 <= num_bits <= 8:
        raise ValueError("num_bits должен быть от 1 до 8!")

    with wave.open(input_wav_path, 'rb') as wav:
        frames = wav.readframes(wav.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16)

    bits = ''
    for sample in samples:
        for j in range(num_bits - 1, -1, -1):
            bits += str((sample >> j) & 1)

    message = ''
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        if len(byte) == 8:
            char = chr(int(byte, 2))
            if char == '\0':
                break
            message += char
    return message


def get_wav_info(wav_path):
    """Получение информации о WAV-файле."""
    with wave.open(wav_path, 'rb') as wav:
        params = wav.getparams()
        nframes = params.nframes
        nchannels = params.nchannels
        sampwidth = params.sampwidth
        framerate = params.framerate

        total_samples = nframes * nchannels
        total_bits = total_samples * sampwidth * 8

    return {
        "total_samples": total_samples,
        "total_bits": total_bits,
        "nchannels": nchannels,
        "framerate": framerate,
        "duration": nframes / framerate
    }