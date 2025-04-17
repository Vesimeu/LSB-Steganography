import wave
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
import glob
import os

def load_audio(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        params = wav_file.getparams()
        frames = wav_file.readframes(params.nframes)
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
    return audio, params.framerate

def plot_amplitude_over_time(audio, sample_rate, label, ax):
    time = np.linspace(0, len(audio) / sample_rate, num=len(audio))
    ax.plot(time, audio, label=label)
    ax.set_xlabel("Время (с)")
    ax.set_ylabel("Амплитуда")
    ax.grid(True)
    ax.legend()

def plot_frequency_spectrum(audio, sample_rate, label, ax):
    N = len(audio)
    T = 1.0 / sample_rate
    freqs = fftfreq(N, T)[:N // 2]
    y = fft(audio)
    spectrum = 2.0 / N * np.abs(y[:N // 2])

    ax.plot(freqs, spectrum, label=label)
    ax.set_xlabel("Частота [Гц]")
    ax.set_ylabel("Амплитуда")
    ax.legend()

def compare_audio_files(file_paths, output_folder="plots"):
    os.makedirs(output_folder, exist_ok=True)

    # График для амплитудно-временной характеристики
    fig_time, axs_time = plt.subplots(len(file_paths), 1, figsize=(10, 2 * len(file_paths)))

    # График для амплитудно-частотной характеристики
    fig_freq, axs_freq = plt.subplots(len(file_paths), 1, figsize=(10, 2 * len(file_paths)))

    if len(file_paths) == 1:
        axs_time = [axs_time]
        axs_freq = [axs_freq]

    for i, file_path in enumerate(file_paths):
        audio, sample_rate = load_audio(file_path)
        label = os.path.basename(file_path).split('.')[0]  # имя без расширения

        # Строим амплитудно-временную характеристику
        plot_amplitude_over_time(audio, sample_rate, label, axs_time[i])

        # Строим амплитудно-частотную характеристику
        plot_frequency_spectrum(audio, sample_rate, label, axs_freq[i])

    # Сохраняем графики
    time_plot_path = os.path.join(output_folder, "amplitude_time.png")
    freq_plot_path = os.path.join(output_folder, "amplitude_frequency.png")

    fig_time.tight_layout()
    fig_time.savefig(time_plot_path)
    plt.close(fig_time)

    fig_freq.tight_layout()
    fig_freq.savefig(freq_plot_path)
    plt.close(fig_freq)

    print(f"Графики амплитудно-временной характеристики сохранены в {time_plot_path}")
    print(f"Графики амплитудно-частотной характеристики сохранены в {freq_plot_path}")

if __name__ == "__main__":
    # Пример использования
    folder_path = 'output/'
    main_file_path = 'audio/Sample_general.wav'

    # Получаем все .wav файлы в папке
    files = glob.glob(os.path.join(folder_path, '*.wav'))

    # Добавляем основной файл из папки 'audio'
    files.insert(0, main_file_path)

    compare_audio_files(files)
