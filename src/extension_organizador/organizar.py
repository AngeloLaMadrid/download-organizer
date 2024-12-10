# Script que cree y comparto para organizar los archivos de la carpeta de descargas de Windows con buen diseño, estilo y orden.
from pathlib import Path
import shutil
import winreg
import os

# Variables de configuración
enable_icons_check = True       # Variable para habilitar la verificación de íconos (Buen diseño)
move_folders_to_others = True  # Sirve para mover carpetas no reconocidas a la carpeta 'others' (Le da un mejor orden al no tener carpetas sueltas)

# Definición de colores usando códigos ANSI
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

extensiones = {
    'videos': ['.avi', '.flv', '.m4v', '.mkv', '.mov', '.mp4', '.wmv', '.webm', '.3gp'],
    'documents': ['.csv', '.doc', '.docx', '.odt', '.pdf', '.ppt', '.pptx', '.txt', '.xlsx'],
    'music': ['.aac', '.flac', '.m4a', '.midi', '.mp3', '.ogg', '.wav', '.wma'],
    'programs': ['.app', '.bat', '.cmd', '.dll', '.exe', '.jar', '.msi', '.py'],
    'compressed': ['.7z', '.bz2', '.gz', '.iso', '.rar', '.tar', '.xz', '.zip'],
    'images': ['.bmp', '.gif', '.ico', '.jpeg', '.jpg', '.png', '.svg', '.tiff', '.webp'],
    'others': []
}

