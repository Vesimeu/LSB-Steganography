import numpy as np
import matplotlib.pyplot as plt
import wave
import os
import scipy.fftpack as fft

def analyze_leakage(original_file, modified_file):
    """
    Оценка утечки информации путем сравнения частотных спектров оригинального и модифицированного аудиофайла.
    
    :param original_file: Путь к оригинальному аудиофайлу
    :param modified_file: Путь к модифицированному аудиофайлу (с скрытыми данными)
    :return: Степень утечки информации
    """
    # Чтение аудиофайлов
    def read_audio(file_path):
        with wave.open(file_path, 'rb') as audio:
            params = audio.getparams()
            frames = audio.readframes(params.nframes)
            audio_data = np.frombuffer(frames, dtype=np.int16)
        return audio_data, params

    original_data, _ = read_audio(original_file)
    modified_data, _ = read_audio(modified_file)
    
    # Преобразование в частотную область с помощью FFT
    def fft_analysis(data):
        # Выполняем FFT
        spectrum = fft.fft(data)
        return np.abs(spectrum)  # Модуль спектра
    
    original_spectrum = fft_analysis(original_data)
    modified_spectrum = fft_analysis(modified_data)
    
    # Приводим спектры к одинаковой длине
    min_length = min(len(original_spectrum), len(modified_spectrum))
    original_spectrum = original_spectrum[:min_length]
    modified_spectrum = modified_spectrum[:min_length]
    
    # Сравнение спектров: использование корреляции для выявления различий
    correlation = np.corrcoef(original_spectrum, modified_spectrum)[0, 1]
    
    # Визуализация спектров
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(original_spectrum)
    plt.title("Оригинальный спектр")
    plt.subplot(2, 1, 2)
    plt.plot(modified_spectrum)
    plt.title("Спектр с скрытыми данными")
    plt.show()
    
    # Степень утечки может быть оценена через корреляцию: чем она ниже, тем выше утечка
    leakage_score = 1 - correlation  # Чем больше корреляция, тем меньше утечка
    
    return leakage_score

# Пример использования
original_file = 'audio/Sample_general.wav'  # Путь к оригинальному файлу
modified_file = 'output/Phaze.wav'  # Путь к файлу с внедренными данными

leakage_score = analyze_leakage(original_file, modified_file)
print(f'Степень утечки информации (Leakage): {leakage_score:.4f}')
