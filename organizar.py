import os
import shutil
import winreg
from colorama import init, Fore, Style

# Inicializar colorama
init(autoreset=True)

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
        # Abrir la clave del registro que contiene la ubicación de descargas
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                          r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            downloads_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            
        if os.path.exists(downloads_path):
            return downloads_path
    except Exception:
        # Si hay algún error con el registro, intentar el método de respaldo
        user_profile = os.environ['USERPROFILE']
        possible_download_names = ['Downloads', 'Descargas', 'Download']
        
        for name in possible_download_names:
            path = os.path.join(user_profile, name)
            if os.path.exists(path):
                return path
    
    # Si todo lo demás falla, devolver la ruta predeterminada
    return os.path.join(os.environ['USERPROFILE'], 'Downloads')

def get_file_category(filename):
    """Determina la categoría de un archivo"""
    ext = os.path.splitext(filename.lower())[1]
    return next((cat for cat, exts in extensiones.items() if ext in exts), 'others')

def move_file(file_path, destination_folder):
    """Mueve un archivo manejando duplicados"""
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    filename = os.path.basename(file_path)
    dest_path = os.path.join(destination_folder, filename)
    
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(destination_folder, f"{base}_{counter}{ext}")
            counter += 1
    
    try:
        shutil.move(file_path, dest_path)
        print(f"{Fore.GREEN}✅ Archivo movido: {filename} -> {destination_folder}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Error al mover {filename}: {e}")
        return False

def organize_downloads():
    """Organiza los archivos de la carpeta de descargas"""
    downloads_folder = find_downloads_folder()
    print(f"{Fore.CYAN}📂 Usando carpeta de descargas: {downloads_folder}")
    processed = failed = 0
    
    for category in extensiones:
        os.makedirs(os.path.join(downloads_folder, category), exist_ok=True)
    
    for filename in os.listdir(downloads_folder):
        file_path = os.path.join(downloads_folder, filename)
        if os.path.isfile(file_path):
            category = get_file_category(filename)
            if move_file(file_path, os.path.join(downloads_folder, category)):
                processed += 1
            else:
                failed += 1
    
    return processed, failed

if __name__ == "__main__":
    try:
        print(f"{Fore.YELLOW}🚀 Iniciando organización de archivos...")
        processed, failed = organize_downloads()
        print(f"{Fore.GREEN}🎉 Proceso completado: {processed} archivos organizados")
        if failed > 0:
            print(f"{Fore.RED}⚠️ {failed} errores")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}")