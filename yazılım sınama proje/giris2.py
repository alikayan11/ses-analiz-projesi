import sqlite3
import tkinter as tk
from tkinter import messagebox
import subprocess  # menu.py'yi çalıştırmak için

# Veritabanı oluşturma fonksiyonu
def create_user_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Üye olma fonksiyonu
def register_user():
    username = register_username_entry.get()
    password = register_password_entry.get()
    confirm_password = confirm_password_entry.get()

    if not username or not password or not confirm_password:
        messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
        return
    
    if password != confirm_password:
        messagebox.showerror("Hata", "Şifreler eşleşmiyor!")
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        messagebox.showerror("Hata", "Bu kullanıcı adı zaten alınmış!")
    else:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        messagebox.showinfo("Başarılı", "Kayıt başarılı!")
    
    conn.close()

# Giriş fonksiyonu
def login_user():
    username = login_username_entry.get()
    password = login_password_entry.get()

    if not username or not password:
        messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        messagebox.showinfo("Başarılı", "Giriş başarılı!")
        login_screen.destroy()  # Giriş ekranını kapat
        subprocess.run(['python', 'menu.py'])  # menu.py'yi çalıştır
    else:
        messagebox.showerror("Hata", "Kullanıcı adı veya şifre yanlış!")
    
    conn.close()

# Tkinter arayüzü oluştur
def open_registration_screen():
    register_screen = tk.Toplevel(app)
    register_screen.title("Üye Ol")
    register_screen.geometry("400x300")

    tk.Label(register_screen, text="Kullanıcı Adı:").pack(pady=5)
    global register_username_entry
    register_username_entry = tk.Entry(register_screen)
    register_username_entry.pack(pady=5)

    tk.Label(register_screen, text="Şifre:").pack(pady=5)
    global register_password_entry
    register_password_entry = tk.Entry(register_screen, show="*")
    register_password_entry.pack(pady=5)

    tk.Label(register_screen, text="Şifreyi Onayla:").pack(pady=5)
    global confirm_password_entry
    confirm_password_entry = tk.Entry(register_screen, show="*")
    confirm_password_entry.pack(pady=5)

    tk.Button(register_screen, text="Kaydol", command=register_user).pack(pady=10)

def open_login_screen():
    global login_screen
    login_screen = tk.Toplevel(app)
    login_screen.title("Giriş Yap")
    login_screen.geometry("400x250")

    tk.Label(login_screen, text="Kullanıcı Adı:").pack(pady=5)
    global login_username_entry
    login_username_entry = tk.Entry(login_screen)
    login_username_entry.pack(pady=5)

    tk.Label(login_screen, text="Şifre:").pack(pady=5)
    global login_password_entry
    login_password_entry = tk.Entry(login_screen, show="*")
    login_password_entry.pack(pady=5)

    tk.Button(login_screen, text="Giriş Yap", command=login_user).pack(pady=10)

# Ana Tkinter arayüzü
app = tk.Tk()
app.title("Ses ve Sahip Kaydı")
app.geometry("700x600")

# Giriş ve Üye Ol butonları
tk.Button(app, text="Giriş Yap", command=open_login_screen).pack(pady=10)
tk.Button(app, text="Üye Ol", command=open_registration_screen).pack(pady=10)

# Veritabanını oluştur
create_user_database()

# Tkinter döngüsünü başlat
app.mainloop()