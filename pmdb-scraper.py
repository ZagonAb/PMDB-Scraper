import logging
import json
from pathlib import Path
import re
import requests
import shutil
import time
from themoviedb import TMDb
from datetime import datetime
from tqdm import tqdm
from rapidfuzz import fuzz
import yt_dlp
import os
import subprocess
import sys
import concurrent.futures
import queue
import contextlib
import io

# Configurar el logging
log_file = Path(__file__).parent / "console.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        #logging.StreamHandler()  # Comenta o elimina esta línea para evitar que se muestre en la terminal
    ]
)

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TRANSLATIONS = {
    "es-ES": {
        "progress": "Progreso",
        "progress_file": "archivo",
        "no_metadata": "No hay metadata disponible.",
        "movies_available": "Películas disponibles:",
        "file": "Archivo",
        "unknown": "Desconocido",
        "select_movie": "Selecciona el número de la película que deseas actualizar (o 0 para cancelar): ",
        "updating_metadata_for": "Actualizando metadatos para",
        "results_for": "Resultados para",
        "not_available": "No disponible",
        "minutes": "minutos",
        "processing_files": "Procesando {} archivos...",
        "operation_summary": "=== Resumen de la operación ===",
        "file_generated": "Archivo generado:",
        "total_files_processed": "Total de archivos procesados:",
        "movies_found": "Películas encontradas:",
        "movies_not_found": "Películas no encontradas:",
        "images_downloaded": "Imágenes descargadas:",
        "posters": "- Posters (boxfront):",
        "screenshots": "- Capturas (screenshot):",
        "logos": "- Logos (wheel):",
        "trailers": "- Tráilers descargados:",
        "select_correct_movie": "Selecciona el número de la película correcta (o 0 para cancelar):",
        "trailer_downloaded": "Trailer descargado exitosamente para:",
        "trailer_no_downloaded": "Trailer no descargado para:",
        "metadata_updated": "Metadatos actualizados para:",
        "metadata_fields": {
            "title": "título",
            "original_title": "título original",
            "year": "año",
            "duration": "duración",
            "director": "director",
            "production": "productora",
            "rating": "rating",
            "description": "descripción",
            "genres": "géneros",
            "release_date": "fecha de lanzamiento",
            "metadata_language": "idioma de metadata",
            "poster": "poster",
            "tmdb_id": "ID de TMDb"
        }
    },
    "en-US": {
        "progress": "Progress",
        "progress_file": "file",
        "no_metadata": "No metadata available.",
        "movies_available": "Available movies:",
        "file": "File",
        "unknown": "Unknown",
        "select_movie": "Select the movie number to update (or 0 to cancel): ",
        "updating_metadata_for": "Updating metadata for",
        "results_for": "Results for",
        "not_available": "Not available",
        "minutes": "minutes",
        "processing_files": "Processing {} files...",
        "operation_summary": "=== Operation Summary ===",
        "file_generated": "Generated file:",
        "total_files_processed": "Total files processed:",
        "movies_found": "Movies found:",
        "movies_not_found": "Movies not found:",
        "images_downloaded": "Downloaded images:",
        "posters": "- Posters (boxfront):",
        "screenshots": "- Screenshots:",
        "logos": "- Logos (wheel):",
        "trailers": "- Downloaded trailers:",
        "select_correct_movie": "Select the correct movie number (or 0 to cancel):",
        "trailer_downloaded": "Trailer successfully downloaded for:",
        "trailer_no_downloaded": "Trailer not downloaded for:",
        "metadata_updated": "Metadata updated for:",
        "metadata_fields": {
            "title": "title",
            "original_title": "original title",
            "year": "year",
            "duration": "duration",
            "director": "director",
            "production": "production",
            "rating": "rating",
            "description": "description",
            "genres": "genres",
            "release_date": "release date",
            "metadata_language": "metadata language",
            "poster": "poster",
            "tmdb_id": "TMDb ID"
        }
    }
}

def get_translation(key, interface_language):
    """Obtiene la traducción correspondiente según el idioma de la interfaz, con soporte para claves anidadas."""
    translation = TRANSLATIONS.get(interface_language, TRANSLATIONS["es-ES"])

    # Dividir la clave en partes (ejemplo: "metadata_fields.title")
    keys = key.split(".")
    for k in keys:
        translation = translation.get(k, None)
        if translation is None:
            return key  # Si no se encuentra la clave, devolver la clave original

    return translation

def load_config():
    """Carga la configuración permitiendo barras simples en rutas de Windows"""
    config_path = Path('config.json')

    if not config_path.exists():
        logging.error("Error: El archivo config.json no existe")
        raise FileNotFoundError("config.json no encontrado")

    try:
        # 1. Leer el archivo como texto
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 2. Preprocesamiento especial para Windows
        if os.name == 'nt':  # Solo en Windows
            # Encontrar el valor de ruta_peliculas
            match = re.search(r'"ruta_peliculas"\s*:\s*"([^"]+)"', content)
            if match:
                original_path = match.group(1)
                # Escapar las barras invertidas
                corrected_path = original_path.replace('\\', '\\\\')
                # Reemplazar en el contenido
                content = content.replace(
                    f'"ruta_peliculas": "{original_path}"',
                    f'"ruta_peliculas": "{corrected_path}"'
                )

        # 3. Parsear el JSON
        config = json.loads(content)

        # 4. Normalizar la ruta para el sistema operativo
        if 'ruta_peliculas' in config:
            config['ruta_peliculas'] = str(Path(config['ruta_peliculas']))

        # 5. Normalizar códigos de idioma (es-Es -> es-ES)
        lang_fields = ['metadata_language', 'interface_language']
        for field in lang_fields:
            if field in config and isinstance(config[field], str):
                parts = config[field].split('-')
                if len(parts) == 2:
                    config[field] = f"{parts[0].lower()}-{parts[1].upper()}"

        return config

    except json.JSONDecodeError as e:
        logging.error(f"Error en config.json (línea {e.lineno}): {e.msg}")
        raise
    except Exception as e:
        logging.error(f"Error al cargar configuración: {str(e)}")
        raise
def normalizar_ruta_para_sistema(ruta, es_asset=False):
    """
    Normaliza una ruta para el sistema operativo actual.
    - es_asset: True si es una ruta de imagen/video (debe ser relativa a la carpeta media)
    """
    if not ruta:
        return ''

    path_obj = Path(ruta)

    # Determinar el separador de ruta según el SO
    separador = '\\' if os.name == 'nt' else '/'

    # Para activos (imágenes/videos), la ruta debe ser relativa a la carpeta media
    if es_asset:
        # Extraer solo el nombre del archivo y la subcarpeta de media
        return f".{separador}media{separador}{path_obj.parent.name}{separador}{path_obj.name}"

    # Para el archivo principal, usar solo el nombre del archivo
    return f".{separador}{path_obj.name}"