def find_downloads_folder():
    """Encuentra la carpeta de descargas actual del usuario usando el registro de Windows"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                          r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            downloads_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            
        if Path(downloads_path).exists():
            return downloads_path
    except Exception:
        user_profile = Path(os.environ['USERPROFILE'])
        possible_download_names = ['Downloads', 'Descargas', 'Download']
        
        for name in possible_download_names:
            path = user_profile / name
            if path.exists():
                return path
    
    return user_profile / 'Downloads'

def get_file_category(filename):
    """Determina la categoría de un archivo"""
    ext = Path(filename).suffix.lower()
    return next((cat for cat, exts in extensiones.items() if ext in exts), 'others')

def move_file(file_path, destination_folder):
    """Mueve un archivo manejando duplicados"""
    destination_folder.mkdir(parents=True, exist_ok=True)
    dest_path = destination_folder / file_path.name
    
    if dest_path.exists():
        base, ext = file_path.stem, file_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = destination_folder / f"{base}_{counter}{ext}"
            counter += 1
    
    try:
        shutil.move(str(file_path), str(dest_path))
        print(f"{Colors.GREEN}✅ Archivo movido: {file_path.name} -> {destination_folder}{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Error al mover {file_path.name}: {e}{Colors.RESET}")
        return False

def check_folder_icons(downloads_folder):
    """Verifica y aplica íconos a cada carpeta"""
    show_icons_messages = True
    script_dir = Path(__file__).parent
    icons_folder = script_dir / "icons"
    carpetas_con_iconos = 0
    carpetas_procesadas = []

    if not icons_folder.exists():
        if show_icons_messages:
            print(f"{Colors.YELLOW}⚠️ Carpeta de íconos no encontrada: {icons_folder}{Colors.RESET}")
        return

    for category in extensiones:
        folder_path = downloads_folder / category
        icon_file = icons_folder / f"{category}.ico"
        ini_path = folder_path / "desktop.ini"
        
        if not icon_file.exists():
            if show_icons_messages:
                print(f"{Colors.RED}⚠️ Falta el ícono para la carpeta '{category}': {icon_file}{Colors.RESET}")
            continue
            
        if ini_path.exists():
            try:
                with ini_path.open('r') as f:
                    content = f.read()
                    if str(icon_file) in content:
                        carpetas_con_iconos += 1
                        carpetas_procesadas.append(category)
                        continue
            except Exception:
                pass
            
        try:
            os.system(f'attrib +s "{folder_path}"')
            
            with ini_path.open('w') as f:
                f.write("[.ShellClassInfo]\n")
                f.write(f"IconFile={icon_file}\n")
                f.write("IconIndex=0\n")
                f.write("ConfirmFileOp=0\n")
            
            os.system(f'attrib +s +h "{ini_path}"')
            carpetas_con_iconos += 1
            carpetas_procesadas.append(category)
            
        except PermissionError as e:
            if show_icons_messages:
                print(f"{Colors.RED}❌ Error al aplicar el ícono a '{category}': {str(e)}{Colors.RESET}")
            # Mover archivos fuera de la carpeta con problemas
            temp_folder = downloads_folder / "temp"
            temp_folder.mkdir(exist_ok=True)
            for file in folder_path.iterdir():
                shutil.move(str(file), str(temp_folder / file.name))
            
            # Eliminar y recrear la carpeta
            shutil.rmtree(folder_path)
            folder_path.mkdir(exist_ok=True)
            
            # Aplicar el ícono nuevamente
            try:
                os.system(f'attrib +s "{folder_path}"')
                
                with ini_path.open('w') as f:
                    f.write("[.ShellClassInfo]\n")
                    f.write(f"IconFile={icon_file}\n")
                    f.write("IconIndex=0\n")
                    f.write("ConfirmFileOp=0\n")
                
                os.system(f'attrib +s +h "{ini_path}"')
                carpetas_con_iconos += 1
                carpetas_procesadas.append(category)
                
                # Mover archivos de vuelta a la carpeta
                for file in temp_folder.iterdir():
                    shutil.move(str(file), str(folder_path / file.name))
                
                shutil.rmtree(temp_folder)
                
            except Exception as e:
                if show_icons_messages:
                    print(f"{Colors.RED}❌ Error al aplicar el ícono a '{category}': {str(e)}{Colors.RESET}")

    # Mostrar resumen final
    if carpetas_con_iconos > 0:
        print(f"{Colors.YELLOW}   ↪ 🗂️  Carpetas con sus iconos correspondientes: {', '.join(carpetas_procesadas)}{Colors.RESET} \n")
    else:
        print(f"{Colors.YELLOW}   ↪ ⚠️  No se encontraron carpetas con íconos aplicados{Colors.RESET}")

def organize_downloads():
    downloads_folder = Path(find_downloads_folder())
    print(f"{Colors.CYAN}📂 Usando carpeta de descargas: {downloads_folder}{Colors.RESET}")
    processed = failed = 0
    
    for category in extensiones:
        (downloads_folder / category).mkdir(exist_ok=True)
    
    if enable_icons_check:
        check_folder_icons(downloads_folder)
    
    for item in downloads_folder.iterdir():
        if item.is_file():
            category = get_file_category(item.name)
            if move_file(item, downloads_folder / category):
                processed += 1
            else:
                failed += 1
        elif item.is_dir() and move_folders_to_others:
            if item.name not in extensiones.keys() and item.name != 'others':
                others_path = downloads_folder / 'others'
                try:
                    others_path.mkdir(exist_ok=True)
                    shutil.move(str(item), str(others_path / item.name))
                    processed += 1
                    print(f"{Colors.GREEN}✅ Carpeta '{item.name}' movida a 'others'{Colors.RESET}")
                except Exception as e:
                    failed += 1
                    print(f"{Colors.RED}❌ Error al mover la carpeta '{item.name}': {str(e)}{Colors.RESET}")
    
    return processed, failed

if __name__ == "__main__":
    try:
        print(f"{Colors.YELLOW}🚀 Iniciando organización de archivos...{Colors.RESET}")
        processed, failed = organize_downloads()
        print(f"{Colors.GREEN}🎉 Proceso completado: {processed} archivos organizados{Colors.RESET}")
        if failed > 0:
            print(f"{Colors.RED}⚠️ {failed} errores{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")