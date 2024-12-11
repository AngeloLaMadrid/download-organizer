from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import shutil
import winreg
from typing import Dict, List, Tuple
import logging
import signal
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import deque

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variable para desactivar los prints
ENABLE_PRINTS = False

# Constantes
EXTENSIONS: Dict[str, List[str]] = {
    'videos': ['.avi', '.flv', '.m4v', '.mkv', '.mov', '.mp4', '.wmv', '.webm', '.3gp'],
    'documents': ['.csv', '.doc', '.docx', '.odt', '.pdf', '.ppt', '.pptx', '.txt', '.xlsx'],
    'music': ['.aac', '.flac', '.m4a', '.midi', '.mp3', '.ogg', '.wav', '.wma'],
    'programs': ['.app', '.bat', '.cmd', '.dll', '.exe', '.jar', '.msi', '.py'],
    'compressed': ['.7z', '.bz2', '.gz', '.iso', '.rar', '.tar', '.xz', '.zip'],
    'images': ['.bmp', '.gif', '.ico', '.jpeg', '.jpg', '.png', '.svg', '.tiff', '.webp'],
    'others': []
}

TEMP_EXTENSIONS = ['.crdownload', '.part', '.tmp']

CONFIG = {
    'enable_icons': True,
    'move_folders': True
}

COLORS = {
    'success': '\033[92m',
    'error': '\033[91m',
    'info': '\033[96m',
    'warning': '\033[93m',
    'reset': '\033[0m'
}

# Registro de archivos procesados
processed_files = deque(maxlen=10)

def print_colored(message: str, color: str) -> None:
    if ENABLE_PRINTS:
        print(f"{COLORS.get(color, '')}{message}{COLORS['reset']}")
    logging.info(message)

