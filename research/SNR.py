import numpy as np
import scipy.io.wavfile as wav

def normalize_audio(data):
    return data / np.max(np.abs(data)) if np.max(np.abs(data)) != 0 else data

def calculate_snr(original_path, stego_path):
    # Загрузка аудиофайлов
    rate_orig, data_orig = wav.read(original_path)
    rate_stego, data_stego = wav.read(stego_path)
    print(data_orig)
    print(data_stego)
    # Проверка на совпадение частоты дискретизации
    if rate_orig != rate_stego:
        raise ValueError("Частоты дискретизации не совпадают.")

    # Приведение к одному количеству каналов (моно)
    if data_orig.ndim > 1:
        data_orig = data_orig[:, 0]
    if data_stego.ndim > 1:
        data_stego = data_stego[:, 0]

    # Обрезка до одинаковой длины
    min_len = min(len(data_orig), len(data_stego))
    data_orig = data_orig[:min_len].astype(np.float64)
    data_stego = data_stego[:min_len].astype(np.float64)

    # 🔄 Нормализация обоих сигналов
    data_orig = normalize_audio(data_orig)
    data_stego = normalize_audio(data_stego)

    # Расчёт мощностей
    signal_power = np.sum(data_orig ** 2)
    noise_power = np.sum((data_orig - data_stego) ** 2)

    if noise_power == 0:
        return float('inf')

    snr = 10 * np.log10(signal_power / noise_power)
    return snr

# Пример использования
if __name__ == "__main__":
    original_path = "audio/Sample_general.wav"
    stego_path = "output/Phaze.wav"

    snr = calculate_snr(original_path, stego_path)
    print(f"SNR: {snr:.2f} dB")
