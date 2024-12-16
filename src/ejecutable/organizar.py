import os
import shutil
import sys
import winreg
from typing import Tuple, Dict, List

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
    ext = os.path.splitext(filename.lower())[1]
    return next((cat for cat, exts in EXTENSIONS.items() if ext in exts), 'others')

def setup_folder_icons() -> str:
    downloads = find_downloads_folder()
    icons_path = os.path.join(downloads, 'images', 'folder_icons')
    if not os.path.exists(icons_path):
        os.makedirs(icons_path)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_icons = os.path.join(script_dir, "icons")
    for category in EXTENSIONS:
        icon_name = f"{category}.ico"
        src_icon = os.path.join(original_icons, icon_name)
        dst_icon = os.path.join(icons_path, icon_name)
        if os.path.exists(src_icon) and not os.path.exists(dst_icon):
            shutil.copy2(src_icon, dst_icon)
            print_colored(f"✅ Icono copiado: {icon_name}", 'success')
    return icons_path

def validate_icons() -> bool:
    downloads = find_downloads_folder()
    icons_path = os.path.join(downloads, 'images', 'folder_icons')
    if not os.path.exists(icons_path):
        print_colored("📁 Creando carpeta de iconos...", 'info')
        return setup_folder_icons() is not None
    missing_icons = [category for category in EXTENSIONS if not os.path.exists(os.path.join(icons_path, f"{category}.ico"))]
    if missing_icons:
        print_colored(f"⚠️ Faltan los siguientes iconos: {', '.join(missing_icons)}", 'warning')
        script_dir = os.path.dirname(os.path.abspath(__file__))
        original_icons = os.path.join(script_dir, "icons")
        for category in missing_icons:
            icon_name = f"{category}.ico"
            src_icon = os.path.join(original_icons, icon_name)
            dst_icon = os.path.join(icons_path, icon_name)
            if os.path.exists(src_icon):
                shutil.copy2(src_icon, dst_icon)
                print_colored(f"✅ Icono regenerado: {icon_name}", 'success')
            else:
                print_colored(f"❌ No se encontró el icono original: {icon_name}", 'error')
                return False
    return True

def setup_folder_icon(folder_path: str, category: str) -> bool:
    if not CONFIG['enable_icons']:
        return False
    try:
        downloads = find_downloads_folder()
        icons_path = os.path.join(downloads, 'images', 'folder_icons')
        icon_path = os.path.join(icons_path, f"{category}.ico")
        ini_path = os.path.join(folder_path, "desktop.ini")
        if not validate_icons():
            return False
        os.system(f'attrib +s "{folder_path}"')
        with open(ini_path, 'w') as f:
            f.write(f"[.ShellClassInfo]\nIconFile={icon_path}\nIconIndex=0\nConfirmFileOp=0\n")
        os.system(f'attrib +s +h "{ini_path}"')
        return True
    except Exception as e:
        if isinstance(e, PermissionError) and os.path.exists(ini_path):
            return True
        return False

def move_item(src, dest) -> bool:
    src_norm = os.path.normcase(os.path.abspath(src))
    py_path = os.path.normcase(os.path.abspath(__file__))
    exe_path = os.path.normcase(sys.executable) if getattr(sys, 'frozen', False) else None
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

def main():
    try:
        print_colored("🚀 Iniciando organización...", 'info')
        if CONFIG['enable_icons'] and not validate_icons():
            print_colored("⚠️ Error validando iconos, continuando sin iconos", 'warning')
            CONFIG['enable_icons'] = False
        success, failed = organize_downloads()
        if success > 0 or failed > 0:
            if success > 0:
                print_colored(f"🎉 Completado: {success} elementos organizados", 'success')
            if failed > 0:
                print_colored(f"⚠️ {failed} elementos no pudieron ser organizados", 'warning')
            total = success + failed
            porcentaje = (success / total) * 100
            print_colored(f"📊 Efectividad: {porcentaje:.1f}%", 'info')
        else:
            print_colored("ℹ️ No se encontraron elementos para organizar", 'info')
    except Exception as e:
        if isinstance(e, PermissionError):
            print_colored("❌ Error: No hay permisos suficientes para acceder a algunas carpetas", 'error')
        elif isinstance(e, FileNotFoundError):
            print_colored("❌ Error: No se encontró la carpeta de descargas", 'error')
        else:
            print_colored(f"❌ Error inesperado: {str(e)}", 'error')
    finally:
        print_colored("\n👋 Programa finalizado", 'info')

if __name__ == "__main__":
    main()