# Es un organizar.py adaptado para que funciones como un servidor web que recibe solicitudes POST para mover archivos a carpetas específicas
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import shutil
import winreg

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
            
        if os.path.exists(downloads_path):
            return downloads_path
    except Exception:
        user_profile = os.environ['USERPROFILE']
        possible_download_names = ['Downloads', 'Descargas', 'Download']
        
        for name in possible_download_names:
            path = os.path.join(user_profile, name)
            if os.path.exists(path):
                return path
    
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
        print(f"{Colors.GREEN}✅ Archivo movido: {filename} -> {destination_folder}{Colors.RESET}")
        return dest_path  # Devuelve la ruta de destino
    except Exception as e:
        print(f"{Colors.RED}❌ Error al mover {filename}: {e}{Colors.RESET}")
        return None

def check_folder_icons(downloads_folder):
    """Verifica y aplica íconos a cada carpeta"""
    show_icons_messages = True
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_folder = os.path.join(script_dir, "icons")
    carpetas_con_iconos = 0
    carpetas_procesadas = []

    if not os.path.exists(icons_folder):
        if show_icons_messages:
            print(f"{Colors.YELLOW}⚠️ Carpeta de íconos no encontrada: {icons_folder}{Colors.RESET}")
        return

    for category in extensiones:
        folder_path = os.path.join(downloads_folder, category)
        icon_file = os.path.join(icons_folder, f"{category}.ico")
        ini_path = os.path.join(folder_path, "desktop.ini")
        
        if not os.path.exists(icon_file):
            if show_icons_messages:
                print(f"{Colors.RED}   ⚠️ Falta el ícono para la carpeta '{category}': {icon_file}{Colors.RESET}")
            continue
            
        if os.path.exists(ini_path):
            try:
                with open(ini_path, 'r') as f:
                    content = f.read()
                    if icon_file in content:
                        carpetas_con_iconos += 1
                        carpetas_procesadas.append(category)
                        continue
            except Exception:
                pass
            
        try:
            # Eliminar el atributo de solo lectura si está presente
            os.system(f'attrib -r "{ini_path}"')
            os.system(f'attrib +s "{folder_path}"')
            
            with open(ini_path, 'w') as f:
                f.write("[.ShellClassInfo]\n")
                f.write(f"IconFile={icon_file}\n")
                f.write("IconIndex=0\n")
                f.write("ConfirmFileOp=0\n")
            
            os.system(f'attrib +s +h "{ini_path}"')
            carpetas_con_iconos += 1
            carpetas_procesadas.append(category)
            
        except Exception as e:
            if show_icons_messages:
                print(f"{Colors.RED}   ❌ Error al aplicar el ícono a '{category}': {str(e)}{Colors.RESET}")

    # Mostrar resumen final
    if carpetas_con_iconos > 0:
        print(f"{Colors.YELLOW}  ↪🗂️  Carpetas con sus iconos correspondientes: {', '.join(carpetas_procesadas)}{Colors.RESET} \n")
    else:
        print(f"{Colors.YELLOW}↪⚠️ No se encontraron carpetas con íconos aplicados{Colors.RESET}")
    """Verifica y aplica íconos a cada carpeta"""
    show_icons_messages = True
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_folder = os.path.join(script_dir, "icons")
    carpetas_con_iconos = 0
    carpetas_procesadas = []

    if not os.path.exists(icons_folder):
        if show_icons_messages:
            print(f"{Colors.YELLOW}⚠️ Carpeta de íconos no encontrada: {icons_folder}{Colors.RESET}")
        return

    for category in extensiones:
        folder_path = os.path.join(downloads_folder, category)
        icon_file = os.path.join(icons_folder, f"{category}.ico")
        ini_path = os.path.join(folder_path, "desktop.ini")
        
        if not os.path.exists(icon_file):
            if show_icons_messages:
                print(f"{Colors.RED}   ⚠️ Falta el ícono para la carpeta '{category}': {icon_file}{Colors.RESET}")
            continue
            
        if os.path.exists(ini_path):
            try:
                with open(ini_path, 'r') as f:
                    content = f.read()
                    if icon_file in content:
                        carpetas_con_iconos += 1
                        carpetas_procesadas.append(category)
                        continue
            except Exception:
                pass
            
        try:
            # Eliminar el atributo de solo lectura si está presente
            os.system(f'attrib -r "{ini_path}"')
            os.system(f'attrib +s "{folder_path}"')
            
            with open(ini_path, 'w') as f:
                f.write("[.ShellClassInfo]\n")
                f.write(f"IconFile={icon_file}\n")
                f.write("IconIndex=0\n")
                f.write("ConfirmFileOp=0\n")
            
            os.system(f'attrib +s +h "{ini_path}"')
            carpetas_con_iconos += 1
            carpetas_procesadas.append(category)
            
        except Exception as e:
            if show_icons_messages:
                print(f"{Colors.RED}   ❌ Error al aplicar el ícono a '{category}': {str(e)}{Colors.RESET}")

    # Mostrar resumen final
    if carpetas_con_iconos > 0:
        print(f"{Colors.YELLOW}  ↪🗂️  Carpetas con sus iconos correspondientes: {', '.join(carpetas_procesadas)}{Colors.RESET} \n")
    else:
        print(f"{Colors.YELLOW}↪⚠️ No se encontraron carpetas con íconos aplicados{Colors.RESET}")

def organize_downloads():
    downloads_folder = find_downloads_folder()
    print(f"{Colors.CYAN}📂 Usando carpeta de descargas: {downloads_folder}{Colors.RESET}")
    processed = failed = 0
    
    for category in extensiones:
        os.makedirs(os.path.join(downloads_folder, category), exist_ok=True)
    
    if enable_icons_check:
        check_folder_icons(downloads_folder)
    
    for filename in os.listdir(downloads_folder):
        file_path = os.path.join(downloads_folder, filename)
        if os.path.isfile(file_path):
            category = get_file_category(filename)
            if move_file(file_path, os.path.join(downloads_folder, category)):
                processed += 1
            else:
                failed += 1
        elif os.path.isdir(file_path) and move_folders_to_others:
            if filename not in extensiones.keys() and filename != 'others':
                others_path = os.path.join(downloads_folder, 'others')
                try:
                    os.makedirs(others_path, exist_ok=True)
                    shutil.move(file_path, os.path.join(others_path, filename))
                    processed += 1
                    print(f"{Colors.GREEN}✅ Carpeta '{filename}' movida a 'others'{Colors.RESET}")
                except Exception as e:
                    failed += 1
                    print(f"{Colors.RED}❌ Error al mover la carpeta '{filename}': {str(e)}{Colors.RESET}")
    
    return processed, failed

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

    def do_POST(self):
        self._set_headers()
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        file_path = data['file_path']
        downloads_folder = find_downloads_folder()
        category = get_file_category(file_path)
        destination_folder = os.path.join(downloads_folder, category)
        
        dest_path = move_file(file_path, destination_folder)
        if dest_path:
            response = {'message': 'File moved successfully', 'destination': dest_path}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(500)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}')
    httpd.serve_forever()

if __name__ == "__main__":
    try:
        print(f"{Colors.YELLOW}🚀 Iniciando organización de archivos...{Colors.RESET}")
        processed, failed = organize_downloads()
        print(f"{Colors.GREEN}🎉 Proceso completado: {processed} archivos organizados{Colors.RESET}")
        if failed > 0:
            print(f"{Colors.RED}⚠️ {failed} errores{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")
    
    run()