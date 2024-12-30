import sqlite3
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import sounddevice as sd
import wave
import threading
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import librosa

# Veritabanını oluştur ve tabloyu tanımla
def create_database():
    conn = sqlite3.connect("audio_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audio_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name TEXT NOT NULL,
            file_path TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Ses dosyasını ve sahibi adını veritabanına kaydet
def save_to_database(owner_name, file_path):
    conn = sqlite3.connect("audio_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO audio_data (owner_name, file_path) VALUES (?, ?)", (owner_name, file_path))
    conn.commit()
    conn.close()

# Ses dosyasını seçmek için fonksiyon
def select_file():
    file_path = filedialog.askopenfilename(
        title="Ses Dosyasını Seç",
        filetypes=[("Ses Dosyaları", ".mp3;.wav;.aac;.ogg")]
    )
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)

# Kaydet butonunun işlevi
def save_data():
    owner_name = name_entry.get()
    file_path = file_entry.get()

    if not owner_name or not file_path:
        messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
        return

    if not os.path.exists(file_path):
        messagebox.showerror("Hata", "Seçilen dosya bulunamadı!")
        return

    save_to_database(owner_name, file_path)
    messagebox.showinfo("Başarılı", "Veriler başarıyla kaydedildi!")
    name_entry.delete(0, tk.END)
    file_entry.delete(0, tk.END)

# Veritabanındaki verileri listelemek için fonksiyon
def list_data():
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("audio_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audio_data")
    rows = cursor.fetchall()
    for row in rows:
        tree.insert("", tk.END, values=row)
    conn.close()

# Ses kaydı için değişkenler
is_recording = False
output_file = ""

# Ses kaydını başlat
def start_recording():
    global is_recording, output_file
    owner_name = name_entry.get()
    if not owner_name:
        messagebox.showerror("Hata", "Lütfen sahibin adını girin!")
        return

    output_file = f"{owner_name}_recording.wav"
    is_recording = True
    threading.Thread(target=record_audio, args=(output_file,)).start()
    messagebox.showinfo("Bilgi", "Ses kaydı başladı!")

# Ses kaydını durdur
def stop_recording():
    global is_recording
    is_recording = False
    messagebox.showinfo("Bilgi", "Ses kaydı durduruldu ve kaydedildi!")
    file_entry.delete(0, tk.END)
    file_entry.insert(0, output_file)

# Ses kaydı işlevi
def record_audio(file_path):
    global is_recording
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(44100)  # 44.1kHz
        with sd.InputStream(samplerate=44100, channels=1, dtype="int16") as stream:
            while is_recording:
                data = stream.read(1024)[0]
                wf.writeframes(data)

# Dalga formu ve spektrogram görüntüleme
def display_waveform_and_spectrogram():
    file_path = file_entry.get()
    if not file_path or not os.path.exists(file_path):
        messagebox.showwarning("Hata", "Lütfen geçerli bir ses dosyası seçin!")
        return

    # WAV dosyasını yükle
    sample_rate, data = wavfile.read(file_path)

    # Tek kanallı hale getir (mono)
    if len(data.shape) > 1:
        data = data.mean(axis=1)

    # Spektrogram oluştur
    fig, axs = plt.subplots(2, 1, figsize=(10, 6))

    # Zaman alanında göster
    axs[0].plot(data)
    axs[0].set_title("Waveform")
    axs[0].set_xlabel("Sample")
    axs[0].set_ylabel("Amplitude")

    # Spektrogram
    axs[1].specgram(data, Fs=sample_rate, cmap="viridis")
    axs[1].set_title("Spectrogram")
    axs[1].set_xlabel("Time (s)")
    axs[1].set_ylabel("Frequency (Hz)")

    plt.colorbar(axs[1].images[0], ax=axs[1], orientation='horizontal', pad=0.2)
    plt.tight_layout()
    plt.show()

# Ses tanıma modeli oluşturma ve değerlendirme
def train_and_evaluate_model():
    conn = sqlite3.connect("audio_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, owner_name FROM audio_data")
    rows = cursor.fetchall()

    features = []
    labels = []

    for file_path, owner_name in rows:
        if os.path.exists(file_path):
            try:
                audio, sample_rate = librosa.load(file_path, res_type='kaiser_fast')
                mfcc = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
                features.append(np.mean(mfcc.T, axis=0))
                labels.append(owner_name)
            except Exception as e:
                print(f"Hata: {e}")

    conn.close()

    if not features or not labels:
        messagebox.showerror("Hata", "Model eğitimi için yeterli veri yok!")
        return

    # Veriyi böl ve modeli eğit
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Tahmin yap ve metrikleri hesapla
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')

    messagebox.showinfo("Model Sonuçları", f"Accuracy: {accuracy:.2f}\nF1 Score: {f1:.2f}")

# Tkinter arayüzü oluştur
app = tk.Tk()
app.title("Ses ve Sahip Kaydı")
app.geometry("700x600")

# Etiketler ve giriş alanları
name_label = tk.Label(app, text="Sahibin Adı:")
name_label.pack(pady=5)
name_entry = tk.Entry(app, width=50)
name_entry.pack(pady=5)

file_label = tk.Label(app, text="Ses Dosyası:")
file_label.pack(pady=5)
file_frame = tk.Frame(app)
file_frame.pack(pady=5)
file_entry = tk.Entry(file_frame, width=40)
file_entry.pack(side=tk.LEFT, padx=5)
file_button = tk.Button(file_frame, text="Seç", command=select_file)
file_button.pack(side=tk.LEFT)

# Kaydet butonu (Kırmızı)
save_button = tk.Button(app, text="Kaydet", command=save_data, bg="red")
save_button.pack(pady=10)

# Listeleme butonu
list_button = tk.Button(app, text="Listele", command=list_data)
list_button.pack(pady=10)

# Ses kaydı butonları
record_button = tk.Button(app, text="Kayda Başla", command=start_recording)
record_button.pack(pady=5)
stop_button = tk.Button(app, text="Kaydı Durdur", command=stop_recording)
stop_button.pack(pady=5)

# Dalga formu ve spektrogram gösterme butonu
plot_button = tk.Button(app, text="Dalga Formu ve Spektrogram Göster", command=display_waveform_and_spectrogram)
plot_button.pack(pady=10)

# Model eğitimi ve değerlendirme butonu
train_button = tk.Button(app, text="Model Eğit ve Değerlendir", command=train_and_evaluate_model)
train_button.pack(pady=10)

# Listeleme alanı (Treeview)
columns = ("ID", "Sahip Adı", "Dosya Yolu")
tree = ttk.Treeview(app, columns=columns, show="headings")
tree.heading("ID", text="ID")
tree.heading("Sahip Adı", text="Sahip Adı")
tree.heading("Dosya Yolu", text="Dosya Yolu")
tree.pack(pady=10, fill=tk.BOTH, expand=True)

# Veritabanını oluştur
create_database()

# Tkinter döngüsünü başlat
app.mainloop()
