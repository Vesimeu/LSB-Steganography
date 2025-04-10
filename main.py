import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import time
import threading
from service import hide_message, extract_message, INPUT_DIR, OUTPUT_DIR, get_wav_info

class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WAV Steganography")
        self.root.geometry("700x600")
        self.root.configure(bg="#F5F5F5")  # Светло-бежевый фон

        # Стиль
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Helvetica", 10, "bold"), padding=8, background="#A3BFFA", foreground="#4A4A4A")
        style.map("TButton", background=[("active", "#7F9CF5")])
        style.configure("TLabel", font=("Helvetica", 10), background="#F5F5F5", foreground="#4A4A4A")
        style.configure("TEntry", fieldbackground="#FFF8E7", font=("Helvetica", 10), foreground="#4A4A4A")

        # Основной фрейм
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Поле ввода сообщения
        ttk.Label(main_frame, text="Message to Encrypt:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.message_entry = ttk.Entry(main_frame, width=50)
        self.message_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Кнопка выбора файла
        ttk.Button(main_frame, text="Select WAV File", command=self.select_file).grid(row=2, column=0, pady=10)
        self.selected_file_label = ttk.Label(main_frame, text="No file selected", font=("Helvetica", 9, "italic"))
        self.selected_file_label.grid(row=2, column=1, sticky="w", pady=10)

        # Кнопки действий
        ttk.Button(main_frame, text="Encrypt", command=self.encrypt).grid(row=3, column=0, pady=10, padx=5)
        ttk.Button(main_frame, text="Decrypt", command=self.decrypt).grid(row=3, column=1, pady=10, padx=5)

        # Поле вывода логов
        ttk.Label(main_frame, text="Logs:").grid(row=4, column=0, sticky="w", pady=(10, 5))
        self.log_text = tk.Text(main_frame, height=15, width=80, bg="#FFF8E7", fg="#4A4A4A", font=("Helvetica", 10), borderwidth=0, relief="flat")
        self.log_text.grid(row=5, column=0, columnspan=2, sticky="nsew")

        # Время выполнения
        ttk.Label(main_frame, text="Execution Time:").grid(row=6, column=0, sticky="w", pady=(10, 5))
        self.time_label = ttk.Label(main_frame, text="0.00 sec", font=("Helvetica", 9))
        self.time_label.grid(row=6, column=1, sticky="w")

        # Кнопки Clear и Exit
        ttk.Button(main_frame, text="Clear", command=self.clear_logs).grid(row=7, column=0, pady=10, padx=5)
        ttk.Button(main_frame, text="Exit", command=self.root.quit).grid(row=7, column=1, pady=10, padx=5)

        # Описание программы и GitHub
        footer_frame = ttk.Frame(main_frame, style="Footer.TFrame")
        style.configure("Footer.TFrame", background="#EDE4D3")
        footer_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")
        description = (
            "Инструмент волновой стеганографии с использованием LSB.\n"
            "GitHub: https://github.com/Vesimeu"
        )
        ttk.Label(footer_frame, text=description, justify="center", font=("Helvetica", 9), foreground="#4A4A4A", background="#EDE4D3").pack()

        # Настройка растяжения
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Переменные
        self.selected_file = None
        self.encoded_file = None
        self.loading_window = None

    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

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
            self.log(f"File Info: {os.path.basename(file_path)}")
            self.log(f"  Samples: {info['total_samples']}")
            self.log(f"  Bits: {info['total_bits']}")
            self.log(f"  Available Characters: {info['available_chars']}")
            self.log(f"  Channels: {info['nchannels']}, Rate: {info['framerate']} Hz, Duration: {info['duration']:.2f} sec")

    def encrypt(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a WAV file!")
            return

        message = self.message_entry.get()
        if not message:
            messagebox.showerror("Error", "Please enter a message!")
            return

        self.time_label.config(text="0.00 sec")
        self.show_loading("Encrypting...")
        self.encoded_file = os.path.join(OUTPUT_DIR, f"encoded_{os.path.basename(self.selected_file)}")

        def encrypt_thread():
            start_time = time.time()
            try:
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                hide_message(self.selected_file, self.encoded_file, message)
                self.log(f"Encrypted to: {os.path.basename(self.encoded_file)}")

                # Информация о зашифрованном файле
                info = get_wav_info(self.encoded_file)
                self.log(f"Encrypted File Info: {os.path.basename(self.encoded_file)}")
                self.log(f"  Samples: {info['total_samples']}")
                self.log(f"  Bits: {info['total_bits']}")
                self.log(f"  Available Characters: {info['available_chars']}")
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

        self.time_label.config(text="0.00 sec")
        self.show_loading("Decrypting...")

        def decrypt_thread():
            start_time = time.time()
            try:
                extracted = extract_message(self.encoded_file)
                self.log(f"Decrypted Message from {os.path.basename(self.encoded_file)}: {extracted}")
            except Exception as e:
                self.log(f"Decryption Error: {e}")
            finally:
                elapsed_time = time.time() - start_time
                self.root.after(0, lambda: self.time_label.config(text=f"{elapsed_time:.2f} sec"))
                self.root.after(0, self.hide_loading)

        threading.Thread(target=decrypt_thread, daemon=True).start()

    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.time_label.config(text="0.00 sec")

if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()