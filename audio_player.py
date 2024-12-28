import tkinter as tk
from tkinter import ttk, filedialog
import pygame
import os
from tkinter import messagebox
import shutil
from mutagen import File
from mutagen.mp3 import MP3
import threading
import time

class AudioListItem(ttk.Frame):
    def __init__(self, parent, filename, play_callback, download_callback):
        super().__init__(parent)
        
        # Botón de reproducción
        self.play_button = ttk.Button(self, text="▶", width=3, 
                                    command=lambda: play_callback(filename))
        self.play_button.pack(side=tk.LEFT, padx=(5, 10))
        
        # Nombre del archivo
        self.label = ttk.Label(self, text=filename)
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Botón de descarga
        self.download_button = ttk.Button(self, text="⭳", width=3,
                                        command=lambda: download_callback(filename))
        self.download_button.pack(side=tk.RIGHT, padx=5)

class AudioPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reproductor de Audio")
        self.root.geometry("800x600")
        
        # Configurar el tema y estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Variables
        self.current_file = None
        self.is_playing = False
        self.audio_length = 0
        self.audio_pos = 0
        
        # Inicializar pygame
        pygame.mixer.init()
        
        # Directorio de audio predeterminado
        self.audio_dir = "./audios"
        
        # Crear interfaz
        self.create_widgets()
        self.load_audio_files()
        
        # Iniciar thread para actualizar progreso
        self.update_thread = threading.Thread(target=self.update_progress, daemon=True)
        self.update_thread.start()

    def create_widgets(self):
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame superior para el directorio
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dir_frame, text="Directorio:").pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.dir_entry.insert(0, self.audio_dir)
        
        ttk.Button(dir_frame, text="Buscar", command=self.select_directory).pack(side=tk.LEFT)

        # Canvas y Scrollbar para la lista de archivos
        self.canvas = tk.Canvas(main_frame, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, 
                                command=self.canvas.yview)
        
        # Frame contenedor para los items de audio
        self.files_frame = ttk.Frame(self.canvas)
        self.files_frame.bind("<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Configurar canvas
        self.canvas.create_window((0, 0), window=self.files_frame, anchor="nw", 
                                width=self.canvas.winfo_reqwidth())
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Empaquetar elementos
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frame para controles globales
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)

        # Información del archivo
        self.info_label = ttk.Label(controls_frame, text="No hay archivo seleccionado")
        self.info_label.pack(fill=tk.X)

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(controls_frame, from_=0, to=100, 
                                    orient=tk.HORIZONTAL, variable=self.progress_var,
                                    command=self.seek_audio)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Control de volumen
        volume_frame = ttk.Frame(controls_frame)
        volume_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(volume_frame, text="🔈").pack(side=tk.LEFT)
        self.volume_var = tk.DoubleVar(value=70)
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, 
                                    orient=tk.HORIZONTAL, variable=self.volume_var,
                                    command=self.change_volume)
        self.volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(volume_frame, text="🔊").pack(side=tk.LEFT)

    def select_directory(self):
        new_dir = filedialog.askdirectory(initialdir=self.audio_dir)
        if new_dir:
            self.audio_dir = new_dir
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, new_dir)
            self.load_audio_files()

    def update_progress(self):
        while True:
            if self.is_playing and pygame.mixer.music.get_busy():
                self.audio_pos = pygame.mixer.music.get_pos() / 1000
                progress = (self.audio_pos / self.audio_length) * 100
                self.progress_var.set(progress)
            time.sleep(0.1)

    def seek_audio(self, value):
        if self.current_file and self.audio_length > 0:
            position = float(value) * self.audio_length / 100
            pygame.mixer.music.play(start=position)
            self.audio_pos = position

    def change_volume(self, value):
        volume = float(value) / 100
        pygame.mixer.music.set_volume(volume)

    def get_audio_length(self, filepath):
        try:
            audio = MP3(filepath)
            return audio.info.length
        except:
            try:
                audio = File(filepath)
                return audio.info.length
            except:
                return 0

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def play_audio(self):
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                messagebox.showwarning("Aviso", "Por favor selecciona un archivo")
                return

            filename = self.file_listbox.get(selection[0])
            filepath = os.path.join(self.audio_dir, filename)

            if self.current_file != filepath:
                self.current_file = filepath
                self.audio_length = self.get_audio_length(filepath)
                pygame.mixer.music.load(filepath)
                self.info_label.config(text=f"{filename} - {self.format_time(self.audio_length)}")

            pygame.mixer.music.play()
            self.is_playing = True
            self.play_button.config(text="⏸")

        except Exception as e:
            messagebox.showerror("Error", f"Error al reproducir: {str(e)}")

    def stop_audio(self):
        pygame.mixer.music.stop()
        
    def download_audio(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor selecciona un archivo")
            return
            
        filename = self.file_listbox.get(selection[0])
        source_path = os.path.join(self.audio_dir, filename)
        
        # Crear directorio de descargas si no existe
        download_dir = "./downloads"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # Copiar archivo
        try:
            shutil.copy2(source_path, os.path.join(download_dir, filename))
            messagebox.showinfo("Éxito", f"Archivo descargado en: {download_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al descargar: {str(e)}")

    def load_audio_files(self):
        # Limpiar lista actual
        for widget in self.files_frame.winfo_children():
            widget.destroy()

        # Verificar que el directorio existe
        if not os.path.exists(self.audio_dir):
            messagebox.showerror("Error", "Directorio de audio no encontrado")
            return

        # Obtener archivos de audio
        audio_files = [f for f in os.listdir(self.audio_dir) 
                      if f.endswith(('.mp3', '.wav', '.ogg'))]

        # Crear items para cada archivo
        for file in audio_files:
            item = AudioListItem(self.files_frame, file, 
                               self.play_audio_file, self.download_audio_file)
            item.pack(fill=tk.X, padx=5, pady=2)

    def play_audio_file(self, filename):
        try:
            filepath = os.path.join(self.audio_dir, filename)

            if self.current_file != filepath:
                self.current_file = filepath
                self.audio_length = self.get_audio_length(filepath)
                pygame.mixer.music.load(filepath)
                self.info_label.config(text=f"{filename} - {self.format_time(self.audio_length)}")

            if not self.is_playing:
                pygame.mixer.music.play()
                self.is_playing = True
            else:
                pygame.mixer.music.pause()
                self.is_playing = False

            # Actualizar botones de reproducción
            for widget in self.files_frame.winfo_children():
                if isinstance(widget, AudioListItem):
                    if widget.label['text'] == filename:
                        widget.play_button['text'] = "⏸" if self.is_playing else "▶"
                    else:
                        widget.play_button['text'] = "▶"

        except Exception as e:
            messagebox.showerror("Error", f"Error al reproducir: {str(e)}")

    def download_audio_file(self, filename):
        source_path = os.path.join(self.audio_dir, filename)
        
        # Crear directorio de descargas si no existe
        download_dir = "./downloads"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # Copiar archivo
        try:
            shutil.copy2(source_path, os.path.join(download_dir, filename))
            messagebox.showinfo("Éxito", f"Archivo descargado en: {download_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al descargar: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioPlayerApp(root)
    root.mainloop() 