def descargar_imagen(url, ruta_destino):
    """Descarga una imagen desde una URL con timeout y reintentos."""
    for intento in range(config['max_reintentos']):
        try:
            response = requests.get(url, stream=True, timeout=config['timeout_descargas'])
            if response.status_code == 200:
                # Extraer la extensión del archivo de la URL
                extension = Path(url).suffix.lower()  # Ejemplo: .jpg, .png
                ruta_destino_con_extension = f"{ruta_destino}{extension}"

                with open(ruta_destino_con_extension, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                return True
        except requests.exceptions.RequestException as e:
            logging.warning(f"Intento {intento + 1} fallido para {url}: {e}")
            time.sleep((2 ** intento) * 1)  # Espera exponencial
    logging.error(f"Error al descargar imagen: {url}")
    return False

def crear_carpetas_imagenes(ruta_base):
    media_path = Path(ruta_base) / 'media'
    media_path.mkdir(parents=True, exist_ok=True)

    carpetas = {
        'boxFront': media_path / 'boxFront',
        'screenshot': media_path / 'screenshot',
        'wheel': media_path / 'wheel',
        'video': media_path / 'video'
    }
    for carpeta in carpetas.values():
        carpeta.mkdir(parents=True, exist_ok=True)
    return carpetas

def validar_api_key(api_key, config):
    try:
        tmdb = TMDb(key=api_key, language=config['idiomas'][0])
        tmdb.movies().top_rated()
        return True
    except Exception as e:
        logging.error(f"Error validando API key: {e}")
        return False

def archivo_tiene_imagenes(archivo, carpetas_imagenes):
    nombre_base = archivo.stem
    imagenes_existentes = {
        'boxfront': None,
        'screenshot': None,
        'wheel': None,
        'video': None  # Nueva clave para tráilers
    }

    # Buscar archivos existentes con cualquier extensión
    for tipo, carpeta in carpetas_imagenes.items():
        for archivo_imagen in carpeta.glob(f"{nombre_base}.*"):
            imagenes_existentes[tipo.lower()] = str(archivo_imagen)
            break

    return imagenes_existentes

def obtener_archivos_video(ruta):
    """Obtiene una lista de archivos de video en la ruta especificada, excluyendo metadata.json y la carpeta media/video."""
    extensiones_video = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.ts')
    archivos = []
    try:
        for archivo in Path(ruta).glob('**/*'):
            # Excluir archivos dentro de la carpeta media/video
            if "media/video" in str(archivo):
                continue
            if archivo.is_file() and archivo.suffix.lower() in extensiones_video and archivo.name != "metadata.json":
                archivos.append(archivo)
    except Exception as e:
        logging.error(f"Error al acceder a la ruta: {e}")
    return archivos

def extraer_nombre_pelicula(nombre_archivo):
    """Extrae el nombre de la película del nombre del archivo con manejo especial para números."""
    nombre = Path(nombre_archivo).stem

    # Conservar números que son parte del título (como "3096 Dias")
    # Paso 1: Reemplazar caracteres especiales, pero preservar los adyacentes a números
    nombre = re.sub(r'(?<!\d)[\-_.()\[\]](?!\d)', ' ', nombre)

    # Paso 2: Eliminar términos técnicos pero solo si no están unidos a números
    patrones_tecnicos = r'(?<!\d)(720p|1080p|2160p|BluRay|x264|WEB-DL|HEVC|XviD|HDR|DTS)(?!\d)'
    nombre = re.sub(patrones_tecnicos, '', nombre, flags=re.IGNORECASE)

    # Paso 3: Eliminar años entre paréntesis (pero solo si están al final)
    nombre = re.sub(r'\s*\(\d{4}\)$', '', nombre)

    return nombre.strip()

def descargar_trailer(tmdb, pelicula_id, ruta_destino, calidad):
    try:
        # Redirigir la salida estándar y de errores a /dev/null
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

        # Guardar el idioma original de la instancia TMDb
        idioma_original = tmdb.language

        # Intentar descargar el tráiler en cada idioma configurado
        for idioma in config['trailer_lenguaje']:
            try:
                # Cambiar el idioma de la instancia TMDb
                tmdb.language = idioma
                videos = tmdb.movie(pelicula_id).videos()

                if videos:
                    # Filtrar tráilers
                    trailers = [video for video in videos if video.type == "Trailer"]
                    if trailers:
                        logging.info(f"Se encontraron {len(trailers)} tráilers para la película ID {pelicula_id} en idioma {idioma}")
                        # Obtener la URL del tráiler
                        for trailer in trailers:
                            if trailer.site == "YouTube":
                                trailer_url = f"https://www.youtube.com/watch?v={trailer.key}"
                                logging.info(f"Intentando descargar tráiler desde YouTube: {trailer_url}")

                                # Mapeo de calidades a formatos de yt-dlp
                                calidad_mapping = {
                                    "240p": "bestvideo[height<=240]+bestaudio/best[height<=240]",
                                    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
                                    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                                    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                                    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
                                }

                                # Obtener el formato correcto según la calidad configurada
                                formato = calidad_mapping.get(calidad.lower(), "bestvideo[height<=240]+bestaudio/best[height<=240]")

                                try:
                                    # Configurar yt-dlp con manejo silencioso de errores
                                    ydl_opts = {
                                        'format': formato,
                                        'outtmpl': f"{ruta_destino}.%(ext)s",
                                        'quiet': True,  # Suprime la salida de yt-dlp
                                        'no_warnings': True,  # Suprime las advertencias
                                        'merge_output_format': 'mp4',
                                        'geo_bypass': True,  # Intenta evitar restricciones geográficas
                                        'ignoreerrors': True,  # Ignora errores y continúa con el siguiente video
                                        'no_check_certificate': True,  # Evita problemas con certificados SSL
                                    }

                                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                        ydl.download([trailer_url])
                                        if Path(f"{ruta_destino}.mp4").exists():
                                            logging.info(f"Tráiler descargado exitosamente: {ruta_destino}.mp4")
                                            return True
                                except Exception as e:
                                    logging.error(f"Error al descargar tráiler: {e}")
                                    continue

            except Exception as e:
                logging.error(f"Error en el idioma {idioma}: {e}")
                continue  # Silenciosamente continúa con el siguiente idioma

        # Restaurar el idioma original de la instancia TMDb
        tmdb.language = idioma_original
        return False

    except Exception as e:
        logging.error(f"Error general en descargar_trailer: {e}")
        return False
    finally:
        # Restaurar la salida estándar y de errores
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

def obtener_duracion_con_ffprobe(ruta_archivo):
    """
    Obtiene la duración de un archivo de video usando ffprobe.
    Devuelve la duración en segundos.
    """
    try:
        # Comando para obtener la duración en segundos
        comando = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', ruta_archivo
        ]
        resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if resultado.returncode == 0:
            duracion_segundos = float(resultado.stdout.strip())
            return int(duracion_segundos)  # Devolver la duración en segundos como entero
        else:
            logging.warning(f"No se pudo obtener la duración con ffprobe para {ruta_archivo}: {resultado.stderr}")
            return None
    except Exception as e:
        logging.error(f"Error al ejecutar ffprobe para {ruta_archivo}: {e}")
        return None

