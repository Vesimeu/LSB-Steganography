import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import time
import threading
import wave
import numpy as np
from service import hide_message, extract_message, INPUT_DIR, OUTPUT_DIR, get_wav_info, read_txt_file

class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WAV Steganography")
        self.root.geometry("700x600")
        self.root.configure(bg="#F5F5F5")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Helvetica", 10, "bold"), padding=8, background="#A3BFFA", foreground="#4A4A4A")
        style.map("TButton", background=[("active", "#7F9CF5")])
        style.configure("TLabel", font=("Helvetica", 10), background="#F5F5F5", foreground="#4A4A4A")
        style.configure("TEntry", fieldbackground="#FFF8E7", font=("Helvetica", 10), foreground="#4A4A4A")
        style.configure("TCombobox", fieldbackground="#FFF8E7", font=("Helvetica", 10), foreground="#4A4A4A")

        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Поле ввода сообщения
        ttk.Label(main_frame, text="Message to Encrypt:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.message_entry = ttk.Entry(main_frame, width=50)
        self.message_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Кнопка выбора текстового файла
        ttk.Button(main_frame, text="Select TXT File", command=self.select_txt_file).grid(row=2, column=0, pady=10)
        self.txt_file_label = ttk.Label(main_frame, text="No text file selected", font=("Helvetica", 9, "italic"))
        self.txt_file_label.grid(row=2, column=1, sticky="w", pady=10)

        # Выбор количества битов
        ttk.Label(main_frame, text="Bits to Replace:").grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.bits_combobox = ttk.Combobox(main_frame, values=[1, 2, 3, 4, 5, 6, 7, 8], state="readonly", width=5)
        self.bits_combobox.set(1)
        self.bits_combobox.grid(row=3, column=1, sticky="w", pady=(0, 10))

        # Кнопка выбора WAV-файла
        ttk.Button(main_frame, text="Select WAV File", command=self.select_file).grid(row=4, column=0, pady=10)
        self.selected_file_label = ttk.Label(main_frame, text="No file selected", font=("Helvetica", 9, "italic"))
        self.selected_file_label.grid(row=4, column=1, sticky="w", pady=10)

        # Кнопки действий
        ttk.Button(main_frame, text="Encrypt", command=self.encrypt).grid(row=5, column=0, pady=10, padx=5)
        ttk.Button(main_frame, text="Decrypt", command=self.decrypt).grid(row=5, column=1, pady=10, padx=5)
        ttk.Button(main_frame, text="Analyze Difference", command=self.analyze_difference).grid(row=5, column=2, pady=10, padx=5)

        # Поле вывода логов
        ttk.Label(main_frame, text="Logs:").grid(row=6, column=0, sticky="w", pady=(10, 5))
        self.log_text = tk.Text(main_frame, height=15, width=80, bg="#FFF8E7", fg="#4A4A4A", 
                               font=("Helvetica", 10), borderwidth=0, relief="flat")
        self.log_text.grid(row=7, column=0, columnspan=3, sticky="nsew")
        
        # Настройка возможности копирования текста
        self.log_text.configure(state="normal")  # Разрешаем редактирование для копирования
        
        # Добавляем контекстное меню для копирования
        self.log_menu = tk.Menu(self.log_text, tearoff=0)
        self.log_menu.add_command(label="Copy", command=lambda: self.copy_text())
        self.log_text.bind("<Button-3>", self.show_context_menu)
        
        # Добавляем скроллбар для удобства
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=7, column=3, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # Время выполнения
        ttk.Label(main_frame, text="Execution Time:").grid(row=8, column=0, sticky="w", pady=(10, 5))
        self.time_label = ttk.Label(main_frame, text="0.00 sec", font=("Helvetica", 9))
        self.time_label.grid(row=8, column=1, sticky="w")

        # Кнопки Clear и Exit
        ttk.Button(main_frame, text="Clear", command=self.clear_logs).grid(row=9, column=0, pady=10, padx=5)
        ttk.Button(main_frame, text="Exit", command=self.root.quit).grid(row=9, column=1, pady=10, padx=5)

        # Описание программы и GitHub
        footer_frame = ttk.Frame(main_frame, style="Footer.TFrame")
        style.configure("Footer.TFrame", background="#EDE4D3")
        footer_frame.grid(row=10, column=0, columnspan=3, pady=10, sticky="ew")
        description = (
            "Инструмент волновой стеганографии с использованием LSB.\n"
            "GitHub: https://github.com/Vesimeu"
        )
        ttk.Label(footer_frame, text=description, justify="center", font=("Helvetica", 9), foreground="#4A4A4A", background="#EDE4D3").pack()

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.selected_file = None
        self.txt_file = None
        self.encoded_file = None
        self.loading_window = None

    def log(self, message):
        # Вывод в интерфейс
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        
        # Вывод в терминал
        print(message)

    def show_loading(self, message):
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Processing")
        self.loading_window.geometry("300x100")
        self.loading_window.configure(bg="#F5F5F5")
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()

        ttk.Label(self.loading_window, text=message, foreground="#4A4A4A").pack(pady=20)
        progress = ttk.Progressbar(self.loading_window, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

    def hide_loading(self):
        if self.loading_window:
            self.loading_window.destroy()
            self.loading_window = None

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file_path:
            self.selected_file = file_path
            self.selected_file_label.config(text=os.path.basename(file_path))
            info = get_wav_info(file_path)
            num_bits = int(self.bits_combobox.get())
            available_chars = (info['total_samples'] * num_bits) // 8
            self.log(f"File Info: {os.path.basename(file_path)}")
            self.log(f"  Samples: {info['total_samples']}")
            self.log(f"  Bits: {info['total_bits']}")
            self.log(f"  Available Characters (for {num_bits} bits): {available_chars}")
            self.log(f"  Channels: {info['nchannels']}, Rate: {info['framerate']} Hz, Duration: {info['duration']:.2f} sec")

    def select_txt_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.txt_file = file_path
            self.txt_file_label.config(text=os.path.basename(file_path))
            self.log(f"Selected text file: {os.path.basename(file_path)}")

    def get_quality_assessment(self, snr, changed_percent, num_bits):
        """Автоматическая оценка качества изменений с учётом num_bits."""
        if snr > 60 and changed_percent < 5 and num_bits <= 2:
            return "Незаметно"
        elif (snr > 40 and changed_percent < 10) or num_bits <= 4:
            return "Возможен лёгкий шум"
        else:
            return "Заметные искажения"

    def encrypt(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a WAV file!")
            return

        # Получаем сообщение
        if self.txt_file:
            try:
                message = read_txt_file(self.txt_file)
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return
        else:
            message = self.message_entry.get()
            if not message:
                messagebox.showerror("Error", "Please enter a message or select a text file!")
                return

        num_bits = int(self.bits_combobox.get())
        self.time_label.config(text="0.00 sec")
        self.show_loading("Encrypting...")
        self.encoded_file = os.path.join(OUTPUT_DIR, f"encoded_bits{num_bits}_{os.path.basename(self.selected_file)}")

        def encrypt_thread():
            start_time = time.time()
            try:
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                stats = hide_message(self.selected_file, self.encoded_file, message, num_bits)
                self.log(f"Encrypted to: {os.path.basename(self.encoded_file)}")
                self.log(f"Max sample difference: {stats['max_diff']}")
                self.log(f"Mean sample difference: {stats['mean_diff']:.2f}")
                self.log(f"SNR: {stats['snr']:.2f} dB")
                self.log(f"Changed samples: {stats['changed_samples']} ({stats['changed_percent']:.2f}%)")
                self.log(f"Quality assessment: {self.get_quality_assessment(stats['snr'], stats['changed_percent'], num_bits)}")

                info = get_wav_info(self.encoded_file)
                self.log(f"Encrypted File Info: {os.path.basename(self.encoded_file)}")
                self.log(f"  Samples: {info['total_samples']}")
                self.log(f"  Bits: {info['total_bits']}")
                self.log(f"  Available Characters (for {num_bits} bits): {stats['available_chars']}")
            except Exception as e:
                self.log(f"Encryption Error: {e}")
            finally:
                elapsed_time = time.time() - start_time
                self.root.after(0, lambda: self.time_label.config(text=f"{elapsed_time:.2f} sec"))
                self.root.after(0, self.hide_loading)

        threading.Thread(target=encrypt_thread, daemon=True).start()

    def decrypt(self):
        if not self.encoded_file:
            messagebox.showerror("Error", "Encrypt a file first!")
            return

        num_bits = int(self.bits_combobox.get())
        self.time_label.config(text="0.00 sec")
        self.show_loading("Decrypting...")

        def decrypt_thread():
            start_time = time.time()
            try:
                extracted = extract_message(self.encoded_file, num_bits)
                self.log(f"Decrypted Message from {os.path.basename(self.encoded_file)}: {extracted[:100]}...")
            except Exception as e:
                self.log(f"Decryption Error: {e}")
            finally:
                elapsed_time = time.time() - start_time
                self.root.after(0, lambda: self.time_label.config(text=f"{elapsed_time:.2f} sec"))
                self.root.after(0, self.hide_loading)

        threading.Thread(target=decrypt_thread, daemon=True).start()

    def analyze_difference(self):
        if not self.selected_file or not self.encoded_file:
            messagebox.showerror("Error", "Select both original and encrypted files!")
            return

        self.time_label.config(text="0.00 sec")
        self.show_loading("Analyzing...")

        def analyze_thread():
            start_time = time.time()
            try:
                with wave.open(self.selected_file, 'rb') as wav_orig:
                    frames_orig = wav_orig.readframes(wav_orig.getnframes())
                    samples_orig = np.frombuffer(frames_orig, dtype=np.int16)

                with wave.open(self.encoded_file, 'rb') as wav_enc:
                    frames_enc = wav_enc.readframes(wav_enc.getnframes())
                    samples_enc = np.frombuffer(frames_enc, dtype=np.int16)

                if len(samples_orig) != len(samples_enc):
                    raise ValueError("Files have different lengths!")

                max_diff = np.max(np.abs(samples_enc - samples_orig))
                mean_diff = np.mean(np.abs(samples_enc - samples_orig))
                signal_power = np.mean(samples_orig.astype(np.float64) ** 2)
                noise_power = np.mean((samples_enc - samples_orig).astype(np.float64) ** 2)
                snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')
                changed_samples = np.sum(samples_enc != samples_orig)
                changed_percent = (changed_samples / len(samples_orig)) * 100 if len(samples_orig) > 0 else 0

                num_bits = int(self.bits_combobox.get())
                self.log(f"Analysis of {os.path.basename(self.selected_file)} vs {os.path.basename(self.encoded_file)}:")
                self.log(f"  Max sample difference: {max_diff}")
                self.log(f"  Mean sample difference: {mean_diff:.2f}")
                self.log(f"  SNR: {snr:.2f} dB")
                self.log(f"  Changed samples: {changed_samples} ({changed_percent:.2f}%)")
                self.log(f"  Quality assessment: {self.get_quality_assessment(snr, changed_percent, num_bits)}")
            except Exception as e:
                self.log(f"Analysis Error: {e}")
            finally:
                elapsed_time = time.time() - start_time
                self.root.after(0, lambda: self.time_label.config(text=f"{elapsed_time:.2f} sec"))
                self.root.after(0, self.hide_loading)

        threading.Thread(target=analyze_thread, daemon=True).start()

    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.time_label.config(text="0.00 sec")

    def copy_text(self):
        try:
            selected_text = self.log_text.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass  # Если ничего не выделено, просто игнорируем

    def show_context_menu(self, event):
        try:
            self.log_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.log_menu.grab_release()

if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()