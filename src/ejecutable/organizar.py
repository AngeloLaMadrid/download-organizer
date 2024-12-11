import os
import shutil
import winreg
from typing import Tuple, Dict, List

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
    
    # Fallback a rutas comunes
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

def move_item(src, dest):
    """Mueve un elemento a la carpeta destino"""
    import sys

    src_norm = os.path.normcase(os.path.abspath(src))
    py_path = os.path.normcase(os.path.abspath(__file__))
    exe_path = os.path.normcase(sys.executable) if getattr(sys, 'frozen', False) else None
    
    # Verificar si el archivo a mover es el script o el exe # No mover el script/ejecutable, retornar éxito
    if src_norm == py_path or (exe_path and src_norm == exe_path):
        return True  
        
    try:
        if not os.path.exists(dest):
            os.makedirs(dest)
        
        if os.path.exists(os.path.join(dest, os.path.basename(src))):
            base, ext = os.path.splitext(os.path.basename(src))
            counter = 1
            while os.path.exists(os.path.join(dest, f"{base}_{counter}{ext}")):
                counter += 1
            shutil.move(src, os.path.join(dest, f"{base}_{counter}{ext}"))
        else:
            shutil.move(src, dest)
        return True
    except Exception as e:
        print_colored(f"❌ Error moviendo {src}: {str(e)}", 'error')
        return False

def organize_downloads() -> Tuple[int, int]:
    """Organiza los archivos de la carpeta de descargas"""
    downloads = find_downloads_folder()
    print_colored(f"📂 Organizando: {downloads}", 'info')
    
    success = failed = 0

    # Crear carpetas de categorías
    for category in EXTENSIONS:
        category_path = os.path.join(downloads, category)
        os.makedirs(category_path, exist_ok=True)
        setup_folder_icon(category_path, category)

    # Procesar archivos y carpetas
    for item in os.listdir(downloads):
        item_path = os.path.join(downloads, item)
        
        # Ignorar carpetas de categorías
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

def main():
    """Función principal"""
    try:
        print_colored("🚀 Iniciando organización...", 'info')
        success, failed = organize_downloads()
        print_colored(f"🎉 Completado: {success} elementos organizados", 'success')
        if failed > 0:
            print_colored(f"⚠️ {failed} errores", 'error')
    except Exception as e:
        print_colored(f"❌ Error: {e}", 'error')

if __name__ == "__main__":
    main()