def find_downloads_folder() -> str:
    """Encuentra la carpeta de descargas del usuario."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            downloads_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            if os.path.exists(downloads_path):
                return downloads_path
    except FileNotFoundError:
        logging.warning("No se encontró la clave del registro.")
    except OSError as e:
        logging.error(f"Error al acceder al registro: {e}")

    user_profile = os.environ.get('USERPROFILE', '')
    for folder in ['Downloads', 'Descargas']:
        path = os.path.join(user_profile, folder)
        if os.path.exists(path):
            return path
    return os.path.join(user_profile, 'Downloads')

def get_category(filename: str) -> str:
    """Determina la categoría de un archivo por su extensión."""
    ext = os.path.splitext(filename.lower())[1]
    return next((cat for cat, exts in EXTENSIONS.items() if ext in exts), 'others')

def is_file_complete(file_path):
    """Verifica si el archivo ha terminado de descargarse."""
    try:
        # Si el archivo tiene extensión temporal, no está completo
        if any(file_path.lower().endswith(ext.lower()) for ext in TEMP_EXTENSIONS):
            return False
            
        if not os.path.exists(file_path):
            return False

        # Verifica si el archivo está siendo usado
        try:
            with open(file_path, 'rb') as f:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(f.fileno(), 1, 1)
                    msvcrt.locking(f.fileno(), 0, 1)
                return True
        except (IOError, PermissionError):
            return False
            
        return True
    except Exception as e:
        logging.error(f"Error al verificar archivo: {e}")
        return False

def setup_folder_icon(folder_path: str, category: str) -> bool:
    """Configura el ícono de una carpeta."""
    if not CONFIG['enable_icons']:
        return False

    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "icons", f"{category}.ico")
    ini_path = os.path.join(folder_path, "desktop.ini")

    if not os.path.exists(icon_path):
        return False

    try:
        os.system(f'attrib +s "{folder_path}"')
        with open(ini_path, 'w') as f:
            f.write(f"[.ShellClassInfo]\nIconFile={icon_path}\nIconIndex=0\nConfirmFileOp=0\n")
        os.system(f'attrib +s +h "{ini_path}"')
        return True
    except Exception:
        return False

def move_item(src: str, dest_folder: str) -> bool:
    """Mueve un archivo o carpeta manejando duplicados."""
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    name = os.path.basename(src)
    dest_path = os.path.join(dest_folder, name)

    if os.path.exists(dest_path):
        base, ext = os.path.splitext(name)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_folder, f"{base}_{counter}{ext}")
            counter += 1

    try:
        shutil.move(src, dest_path)
        message = f"\n✅ Movido: {name} -> {os.path.basename(dest_folder)}\n"
        print_colored(message, 'success')
        logging.info(message)
        return True
    except Exception as e:
        message = f"❌ Error al mover {name}: {e}"
        print_colored(message, 'error')
        logging.error(message)
        return False

def organize_downloads():
    """Organiza los archivos en la carpeta de descargas."""
    downloads = find_downloads_folder()
    message = f"📂 Organizando: {downloads}..."
    logging.info(message)
    
    success = 0
    failed = 0

    # Crear carpetas si no existen
    for category in EXTENSIONS:
        category_path = os.path.join(downloads, category)
        os.makedirs(category_path, exist_ok=True)
        setup_folder_icon(category_path, category)

    for item in os.listdir(downloads):
        item_path = os.path.join(downloads, item)

        # Ignorar archivos temporales y carpetas de categorías
        if item in EXTENSIONS or any(item.lower().endswith(ext.lower()) for ext in TEMP_EXTENSIONS):
            continue

        if os.path.isfile(item_path) and is_file_complete(item_path):
            category = get_category(item)
            dest = os.path.join(downloads, category)
        elif os.path.isdir(item_path) and CONFIG['move_folders']:
            dest = os.path.join(downloads, 'others')
        else:
            continue

        if move_item(item_path, dest):
            success += 1
        else:
            failed += 1

    return success, failed

class DownloadEventHandler(FileSystemEventHandler):
    def __init__(self):
        self.processing_files = {}
        
    def clean_processing_files(self):
        """Limpia los archivos que ya no existen de processing_files"""
        for file_path in list(self.processing_files.keys()):
            if not os.path.exists(file_path):
                del self.processing_files[file_path]
                message = f"✅ Proceso completado: {file_path}"
                print_colored(message, 'success')
                logging.info(message)

    def handle_file_event(self, file_path):
        """Maneja los eventos de archivo."""
        # Primero limpiamos archivos que ya no existen
        self.clean_processing_files()
        
        # Si el archivo no existe, no hacemos nada
        if not os.path.exists(file_path):
            if file_path in self.processing_files:
                del self.processing_files[file_path]
            return
            
        if file_path not in processed_files:
            base_path = file_path
            # Si es un archivo temporal, obtén el nombre base
            for ext in TEMP_EXTENSIONS:
                if file_path.endswith(ext):
                    base_path = file_path[:-len(ext)]
                    break
                    
            if is_file_complete(file_path):
                if file_path not in processed_files:
                    processed_files.append(file_path)
                    if file_path in self.processing_files:
                        del self.processing_files[file_path]
                    message = f"📂 Archivo completado: {file_path}"
                    print_colored(message, 'info')
                    logging.info(message)
                    organize_downloads()
            else:
                if file_path not in self.processing_files:
                    self.processing_files[file_path] = time.time()
                    message = f"⏳ Archivo descargándose: {file_path}"
                    print_colored(message, 'warning')
                    logging.info(message)

    def on_created(self, event):
        if not event.is_directory:
            self.handle_file_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_file_event(event.src_path)

    def on_deleted(self, event):
        """Maneja cuando se elimina un archivo."""
        if not event.is_directory:
            if event.src_path in self.processing_files:
                del self.processing_files[event.src_path]

def monitor_downloads():
    """Monitorea la carpeta de descargas y organiza los archivos."""
    downloads_folder = find_downloads_folder()
    event_handler = DownloadEventHandler()
    observer = Observer()
    observer.schedule(event_handler, downloads_folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
            # Verifica archivos que llevan mucho tiempo procesando
            current_time = time.time()
            for file_path, start_time in list(event_handler.processing_files.items()):
                if current_time - start_time > 30:  # 30 segundos de timeout
                    if is_file_complete(file_path):
                        event_handler.handle_file_event(file_path)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    def signal_handler(sig, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
try:
    message = "🚀 Iniciando organización automática..."
    print_colored(message, 'info')
    success, failed = organize_downloads()
    message = f"🎉 Completado: {success} elementos organizados"
    print_colored(message, 'success')
    if failed > 0:
        message = f"⚠️ {failed} errores"
        print_colored(message, 'error')
    message = "👀 Monitoreando cambios...\n"
    print_colored(message, 'info')
    monitor_downloads()
except Exception as e:
    message = f"❌ Error: {e}"
    print_colored(message, 'error')
    sys.exit(1)