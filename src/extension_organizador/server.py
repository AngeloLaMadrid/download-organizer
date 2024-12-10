from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import shutil
import winreg
from typing import Tuple, Dict, List
import logging
import signal
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import deque

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Registro de archivos procesados recientemente
processed_files = deque(maxlen=10)

def print_colored(message: str, color: str) -> None:
    print(f"{COLORS.get(color, '')}{message}{COLORS['reset']}")

def find_downloads_folder() -> str:
    """Encuentra la carpeta de descargas del usuario"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            downloads_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            if os.path.exists(downloads_path):
                return downloads_path
    except Exception:
        pass
    
    user_profile = os.environ.get('USERPROFILE', '')
    for folder in ['Downloads', 'Descargas']:
        path = os.path.join(user_profile, folder)
        if os.path.exists(path):
            return path
    return os.path.join(user_profile, 'Downloads')

def get_category(filename: str) -> str:
    """Determina la categoría de un archivo por su extensión"""
    ext = os.path.splitext(filename.lower())[1]
    return next((cat for cat, exts in EXTENSIONS.items() if ext in exts), 'others')

def setup_folder_icon(folder_path: str, category: str) -> bool:
    """Configura el ícono de una carpeta"""
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
    """Mueve un archivo o carpeta manejando duplicados"""
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
        print_colored(f"✅ Movido: {name} -> {os.path.basename(dest_folder)}", 'success')
        return True
    except Exception as e:
        print_colored(f"❌ Error al mover {name}: {e}", 'error')
        return False

def organize_downloads() -> Tuple[int, int]:
    """Organiza los archivos de la carpeta de descargas"""
    downloads = find_downloads_folder()
    print_colored(f"📂 Organizando: {downloads}", 'info')
    
    success = failed = 0

    for category in EXTENSIONS:
        category_path = os.path.join(downloads, category)
        os.makedirs(category_path, exist_ok=True)
        setup_folder_icon(category_path, category)

    for item in os.listdir(downloads):
        item_path = os.path.join(downloads, item)
        
        if item in EXTENSIONS:
            continue

        if os.path.isfile(item_path):
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

class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()
        logging.info(f"{COLORS['info']}🌐 OPTIONS request received{COLORS['reset']}")

    def do_POST(self):
        self._set_headers()
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        file_path = data['file_path']
        downloads_folder = find_downloads_folder()
        category = get_category(file_path)
        destination_folder = os.path.join(downloads_folder, category)
        
        if file_path in processed_files:
            logging.info(f"{COLORS['info']}📁 File already processed: {file_path}{COLORS['reset']}")
            response = {'message': 'File already processed'}
            self.wfile.write(json.dumps(response).encode())
            return

        dest_path = move_item(file_path, destination_folder)
        if dest_path:
            processed_files.append(file_path)
            response = {'message': 'File moved successfully', 'destination': dest_path}
            self.wfile.write(json.dumps(response).encode())
            logging.info(f"{COLORS['success']}📁 File moved successfully: {file_path} -> {dest_path}{COLORS['reset']}")
        else:
            self.send_response(500)
            self.end_headers()
            response = {'message': 'Failed to move file'}
            self.wfile.write(json.dumps(response).encode())
            logging.error(f"{COLORS['error']}❌ Failed to move file: {file_path}{COLORS['reset']}")

def run(server_class=ThreadingHTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info(f"{COLORS['info']}🚀 Starting server on port {port}{COLORS['reset']}")
    httpd.serve_forever()

class DownloadEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path not in processed_files:
            processed_files.append(event.src_path)
            logging.info(f"{COLORS['info']}📂 Archivo añadido: {event.src_path}{COLORS['reset']}")
            print_colored(f"📂 Archivo añadido: {event.src_path}", 'info')
            organize_downloads()

    def on_deleted(self, event):
        if not event.is_directory and event.src_path not in processed_files:
            processed_files.append(event.src_path)
            logging.info(f"{COLORS['warning']}🗑️ Archivo eliminado: {event.src_path}{COLORS['reset']}")
            print_colored(f"🗑️ Archivo eliminado: {event.src_path}", 'warning')

def monitor_downloads():
    """Monitorea la carpeta de descargas y organiza los archivos cuando se detectan cambios"""
    downloads_folder = find_downloads_folder()
    logging.info(f"{COLORS['info']}🔍 Monitoreando la carpeta de descargas: {downloads_folder}{COLORS['reset']}")
    event_handler = DownloadEventHandler()
    observer = Observer()
    observer.schedule(event_handler, downloads_folder, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def signal_handler(sig, frame):
    logging.info(f"{COLORS['warning']}🛑 Señal de interrupción recibida, deteniendo el servidor...{COLORS['reset']}")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    from threading import Thread
    server_thread = Thread(target=run)
    monitor_thread = Thread(target=monitor_downloads)
    
    server_thread.start()
    monitor_thread.start()
    
    server_thread.join()
    monitor_thread.join()