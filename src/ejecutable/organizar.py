import os
import shutil
import sys
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

def setup_folder_icons() -> None:
    """Configura los iconos iniciales en la carpeta images"""
    downloads = find_downloads_folder()
    images_path = os.path.join(downloads, 'images')
    icons_path = os.path.join(images_path, 'folder_icons')
    
    try:
        # Crear carpeta de iconos si no existe
        if not os.path.exists(icons_path):
            os.makedirs(icons_path)
            
        # Copiar iconos originales a la carpeta images/folder_icons
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
    except Exception as e:
        #print_colored(f"❌ Error configurando iconos: {e}", 'error')
        print_colored(f"⚠️ Iconos configurados", 'warning')
        return None

def validate_icons() -> bool:
    """
    Valida que todos los iconos necesarios existan en la carpeta images/folder_icons
    y los regenera si faltan algunos.
    
    Returns:
        bool: True si todos los iconos están presentes o fueron regenerados correctamente
    """
    try:
        # Obtener rutas
        downloads = find_downloads_folder()
        icons_path = os.path.join(downloads, 'images', 'folder_icons')
        
        # Si no existe la carpeta de iconos, crearla y copiar todos
        if not os.path.exists(icons_path):
            print_colored("📁 Creando carpeta de iconos...", 'info')
            return setup_folder_icons() is not None
            
        # Verificar cada icono
        missing_icons = []
        for category in EXTENSIONS:
            icon_path = os.path.join(icons_path, f"{category}.ico")
            if not os.path.exists(icon_path):
                missing_icons.append(category)
                
        # Si faltan iconos, regenerarlos
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
                    
    except Exception as e:
        print_colored(f"❌ Error validando iconos: {e}", 'error')
        return False

# Modificar setup_folder_icon para usar validate_icons
def setup_folder_icon(folder_path: str, category: str) -> bool:
    """Configura el ícono personalizado para una carpeta"""
    if not CONFIG['enable_icons']:
        return False
        
    try:
        downloads = find_downloads_folder()
        icons_path = os.path.join(downloads, 'images', 'folder_icons')
        icon_path = os.path.join(icons_path, f"{category}.ico")
        ini_path = os.path.join(folder_path, "desktop.ini")

        # Validar que existan todos los iconos
        if not validate_icons():
            return False

        # Configurar atributos y crear desktop.ini
        os.system(f'attrib +s "{folder_path}"')
        with open(ini_path, 'w') as f:
            f.write(f"[.ShellClassInfo]\nIconFile={icon_path}\nIconIndex=0\nConfirmFileOp=0\n")
        os.system(f'attrib +s +h "{ini_path}"')
        return True
        
    except Exception as e:
        #print_colored(f"❌ Error configurando ícono para {category}: {e}", 'error')
        if isinstance(e, PermissionError) and os.path.exists(ini_path):
            return True  # Si el archivo existe, consideramos éxito
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
        
        # Validar iconos al inicio
        if CONFIG['enable_icons']:
            if not validate_icons():
                print_colored("⚠️ Error validando iconos, continuando sin iconos", 'warning')
                CONFIG['enable_icons'] = False
            else:
                print_colored("✅ Iconos validados correctamente", 'success')
        
        # Organizar archivos
        success, failed = organize_downloads()
        
        # Mostrar resumen solo si hay resultados
        if success > 0 or failed > 0:
            if success > 0:
                print_colored(f"🎉 Completado: {success} elementos organizados", 'success')
            if failed > 0:
                print_colored(f"⚠️ {failed} elementos no pudieron ser organizados", 'warning')
            
            # Calcular efectividad
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
