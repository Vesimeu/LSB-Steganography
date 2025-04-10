import tkinter as tk
from tkinter import ttk, messagebox
import os
import time
import threading
from service import hide_message, extract_message, INPUT_DIR, OUTPUT_DIR

class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Стеганография в WAV")
        self.root.geometry("700x500")

        # Основной фрейм
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Поле ввода сообщения
        ttk.Label(main_frame, text="Введите сообщение для шифрования:").grid(row=0, column=0, sticky="w", pady=5)
        self.message_entry = ttk.Entry(main_frame, width=50)
        self.message_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        # Кнопки
        ttk.Button(main_frame, text="Зашифровать", command=self.encrypt).grid(row=2, column=0, pady=10, padx=5)
        ttk.Button(main_frame, text="Расшифровать", command=self.decrypt).grid(row=2, column=1, pady=10, padx=5)

        # Поле вывода логов
        ttk.Label(main_frame, text="Логи:").grid(row=3, column=0, sticky="w", pady=5)
        self.log_text = tk.Text(main_frame, height=15, width=80)
        self.log_text.grid(row=4, column=0, columnspan=2, sticky="nsew")

        # Время выполнения
        ttk.Label(main_frame, text="Время выполнения:").grid(row=5, column=0, sticky="w", pady=5)
        self.time_label = ttk.Label(main_frame, text="0.00 сек")
        self.time_label.grid(row=5, column=1, sticky="w")

        # Настройка растяжения
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Загрузочное окно
        self.loading_window = None

    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def show_loading(self, message):
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Пожалуйста, подождите")
        self.loading_window.geometry("300x100")
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()

        ttk.Label(self.loading_window, text=message).pack(pady=20)
        progress = ttk.Progressbar(self.loading_window, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

    def hide_loading(self):
        if self.loading_window:
            self.loading_window.destroy()
            self.loading_window = None

    def encrypt(self):
        message = self.message_entry.get()
        if not message:
            messagebox.showerror("Ошибка", "Введите сообщение!")
            return

        self.log_text.delete(1.0, tk.END)
        self.time_label.config(text="0.00 сек")
        self.show_loading("Шифрование...")

        def encrypt_thread():
            start_time = time.time()
            try:
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)

                for filename in os.listdir(INPUT_DIR):
                    if filename.endswith(".wav"):
                        input_wav_path = os.path.join(INPUT_DIR, filename)
                        output_wav_path = os.path.join(OUTPUT_DIR, f"encoded_{filename}")
                        hide_message(input_wav_path, output_wav_path, message)
                        self.log(f"Сообщение спрятано в {output_wav_path}")
            except Exception as e:
                self.log(f"Ошибка при шифровании: {e}")
            finally:
                elapsed_time = time.time() - start_time
                self.root.after(0, lambda: self.time_label.config(text=f"{elapsed_time:.2f} сек"))
                self.root.after(0, self.hide_loading)

        threading.Thread(target=encrypt_thread, daemon=True).start()

    def decrypt(self):
        self.log_text.delete(1.0, tk.END)
        self.time_label.config(text="0.00 сек")
        self.show_loading("Дешифрование...")

        def decrypt_thread():
            start_time = time.time()
            try:
                for filename in os.listdir(OUTPUT_DIR):
                    if filename.endswith(".wav"):
                        wav_path = os.path.join(OUTPUT_DIR, filename)
                        extracted = extract_message(wav_path)
                        self.log(f"Извлечённое сообщение из {filename}: {extracted}")
            except Exception as e:
                self.log(f"Ошибка при дешифровании: {e}")
            finally:
                elapsed_time = time.time() - start_time
                self.root.after(0, lambda: self.time_label.config(text=f"{elapsed_time:.2f} сек"))
                self.root.after(0, self.hide_loading)

        threading.Thread(target=decrypt_thread, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()