def obtener_info_tecnica(ruta_archivo):
    """Obtiene información técnica del video usando ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height,display_aspect_ratio',
            '-of', 'default=noprint_wrappers=1:nokey=1', ruta_archivo
        ]
        video_info = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip().split('\n')

        cmd_audio = [
            'ffprobe', '-v', 'error', '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name,channels',
            '-of', 'default=noprint_wrappers=1:nokey=1', ruta_archivo
        ]
        audio_info = subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip().split('\n')

        if len(video_info) >= 3 and len(audio_info) >= 2:
            codec = video_info[0].upper()
            width = int(video_info[1])
            height = int(video_info[2])
            aspect_ratio = video_info[3] if len(video_info) > 3 else "1.85:1"
            audio_codec = audio_info[0].upper()
            channels = int(audio_info[1])

            # Determinar resolución
            if width >= 1920 or height >= 1080:
                resolution = "1080 HD"
            elif width >= 1280 or height >= 720:
                resolution = "720 HD"
            else:
                resolution = "SD"

            # Determinar audio
            if channels >= 6:
                audio = "DOLBY 5.1"
            elif channels >= 2:
                audio = "Stereo"
            else:
                audio = "Mono"

            return {
                "x-codec": codec,
                "x-resolution": resolution,
                "x-aspect": aspect_ratio,
                "x-audio": audio
            }
    except Exception as e:
        logging.error(f"Error al obtener información técnica para {ruta_archivo}: {e}")

    return {
        "x-codec": "Unknown",
        "x-resolution": "Unknown",
        "x-aspect": "Unknown",
        "x-audio": "Unknown"
    }

def obtener_clasificacion_mpa(tmdb, pelicula_id):
    """Obtiene SOLO la clasificación MPA (EE.UU.) en formato de letras (G, PG, R, etc.)."""
    try:
        detalles = tmdb.movie(pelicula_id).details(append_to_response="release_dates")
        if hasattr(detalles, 'release_dates') and detalles.release_dates:
            for release in detalles.release_dates.results:
                if release.iso_3166_1 == "US":  # Priorizar EE.UU. (MPA)
                    for date in release.release_dates:
                        if date.certification:
                            return date.certification  # Ejemplo: "PG-13", "R"
        return "NR"  # "No Rated" si no se encuentra
    except Exception as e:
        logging.error(f"Error al obtener clasificación MPA: {e}")
        return "NR"

def obtener_metadata_pelicula(tmdb, nombre_pelicula, carpetas_imagenes, archivo_video, config, imagenes_existentes=None):
    for intento in range(config['max_reintentos']):
        try:
            # Verificar si el archivo es un tráiler (está dentro de la carpeta media/video)
            if "media/video" in str(archivo_video):
                logging.info(f"El archivo {archivo_video.name} es un tráiler. Saltando...")
                return None

            info_tecnica = obtener_info_tecnica(archivo_video)

            # Usar las imágenes existentes si están disponibles
            boxfront_local = imagenes_existentes.get('boxfront') if imagenes_existentes else None
            screenshot_local = imagenes_existentes.get('screenshot') if imagenes_existentes else None
            wheel_local = imagenes_existentes.get('wheel') if imagenes_existentes else None
            video_local = imagenes_existentes.get('video') if imagenes_existentes else None

            # Extraer el año del nombre del archivo si existe
            año_archivo = None
            año_match = re.search(r'\((\d{4})\)', archivo_video.name)
            if año_match:
                año_archivo = año_match.group(1)
                nombre_sin_año = re.sub(r'\s*\(\d{4}\)', '', nombre_pelicula).strip()
            else:
                nombre_sin_año = nombre_pelicula

            # Lista para almacenar resultados de búsqueda en todos los idiomas
            todos_resultados = []

            # Buscar en cada idioma configurado
            for idioma in config['idiomas']:
                tmdb.language = idioma
                resultados = tmdb.search().movies(nombre_sin_año)
                if resultados:
                    todos_resultados.extend(resultados)

            if not todos_resultados:
                logging.warning(f"No se encontró información para la película: {nombre_pelicula} (Archivo: {archivo_video.name})")
                return None

            # Función para calcular la similitud entre el título del archivo y el título de la película
            def calcular_similitud(titulo_archivo, titulo_pelicula):
                # Calcula la similitud entre dos títulos usando RapidFuzz
                return fuzz.ratio(titulo_archivo.lower(), titulo_pelicula.lower()) / 100

            # Seleccionar candidatos que pasen los filtros iniciales
            candidatos_validos = []

            for resultado in todos_resultados:
                # Verificar duración - requiere consulta adicional para obtener información detallada
                tmdb.language = config['metadata_language'][0]  # Usar primer idioma para verificación
                pelicula_detalle = tmdb.movie(resultado.id).details()

                # Filtrar películas cortas (menor a 60 minutos)
                if hasattr(pelicula_detalle, 'runtime') and pelicula_detalle.runtime and pelicula_detalle.runtime < 60:
                    logging.warning(f"Descartando película {resultado.title} (ID: {resultado.id}) por duración insuficiente: {pelicula_detalle.runtime} minutos")
                    continue

                # Obtener el año de la película
                año_resultado = None
                if hasattr(resultado, 'release_date') and resultado.release_date:
                    año_resultado = str(resultado.release_date.year)

                # Si la película pasa el filtro de duración, la agregamos como candidata
                candidato = {
                    'resultado': resultado,
                    'año': año_resultado,
                    'duracion': pelicula_detalle.runtime if hasattr(pelicula_detalle, 'runtime') else None
                }
                candidatos_validos.append(candidato)

            if not candidatos_validos:
                logging.warning(f"No se encontraron candidatos válidos después del filtro de duración para: {nombre_pelicula} (Archivo: {archivo_video.name})")
                return None

            # Seleccionar el resultado más adecuado entre los candidatos válidos
            mejor_resultado = None
            mejor_puntaje = 0

            for candidato in candidatos_validos:
                resultado = candidato['resultado']
                año_resultado = candidato['año']

                # Calcular similitud del título
                puntaje = calcular_similitud(nombre_sin_año, resultado.title)

                # Priorizar resultados que coincidan en el año
                if año_archivo and año_resultado and año_archivo == año_resultado:
                    puntaje += 0.5

                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_resultado = resultado

            if not mejor_resultado:
                logging.warning(f"No se encontró un resultado adecuado para: {nombre_pelicula} (Archivo: {archivo_video.name})")
                return None

            # Variables para almacenar los mejores metadatos
            metadata_final = None
            mejor_tagline = None
            mejor_descripcion = None

            # Obtener detalles de la película en varios idiomas según las prioridades
            for idioma_metadata in config['metadata_language']:
                tmdb.language = idioma_metadata
                pelicula_id = mejor_resultado.id
                pelicula = tmdb.movie(pelicula_id).details(append_to_response="credits,images,videos")
                imagenes = tmdb.movie(pelicula_id).images()

                # Verificar si tenemos descripción y tagline en este idioma
                descripcion_actual = pelicula.overview if hasattr(pelicula, 'overview') else ""
                tagline_actual = pelicula.tagline if hasattr(pelicula, 'tagline') else ""

                # Actualizar la mejor descripción si la actual no está vacía
                if descripcion_actual and not mejor_descripcion:
                    mejor_descripcion = descripcion_actual

                # Actualizar el mejor tagline si el actual no está vacío
                if tagline_actual and not mejor_tagline:
                    mejor_tagline = tagline_actual

                # Si tenemos tanto descripción como tagline, no seguimos buscando
                if mejor_descripcion and mejor_tagline:
                    break

            # Si después de recorrer todos los idiomas no hay descripción, usamos cualquier idioma disponible
            if not mejor_descripcion:
                tmdb.language = config['metadata_language'][0]
                pelicula = tmdb.movie(pelicula_id).details(append_to_response="credits,images,videos")
                mejor_descripcion = pelicula.overview if hasattr(pelicula, 'overview') else "Sin descripción disponible"

            # Usar el primer idioma para obtener el resto de metadatos
            tmdb.language = config['metadata_language'][0]
            pelicula = tmdb.movie(pelicula_id).details(append_to_response="credits,images,videos")
            imagenes = tmdb.movie(pelicula_id).images()

            # Descargar imágenes si están configuradas
            nombre_base = archivo_video.stem

            if not boxfront_local and config['obtener_datos']['poster'] and pelicula.poster_path:
                poster_url = f"https://image.tmdb.org/t/p/original{pelicula.poster_path}"
                poster_path = carpetas_imagenes['boxFront'] / nombre_base
                if descargar_imagen(poster_url, poster_path):
                    boxfront_local = str(poster_path) + Path(poster_url).suffix
                    logging.info(f"Poster descargado exitosamente para: {nombre_pelicula} (Archivo: {archivo_video.name})")
                else:
                    logging.warning(f"No se pudo descargar el poster para la película: {nombre_pelicula} (Archivo: {archivo_video.name})")

            if not screenshot_local and config['obtener_datos']['backdrop'] and pelicula.backdrop_path:
                backdrop_url = f"https://image.tmdb.org/t/p/original{pelicula.backdrop_path}"
                backdrop_path = carpetas_imagenes['screenshot'] / nombre_base
                if descargar_imagen(backdrop_url, backdrop_path):
                    screenshot_local = str(backdrop_path) + Path(backdrop_url).suffix
                else:
                    logging.warning(f"No se pudo descargar el backdrop para la película: {nombre_pelicula} (Archivo: {archivo_video.name})")

            if not wheel_local and config['obtener_datos']['logo'] and hasattr(imagenes, 'logos') and imagenes.logos:
                # Reorganizar la lógica de selección de logos basada en metadata_language
                logos_ordenados = []
                metadata_lang = config['metadata_language'][0].split('-')[0]  # Obtener 'es' de 'es-MX'

                # Primero buscar logos en el idioma configurado
                logos_primary = [logo for logo in imagenes.logos if logo.iso_639_1 == metadata_lang]
                if logos_primary:
                    logos_ordenados.extend(logos_primary)

                # Si el idioma configurado no es inglés y no se encontraron logos,
                # buscar logos en inglés como respaldo
                if not logos_ordenados and metadata_lang != 'en':
                    logos_en = [logo for logo in imagenes.logos if logo.iso_639_1 == 'en']
                    logos_ordenados.extend(logos_en)

                # Si aún no hay logos, usar logos sin idioma especificado
                if not logos_ordenados:
                    logos_null = [logo for logo in imagenes.logos if logo.iso_639_1 is None]
                    logos_ordenados.extend(logos_null)

                # Si todavía no hay logos, usar el primer logo disponible
                if not logos_ordenados and imagenes.logos:
                    logos_ordenados = [imagenes.logos[0]]

                # Intentar descargar el primer logo de la lista ordenada
                if logos_ordenados:
                    logo_url = f"https://image.tmdb.org/t/p/original{logos_ordenados[0].file_path}"
                    logo_path = carpetas_imagenes['wheel'] / nombre_base
                    if descargar_imagen(logo_url, logo_path):
                        wheel_local = str(logo_path) + Path(logo_url).suffix
                    else:
                        logging.warning(f"No se pudo descargar el logo para la película: {nombre_pelicula} (Archivo: {archivo_video.name})")
                else:
                    logging.warning(f"No se encontró logo para la película: {nombre_pelicula} (Archivo: {archivo_video.name})")

            # Descargar tráiler si está configurado
            if not video_local and config['obtener_datos']['trailer']:
                video_path = carpetas_imagenes['video'] / nombre_base
                if descargar_trailer(tmdb, pelicula_id, video_path, config['calidad_trailer']):
                    video_local = str(video_path) + ".mp4"
                else:
                    logging.warning(f"No se pudo descargar el tráiler para la película: {nombre_pelicula} (Archivo: {archivo_video.name})")

            # Crear el diccionario de metadatos
            duracion_tmdb = pelicula.runtime if pelicula.runtime else None

            # Si no hay duración en TMDb, obtenerla localmente con ffprobe
            if not duracion_tmdb:
                duracion_tmdb = obtener_duracion_con_ffprobe(archivo_video)

            # Versión actual (obtiene clasificación según idioma configurado)
            # Nueva versión (siempre prioriza EE.UU.)
            clasificacion = obtener_clasificacion_mpa(tmdb, pelicula_id)  # "PG-13", "R", etc.

            metadata_final = {
                'titulo': archivo_video.stem,  # Usar el nombre del archivo como título
                'titulo_tmdb': pelicula.title,  # Guardar el título de TMDb en un campo separado
                'titulo_original': pelicula.original_title if hasattr(pelicula, 'original_title') else None,
                'año': str(pelicula.release_date.year) if pelicula.release_date else None,
                'duracion': duracion_tmdb,  # Usar la duración de TMDb o ffprobe
                'director': next((crew.name for crew in pelicula.credits.crew if crew.job == "Director"), "Desconocido"),
                'productora': [company.name for company in pelicula.production_companies] if pelicula.production_companies else [],
                'rating': round(pelicula.vote_average / 10, 2) if pelicula.vote_average else 0,
                'descripcion': mejor_descripcion,  # Usar la mejor descripción encontrada
                'generos': [genero.name for genero in pelicula.genres],
                'boxfront_local': boxfront_local,
                'screenshot_local': screenshot_local,
                'wheel_local': wheel_local,
                'video_local': video_local,  # Nueva clave para el tráiler
                'tmdb_id': pelicula_id,
                'fecha_lanzamiento': str(pelicula.release_date) if pelicula.release_date else None,
                'idioma_metadata': ", ".join(config['metadata_language']),  # Lista de idiomas usados
                'x-added-date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Fecha de adición
                'x-Duration': duracion_tmdb,  # Duración en segundos
                'x-tagline': mejor_tagline,  # Usar el mejor tagline encontrado
                'x-classification': clasificacion if clasificacion else "Desconocido",
                'x-codec': info_tecnica['x-codec'],
                'x-resolution': info_tecnica['x-resolution'],
                'x-aspect': info_tecnica['x-aspect'],
                'x-audio': info_tecnica['x-audio']
            }

            return metadata_final

        except Exception as e:
            logging.error(f"Error al procesar {nombre_pelicula} (Intento {intento + 1}): {e}")
            time.sleep((2 ** intento) * 1)  # Espera exponencial entre reintentos

    logging.error(f"Error al procesar {nombre_pelicula} después de {config['max_reintentos']} intentos.")
    return None

def obtener_metadata_serie(tmdb, nombre_serie, carpetas_imagenes, ruta_carpeta):
    """Obtiene la metadata de una serie y descarga las imágenes."""
    try:
        resultados = tmdb.search().tv(nombre_serie)
        if not resultados:
            return None

        serie_id = resultados[0].id
        serie = tmdb.tv(serie_id).details(append_to_response="credits,images")
        imagenes = tmdb.tv(serie_id).images()

        nombre_seguro = re.sub(r'[^\w\-_\. ]', '_', nombre_serie)
        boxfront_local = screenshot_local = wheel_local = None

        if config['obtener_datos']['poster'] and serie.poster_path:
            poster_url = f"https://image.tmdb.org/t/p/original{serie.poster_path}"
            poster_path = carpetas_imagenes['boxFront'] / f"{nombre_seguro}.{config['formato_imagenes']}"
            if descargar_imagen(poster_url, poster_path):
                boxfront_local = str(poster_path)

        if config['obtener_datos']['backdrop'] and serie.backdrop_path:
            backdrop_url = f"https://image.tmdb.org/t/p/original{serie.backdrop_path}"
            backdrop_path = carpetas_imagenes['screenshot'] / f"{nombre_seguro}.{config['formato_imagenes']}"
            if descargar_imagen(backdrop_url, backdrop_path):
                screenshot_local = str(backdrop_path)

        if config['obtener_datos']['logo'] and hasattr(imagenes, 'logos') and imagenes.logos:
            logo_url = f"https://image.tmdb.org/t/p/original{imagenes.logos[0].file_path}"
            logo_path = carpetas_imagenes['wheel'] / f"{nombre_seguro}.{config['formato_imagenes']}"
            if descargar_imagen(logo_url, logo_path):
                wheel_local = str(logo_path)

        return {
            'titulo': serie.name,
            'año': str(serie.first_air_date.year) if serie.first_air_date else "Desconocido",
            'duracion': serie.episode_run_time[0] if serie.episode_run_time else None,
            'creador': next((crew.name for crew in serie.created_by), "Desconocido"),
            'productora': [company.name for company in serie.production_companies] if serie.production_companies else [],
            'rating': round(serie.vote_average / 10, 2) if serie.vote_average else 0,
            'descripcion': serie.overview,
            'generos': [genero.name for genero in serie.genres],
            'boxfront_local': boxfront_local,
            'screenshot_local': screenshot_local,
            'wheel_local': wheel_local,
            'tmdb_id': serie_id,
            'fecha_lanzamiento': str(serie.first_air_date) if serie.first_air_date else None
        }
    except Exception as e:
        logging.error(f"Error al procesar {nombre_serie}: {e}")
        return None

def cargar_metadata_existente(ruta_metadata):
    """Carga el archivo de metadata existente si existe."""
    if ruta_metadata.exists():
        with open(ruta_metadata, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def actualizar_metadata(nuevos_datos, ruta_metadata):
    """Actualiza el archivo de metadata con nuevos datos."""
    if ruta_metadata.exists():
        with open(ruta_metadata, 'r', encoding='utf-8') as f:
            metadata_existente = json.load(f)
    else:
        metadata_existente = {
            "metadata": [],
            "errores": [],
            "timestamp": datetime.now().isoformat(),
            "estadisticas": {
                "total_procesadas": 0,
                "encontradas": 0,
                "no_encontradas": 0,
                "imagenes_descargadas": {
                    "boxfront": 0,
                    "screenshot": 0,
                    "wheel": 0
                },
                "trailers_descargados": 0  # Nueva estadística para tráilers
            }
        }

    # Actualizar o agregar nuevos elementos
    for nuevo_item in nuevos_datos["metadata"]:
        archivo_original = nuevo_item.get("archivo_original")
        encontrado = False

        for item in metadata_existente["metadata"]:
            if item.get("archivo_original") == archivo_original:
                item.update({
                    "tipo": "pelicula",
                    "archivo_original": archivo_original,
                    "nombre_extraido": nuevo_item["nombre_extraido"],
                    "metadata": nuevo_item["metadata"]
                })
                encontrado = True
                break

        if not encontrado:
            metadata_existente["metadata"].append({
                "tipo": "pelicula",
                "archivo_original": archivo_original,
                "nombre_extraido": nuevo_item["nombre_extraido"],
                "metadata": nuevo_item["metadata"]
            })

    # Actualizar estadísticas
    metadata_existente["estadisticas"]["total_procesadas"] += nuevos_datos["estadisticas"]["total_procesadas"]
    metadata_existente["estadisticas"]["encontradas"] += nuevos_datos["estadisticas"]["encontradas"]
    metadata_existente["estadisticas"]["no_encontradas"] += nuevos_datos["estadisticas"]["no_encontradas"]
    metadata_existente["estadisticas"]["imagenes_descargadas"]["boxfront"] += nuevos_datos["estadisticas"]["imagenes_descargadas"]["boxfront"]
    metadata_existente["estadisticas"]["imagenes_descargadas"]["screenshot"] += nuevos_datos["estadisticas"]["imagenes_descargadas"]["screenshot"]
    metadata_existente["estadisticas"]["imagenes_descargadas"]["wheel"] += nuevos_datos["estadisticas"]["imagenes_descargadas"]["wheel"]
    metadata_existente["estadisticas"]["trailers_descargados"] += nuevos_datos["estadisticas"].get("trailers_descargados", 0)

    # Guardar la metadata actualizada en JSON
    with open(ruta_metadata, 'w', encoding='utf-8') as f:
        json.dump(metadata_existente, f, ensure_ascii=False, indent=2)

    # Generar el archivo TXT
    ruta_txt = ruta_metadata.with_suffix('.txt')
    convert_json_to_txt(metadata_existente, ruta_txt)

def archivo_tiene_metadata(archivo, metadata_existente):
    """Verifica si un archivo ya tiene metadata en el archivo .json."""
    if metadata_existente and "metadata" in metadata_existente:
        for item in metadata_existente["metadata"]:
            if item.get("archivo_original") == str(archivo):
                return True
    return False

def listar_peliculas(metadata_existente):
    """Lista las películas disponibles en metadata.json en orden alfabético."""
    if not metadata_existente or "metadata" not in metadata_existente:
        logging.error(get_translation("no_metadata", config['interface_language']))
        return None

    # Ordenar las películas alfabéticamente por el campo "nombre_extraido"
    peliculas_ordenadas = sorted(metadata_existente["metadata"], key=lambda x: x.get('nombre_extraido', '').lower())

    print(f"\n{get_translation('movies_available', config['interface_language'])}")
    for i, item in enumerate(peliculas_ordenadas):
        print(f"{i + 1}. {item.get('nombre_extraido', get_translation('unknown', config['interface_language']))} "
              f"({get_translation('file', config['interface_language'])}: "
              f"{item.get('archivo_original', get_translation('unknown', config['interface_language']))})")

    seleccion = input(f"\n{get_translation('select_movie', config['interface_language'])}")
    if seleccion.isdigit() and 0 < int(seleccion) <= len(peliculas_ordenadas):
        return peliculas_ordenadas[int(seleccion) - 1]
    return None

def actualizar_pelicula_manual(tmdb, pelicula, carpetas_imagenes, ruta_metadata):
    nombre_pelicula = pelicula.get("nombre_extraido", "Desconocido")
    archivo_video = Path(pelicula.get("archivo_original", ""))

    info_tecnica = obtener_info_tecnica(archivo_video)

    print(f"\n{get_translation('updating_metadata_for', config['interface_language'])}: {nombre_pelicula}")

    # Buscar en TMDb usando el idioma de metadata
    tmdb.language = config['metadata_language']
    resultados = tmdb.search().movies(nombre_pelicula)

    if not resultados:
        # Si no hay resultados en el idioma principal, intentar con los idiomas alternativos
        for idioma in config['idiomas']:
            if idioma != config['metadata_language']:
                tmdb.language = idioma
                resultados_alt = tmdb.search().movies(nombre_pelicula)
                if resultados_alt:
                    resultados.extend(resultados_alt)

    if not resultados:
        logging.warning(f"No se encontraron resultados para: {nombre_pelicula}")
        return

    # Mostrar resultados al usuario con información detallada
    print(f"\n{get_translation('results_for', config['interface_language'])} '{nombre_pelicula}':")
    print("\n" + "="*100)  # Línea separadora

    # Asegurarse de usar el idioma de metadata para mostrar los detalles
    tmdb.language = config['metadata_language']

    for i, resultado in enumerate(resultados):
        try:
            # Obtener detalles completos de la película en el idioma de metadata
            detalles = tmdb.movie(resultado.id).details()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.warning(f"Película con ID {resultado.id} no encontrada en TMDb. Saltando...")
                continue  # Saltar a la siguiente película
            else:
                raise  # Relanzar la excepción si no es un error 404

        # Manejar la fecha de lanzamiento
        año = "Desconocido"
        if hasattr(detalles, 'release_date') and detalles.release_date:
            if isinstance(detalles.release_date, str):
                try:
                    fecha = datetime.strptime(detalles.release_date, "%Y-%m-%d").date()
                    año = str(fecha.year)
                except ValueError:
                    año = "Desconocido"
            else:
                año = str(detalles.release_date.year)

        # Obtener el poster URL
        poster_url = None
        if hasattr(detalles, 'poster_path') and detalles.poster_path:
            poster_url = f"https://image.tmdb.org/t/p/original{detalles.poster_path}"

        # Mostrar información detallada
        print(f"\n{i + 1}. {get_translation('metadata_fields.title', config['interface_language'])}: {detalles.title}")
        print(f"   {get_translation('metadata_fields.year', config['interface_language'])}: {año}")
        if hasattr(detalles, 'original_title') and detalles.original_title != detalles.title:
            print(f"   {get_translation('metadata_fields.original_title', config['interface_language'])}: {detalles.original_title}")
        print(f"   {get_translation('metadata_fields.duration', config['interface_language'])}: {detalles.runtime} {get_translation('minutes', config['interface_language'])}" if detalles.runtime else f"   {get_translation('metadata_fields.duration', config['interface_language'])}: {get_translation('unknown', config['interface_language'])}")
        if hasattr(detalles, 'overview') and detalles.overview:
            descripcion = detalles.overview[:300] + "..." if len(detalles.overview) > 300 else detalles.overview
            print(f"   {get_translation('metadata_fields.description', config['interface_language'])}: {descripcion}")
        if poster_url:
            print(f"   Poster: {poster_url}")
        print(f"   ID TMDb: {detalles.id}")
        if hasattr(detalles, 'genres') and detalles.genres:
            generos = ", ".join([genero.name for genero in detalles.genres])
            print(f"   {get_translation('metadata_fields.genres', config['interface_language'])}: {generos}")

        print("\n" + "="*100)

    seleccion = input(f"\n{get_translation('select_correct_movie', config['interface_language'])}")
    if not seleccion.isdigit() or int(seleccion) < 1 or int(seleccion) > len(resultados):
        logging.info("Actualización cancelada.")
        return

    try:
        pelicula_seleccionada = resultados[int(seleccion) - 1]
        pelicula_id = pelicula_seleccionada.id

        # Nueva versión (siempre prioriza EE.UU.)
        clasificacion = obtener_clasificacion_mpa(tmdb, pelicula_id)  # "PG-13", "R", etc.

        # Asegurarse de usar el idioma de metadata para los detalles finales
        tmdb.language = config['metadata_language']
        pelicula = tmdb.movie(pelicula_id).details(append_to_response="credits,images,videos")
        imagenes = tmdb.movie(pelicula_id).images()

        nombre_base = archivo_video.stem
        boxfront_local = screenshot_local = wheel_local = video_local = None

        # Descargar poster si está configurado
        if config['obtener_datos']['poster'] and pelicula.poster_path:
            poster_url = f"https://image.tmdb.org/t/p/original{pelicula.poster_path}"
            poster_path = carpetas_imagenes['boxFront'] / nombre_base
            if descargar_imagen(poster_url, poster_path):
                boxfront_local = str(poster_path) + Path(poster_url).suffix

        # Descargar backdrop si está configurado
        if config['obtener_datos']['backdrop'] and pelicula.backdrop_path:
            backdrop_url = f"https://image.tmdb.org/t/p/original{pelicula.backdrop_path}"
            backdrop_path = carpetas_imagenes['screenshot'] / nombre_base
            if descargar_imagen(backdrop_url, backdrop_path):
                screenshot_local = str(backdrop_path) + Path(backdrop_url).suffix

        # Descargar logo si está configurado
        if config['obtener_datos']['logo'] and hasattr(imagenes, 'logos') and imagenes.logos:
            logo_url = f"https://image.tmdb.org/t/p/original{imagenes.logos[0].file_path}"
            logo_path = carpetas_imagenes['wheel'] / nombre_base
            if descargar_imagen(logo_url, logo_path):
                wheel_local = str(logo_path) + Path(logo_url).suffix

        # Descargar trailer si está configurado
        video_local = None
        if config['obtener_datos']['trailer']:
            video_path = carpetas_imagenes['video'] / nombre_base
            # Intentar descargar el tráiler en los idiomas configurados
            if descargar_trailer(tmdb, pelicula_id, video_path, config['calidad_trailer']):
                video_local = str(video_path) + ".mp4"
                #logging.info(f"{get_translation('trailer_downloaded', config['interface_language'])} {nombre_pelicula}")

            else:
                logging.warning(f"{get_translation('trailer_no_downloaded', config['interface_language'])} {nombre_pelicula}")

        nuevos_metadatos = {
            'titulo': pelicula.title,
            'titulo_original': pelicula.original_title if hasattr(pelicula, 'original_title') else None,
            'año': str(pelicula.release_date.year) if pelicula.release_date else "Desconocido",
            'duracion': pelicula.runtime if pelicula.runtime else None,
            'director': next((crew.name for crew in pelicula.credits.crew if crew.job == "Director"), "Desconocido"),
            'productora': [company.name for company in pelicula.production_companies] if pelicula.production_companies else [],
            'rating': round(pelicula.vote_average / 10, 2) if pelicula.vote_average else 0,
            'descripcion': pelicula.overview,
            'generos': [genero.name for genero in pelicula.genres],
            'boxfront_local': boxfront_local,
            'screenshot_local': screenshot_local,
            'wheel_local': wheel_local,
            'video_local': video_local,
            'tmdb_id': pelicula_id,
            'fecha_lanzamiento': str(pelicula.release_date) if pelicula.release_date else None,
            'idioma_metadata': config['metadata_language'],
            'x-classification': clasificacion if clasificacion else "Desconocido",
            'x-added-date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'x-codec': info_tecnica['x-codec'],  # <-- Ahora info_tecnica está definida
            'x-resolution': info_tecnica['x-resolution'],
            'x-aspect': info_tecnica['x-aspect'],
            'x-audio': info_tecnica['x-audio']
        }

        metadata_existente = cargar_metadata_existente(ruta_metadata)
        for item in metadata_existente["metadata"]:
            if item.get("archivo_original") == str(archivo_video):
                item.update({
                    "tipo": "pelicula",
                    "archivo_original": str(archivo_video),
                    "nombre_extraido": nombre_pelicula,
                    "metadata": nuevos_metadatos
                })
                break

        with open(ruta_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata_existente, f, ensure_ascii=False, indent=2)

        # Generar el archivo TXT actualizado
        ruta_txt = ruta_metadata.with_suffix('.txt')
        convert_json_to_txt(metadata_existente, ruta_txt)

        # Mensaje de confirmación
        print(f"\n{get_translation('metadata_updated', config['interface_language'])}: {nombre_pelicula}")
        print(f"Metadatos actualizados correctamente para: {nombre_pelicula}")
        logging.info(f"Metadatos actualizados correctamente para: {nombre_pelicula}")

    except Exception as e:
        logging.error(f"Error al obtener metadatos para la película seleccionada: {e}")
        print(f"\nError al actualizar los metadatos para: {nombre_pelicula}")
        print(f"Detalles del error: {e}")

def convert_json_to_txt(json_data, output_file):
    """Convierte los datos JSON a formato txt con rutas correctas para cada SO."""
    try:
        # Determinar el separador de ruta según el SO
        separador = '\\' if os.name == 'nt' else '/'

        with open(output_file, 'w', encoding='utf-8') as f:
            # Escribir la cabecera
            f.write("collection: Movies\n")
            f.write("shortname: movies\n")
            f.write("extension: mp4, mkv, avi, mov, wmv, flv, mpeg, ts\n")
            f.write('launch: command... {file.path}\n\n')

            for item in json_data["metadata"]:
                try:
                    # Si metadata es None, usar información básica del archivo
                    if item.get('metadata') is None:
                        archivo_original = item.get('archivo_original', '')
                        nombre_archivo = normalizar_ruta_para_sistema(archivo_original)
                        nombre_base = os.path.splitext(Path(archivo_original).name)[0]

                        f.write(f"game: {nombre_base}\n")
                        f.write("file:\n")
                        f.write(f"  {nombre_archivo}\n")
                        f.write("developer: Unknown\n")
                        f.write("publisher: Unknown\n")
                        f.write("genre: Unknown\n")
                        f.write("description:\n")
                        f.write("  No description available\n")
                        f.write("release: Unknown\n")
                        f.write("rating: 0%\n")
                        f.write("x-tagline: \n")
                        f.write("x-lastPosition: 0\n")
                        f.write("x-codec: Unknown\n")
                        f.write("x-resolution: Unknown\n")
                        f.write("x-aspect: Unknown\n")
                        f.write("x-audio: Unknown\n")
                        f.write("x-classification: Unknown\n")
                        f.write("\n")
                    else:
                        metadata = item['metadata']
                        titulo = metadata.get('titulo', '')
                        archivo_original = item.get('archivo_original', '')
                        director = metadata.get('director', '')
                        productoras = metadata.get('productora', [])
                        productora = productoras[0] if productoras else ''
                        generos = ', '.join(metadata.get('generos', []))
                        descripcion = metadata.get('descripcion', '')
                        fecha_lanzamiento = metadata.get('fecha_lanzamiento', '')
                        rating = int(float(metadata.get('rating', 0)) * 100)
                        x_tagline = metadata.get('x-tagline', '')
                        x_clasification = metadata.get('x-classification', 'Unknown')

                        # Normalizar rutas
                        archivo_normalizado = normalizar_ruta_para_sistema(archivo_original)
                        boxfront_normalizado = normalizar_ruta_para_sistema(metadata.get('boxfront_local', ''), True)
                        screenshot_normalizado = normalizar_ruta_para_sistema(metadata.get('screenshot_local', ''), True)
                        wheel_normalizado = normalizar_ruta_para_sistema(metadata.get('wheel_local', ''), True)
                        video_normalizado = normalizar_ruta_para_sistema(metadata.get('video_local', ''), True)

                        # Obtener timestamp si existe
                        x_timestamp = ""
                        if 'x-added-date' in metadata:
                            try:
                                fecha = datetime.strptime(metadata['x-added-date'], "%Y-%m-%d %H:%M:%S")
                                x_timestamp = str(int(fecha.timestamp() * 1000))
                            except:
                                x_timestamp = ""

                        # Escribir metadatos
                        f.write(f"game: {titulo}\n")
                        f.write("file:\n")
                        f.write(f"  {archivo_normalizado}\n")
                        f.write(f"developer: {director}\n")
                        f.write(f"publisher: {productora}\n")
                        f.write(f"genre: {generos}\n")
                        f.write("description:\n")
                        f.write(f"  {descripcion}\n")
                        f.write(f"release: {fecha_lanzamiento}\n")
                        f.write(f"rating: {rating}%\n")

                        if boxfront_normalizado:
                            f.write(f"assets.boxFront: {boxfront_normalizado}\n")
                        if screenshot_normalizado:
                            f.write(f"assets.screenshot: {screenshot_normalizado}\n")
                        if wheel_normalizado:
                            f.write(f"assets.wheel: {wheel_normalizado}\n")
                        if video_normalizado:
                            f.write(f"assets.video: {video_normalizado}\n")

                        # Campos técnicos
                        f.write(f"x-codec: {metadata.get('x-codec', 'Unknown')}\n")
                        f.write(f"x-resolution: {metadata.get('x-resolution', 'Unknown')}\n")
                        f.write(f"x-aspect: {metadata.get('x-aspect', 'Unknown')}\n")
                        f.write(f"x-audio: {metadata.get('x-audio', 'Unknown')}\n")

                        # Campos adicionales
                        if x_timestamp:
                            f.write(f"x-added-timestamp: {x_timestamp}\n")
                        if metadata.get('x-Duration'):
                            f.write(f"x-Duration: {metadata.get('x-Duration')}\n")
                        f.write(f"x-tagline: {x_tagline}\n")
                        f.write(f"x-classification: {x_clasification}\n")
                        f.write("\n")

                except Exception as e:
                    logging.warning(f"Error procesando película: {e}")
                    continue

    except Exception as e:
        logging.error(f"Error en la conversión a TXT: {e}")

def main():
    # Cargar la configuración
    global config
    config = load_config()

    resultados = {
        "metadata": [],
        "errores": [],
        "timestamp": datetime.now().isoformat(),
        "estadisticas": {
            "total_procesadas": 0,
            "encontradas": 0,
            "no_encontradas": 0,
            "imagenes_descargadas": {
                "boxfront": 0,
                "screenshot": 0,
                "wheel": 0
            },
            "trailers_descargados": 0
        }
    }

    if not validar_api_key(config['api_key'], config):
        logging.error(get_translation("invalid_api_key", config['interface_language']))
        return

    archivos = obtener_archivos_video(config['ruta_peliculas'])
    if not archivos:
        logging.error(get_translation("no_video_files", config['interface_language']))
        return

    carpetas_imagenes = crear_carpetas_imagenes(config['ruta_peliculas'])
    tmdb = TMDb(key=config['api_key'], language=config['metadata_language'])

    # Cargar metadata existente si existe
    ruta_metadata = Path(config['ruta_peliculas']) / f"metadata.{config['exportar_formato']}"
    metadata_existente = cargar_metadata_existente(ruta_metadata)

    if config.get('actualizar_manual', False):
        pelicula = listar_peliculas(metadata_existente)
        if pelicula:
            actualizar_pelicula_manual(tmdb, pelicula, carpetas_imagenes, ruta_metadata)
        return
    else:
        # Modo automático
        logging.info(get_translation("processing_files", config['interface_language']).format(len(archivos)))

        # Cola para mantener el orden de los resultados
        resultados_queue = queue.Queue()

        def procesar_archivo(archivo):
            # Verificar si el archivo ya tiene metadata
            if metadata_existente and archivo_tiene_metadata(archivo, metadata_existente):
                logging.info(f"El archivo {archivo.name} ya tiene metadata. Saltando...")
                resultados["estadisticas"]["total_procesadas"] += 1  # Añadir esta línea
                return

            imagenes_existentes = archivo_tiene_imagenes(archivo, carpetas_imagenes)

            nombre_pelicula = extraer_nombre_pelicula(archivo.name)
            metadata = obtener_metadata_pelicula(tmdb, nombre_pelicula, carpetas_imagenes, archivo, config, imagenes_existentes)

            resultados["estadisticas"]["total_procesadas"] += 1  # Añadir esta línea

            if metadata:
                resultados["estadisticas"]["encontradas"] += 1
                if metadata['boxfront_local'] and metadata['boxfront_local'] not in imagenes_existentes.values():
                    resultados["estadisticas"]["imagenes_descargadas"]["boxfront"] += 1
                if metadata['screenshot_local'] and metadata['screenshot_local'] not in imagenes_existentes.values():
                    resultados["estadisticas"]["imagenes_descargadas"]["screenshot"] += 1
                if metadata['wheel_local'] and metadata['wheel_local'] not in imagenes_existentes.values():
                    resultados["estadisticas"]["imagenes_descargadas"]["wheel"] += 1
                if metadata.get('video_local') and metadata['video_local'] not in imagenes_existentes.values():
                    resultados["estadisticas"]["trailers_descargados"] += 1
            else:
                resultados["estadisticas"]["no_encontradas"] += 1
                resultados["errores"].append(f"No se encontró información para: {nombre_pelicula}")
                logging.warning(f"No se encontró información para: {nombre_pelicula} (Archivo: {archivo.name})")

            resultados_queue.put({
                "tipo": "pelicula",
                "archivo_original": str(archivo),
                "nombre_extraido": nombre_pelicula,
                "metadata": metadata
            })

        # Usar ThreadPoolExecutor para procesar archivos en paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Crear una lista de futures
            futures = [executor.submit(procesar_archivo, archivo) for archivo in archivos]

            # Usar tqdm para mostrar el progreso
            with tqdm(total=len(archivos), desc=get_translation("progress", config['interface_language']), unit=get_translation("progress_file", config['interface_language'])) as pbar:
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()  # Manejar excepciones si las hay
                    except Exception as e:
                        logging.error(f"Error al procesar archivo: {e}")
                    finally:
                        pbar.update(1)  # Actualizar la barra de progreso

        # Recoger los resultados en orden
        while not resultados_queue.empty():
            resultados["metadata"].append(resultados_queue.get())

        # Actualizar el archivo de metadata con los nuevos datos
        actualizar_metadata(resultados, ruta_metadata)

        # Mostrar resumen con los mensajes traducidos correctamente
        print(f"\n{get_translation('operation_summary', config['interface_language'])}")
        print(f"{get_translation('file_generated', config['interface_language'])} {ruta_metadata}")
        print(f"{get_translation('total_files_processed', config['interface_language'])} {resultados['estadisticas']['total_procesadas']}")
        print(f"{get_translation('movies_found', config['interface_language'])} {resultados['estadisticas']['encontradas']}")
        print(f"{get_translation('movies_not_found', config['interface_language'])} {resultados['estadisticas']['no_encontradas']}")
        print(f"\n{get_translation('images_downloaded', config['interface_language'])}")
        print(f"{get_translation('posters', config['interface_language'])} {resultados['estadisticas']['imagenes_descargadas']['boxfront']}")
        print(f"{get_translation('screenshots', config['interface_language'])} {resultados['estadisticas']['imagenes_descargadas']['screenshot']}")
        print(f"{get_translation('logos', config['interface_language'])} {resultados['estadisticas']['imagenes_descargadas']['wheel']}")
        print(f"{get_translation('trailers', config['interface_language'])} {resultados['estadisticas']['trailers_descargados']}")

        logging.info("=== Resumen de la operación ===")
        logging.info(f"Archivo generado: {ruta_metadata}")
        logging.info(f"Total de archivos procesados: {resultados['estadisticas']['total_procesadas']}")
        logging.info(f"Películas encontradas: {resultados['estadisticas']['encontradas']}")
        logging.info(f"Películas no encontradas: {resultados['estadisticas']['no_encontradas']}")
        logging.info("Imágenes descargadas:")
        logging.info(f"- Posters (boxfront): {resultados['estadisticas']['imagenes_descargadas']['boxfront']}")
        logging.info(f"- Capturas (screenshot): {resultados['estadisticas']['imagenes_descargadas']['screenshot']}")
        logging.info(f"- Logos (wheel): {resultados['estadisticas']['imagenes_descargadas']['wheel']}")
        logging.info(f"- Tráilers descargados: {resultados['estadisticas']['trailers_descargados']}")

if __name__ == "__main__":
    main()
