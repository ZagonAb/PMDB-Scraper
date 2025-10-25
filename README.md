# PMDB-Scraper

## ✨ Scraper de Metadatos de Películas para Pegasus Frontend

Pegasus Movie Data Base Scraper (PMDB-Scraper) es una herramienta diseñada para extraer metadatos de películas desde **The Movie Database (TMDB)** y generar archivos de metadatos compatibles con **Pegasus Frontend**. (Esta herramienta no tiene ninguna asociación oficial con Pegasus Frontend. Es un proyecto comunitario diseñado para ayudar a quienes desean integrar su colección de películas en su sistema de juego.)

---

![screen](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen.png)
![screen1](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen1.png)
![screen2](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen2.png)

---
## ⚠️ Aviso
Esta herramienta utiliza la API de [TMDb](https://www.themoviedb.org/) (The Movie Database) pero **no está respaldado ni certificado** por TMDb. Los datos de películas se proporcionan bajo los [Términos de Uso de TMDb](https://www.themoviedb.org/documentation/api/terms-of-use).
 
[<img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_2-d537fb228cf3ded904ef09b136fe3fec72548ebc1fea3fbbd1ad9e36364db38b.svg" width="100" alt="TMDb Logo">](https://www.themoviedb.org/)
---

## ⚡ Características
- 🌍 Soporte de idiomas, español e inglés para el script desde `config.json`
- ✅ Obtiene metadatos de películas desde **TMDB** (título, director, género, sinopsis, etc.).
- 🏷️ Descarga imágenes como posters, screenshots y logos.
- 🎥 Descarga tráilers en distintos idiomas y resoluciones.
- 📊 Exporta los datos en **JSON** y los convierte en **TXT** (compatible con Pegasus Frontend).
- 🚀 Búsqueda en múltiples idiomas configurables.
- 🚫 Opción de ejecución manual (requiere de metadata.json previamente generado.)
- ⏳ Reintentos automáticos para descargas fallidas.

---

## 🛠️ Instalación y Requisitos

### 1. Clonar el repositorio

```sh
git clone git@github.com:ZagonAb/PMDB-Scraper.git
cd PMDB-Scraper
```

### 2. Requisitos previos

#### FFmpeg (Requerido en todos los sistemas)
FFmpeg es necesario para extraer información técnica de los archivos de video.

##### Instalación en Linux:
```bash
sudo apt-get update && sudo apt-get install ffmpeg
```

##### Instalación en Windows:
1. Descarga FFmpeg desde [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extrae el archivo ZIP
3. Copia la ruta de la carpeta `bin` (ejemplo: `C:\ffmpeg\bin`)
4. Agrega la ruta a las variables de entorno PATH:
   - Busca "Variables de entorno" en el menú de Windows
   - Edita las variables del sistema
   - Selecciona "PATH" y haz clic en "Editar"
   - Agrega la ruta a la carpeta `bin` de FFmpeg
5. Verifica la instalación abriendo PowerShell y ejecutando:
   ```
   ffmpeg -version
   ```

### 3. Dependencias de Python

#### En Linux:
1. Crea y activa un entorno virtual (recomendado):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

#### En Windows:
**Puede omitir la creación de un entorno virtual e instalar directamente las dependencias necesarias.**
   ```bash
   pip install -r requirements.txt
   ```

### 4. Configuración API de TMDB

Para utilizar PMDB-Scraper, necesitas una clave API de **The Movie Database (TMDB)**:

1. Crea una cuenta en [TMDB](https://www.themoviedb.org/)
2. Accede a tu perfil y ve a la sección **Configuración > API**
3. Crea una nueva clave API y cópiala en el archivo `config.json` bajo la clave `"api_key"`

### 5. Ejecutar el script

```bash
python pmdb-scraper.py
```

---

## 📂 Configuración (`config.json`)

Antes de ejecutar el scraper, configura el archivo `config.json` con los siguientes parámetros:

- **`api_key`**: Clave API de TMDB (requerida)
- **`ruta_peliculas`**: Ruta absoluta a la carpeta con archivos de video (ej: `/ruta/a/peliculas`)
- **`idiomas`**: Lista de idiomas para búsqueda (orden priorizado). Ej: `["es-ES", "es-MX", "en-US"]`
- **`metadata_language`**: Idiomas para metadatos (orden priorizado)
- **`obtener_datos`**: Campos booleanos para activar/desactivar tipos de metadatos
- **`calidad_trailer`**: Calidad del tráiler (`480p`, `720p` etc.)
- **`timeout_descargas`**: Tiempo máximo (segundos) para descargas
- **`max_reintentos`**: Número máximo de intentos si una descarga falla (ej: `3`)
- **`actualizar_manual`**: Para actualizar manualmente películas con metadatos erróneos o faltantes

**Notas sobre la configuración de idiomas:**
- Para el `trailer_lenguaje`, si el tráiler no está disponible en el idioma principal, buscará automáticamente en los siguientes idiomas listados
  - Ejemplo: `"trailer_lenguaje": ["es-MX", "en-US"]`
- En `idiomas`, configure según el idioma de sus títulos de películas
  - Ejemplo: `"idiomas": ["es-MX", "es-ES", "en-US"]` si tiene mezcla de títulos en español e inglés

**Ejemplo de configuración:**
```json
{
    "api_key": "YOUR_TMDB_API_KEY",
    "ruta_peliculas": "ROUTE/WHERE/ARE/YOUR/MOVIES",
    "idiomas": ["en-US"],
    "metadata_language": "en-US",
    "interface_language": "en-US",
    "exportar_formato": "json",
    "obtener_datos": {
        "titulo": true,
        "año": false,
        "duracion": true,
        "director": true,
        "productora": true,
        "rating": true,
        "descripcion": true,
        "generos": true,
        "poster": true,
        "backdrop": true,
        "logo": true,
        "fecha_lanzamiento": true,
        "trailer": true
    },
    "calidad_trailer": "480p",
    "trailer_lenguaje": ["en-US"],
    "buscar_series": false,
    "timeout_descargas": 10,
    "max_reintentos": 3,
    "actualizar_manual": false
}
```

---

## 📝 Consejos para mejor funcionamiento

- **Formato de nombres de archivos**: El script extrae el año incluido en los títulos de los archivos para mejorar la precisión de búsqueda. Se recomienda usar estos formatos:
  - `Die Hard (1988)` (Título original + año)
  - `Duro de matar (1988)` (Título traducido oficialmente + año)

- **⚠️ Razones por las que TMDB podría no encontrar algunos títulos:**
  - Errores ortográficos o de formato en el nombre del archivo
  - Títulos en diferentes idiomas (intente usar el título original)
  - Contenido no disponible en la base de datos de TMDB
  - Problemas con la API o limitaciones en la búsqueda
  - Restricciones regionales por licencias o derechos de distribución

- **⚠️ Limitaciones en la descarga de tráilers:**
  - Videos no disponibles en su país (bloqueo geográfico)
  - Videos eliminados por el propietario o por incumplimiento de políticas
  - Restricciones de edad que requieren inicio de sesión
  - Bloqueos por derechos de autor

  El script omitirá los tráilers con problemas y continuará con el resto de metadatos.

---

## 📂 Estructura de directorios creada

Al ejecutar PMDB-Scraper, se generará la siguiente estructura dentro de la carpeta de películas:

```
/media
 ├── boxFront/   (Posters de películas)
 ├── screenshot/ (Capturas de pantalla)
 ├── wheel/      (Logos de películas)
 ├── video/      (Tráilers descargados)
```

---

## 🎯 Ejemplo de salida

```sh
=== Resumen de la Operación ===
Archivo generado: metadata.json
Total de archivos procesados: 10
Películas encontradas: 8
Películas no encontradas: 2

=== Imágenes Descargadas ===
- Posters: 8
- Screenshots: 7
- Logos: 5
- Tráilers descargados: 6
```

## 📄 Generación de archivos

El script genera un archivo `metadata.json` con toda la información recopilada, que es necesario para:

1. Exportar los datos a Pegasus Frontend
2. Utilizar la función `actualizar_manual` en futuras ejecuciones
3. Si desea modificar el archivo `metadata.txt`, se recomienda realizar los mismos cambios en el archivo `metadata.json` para mantener la consistencia en futuras extracciones

---

## [(PMDB-Theme)](https://github.com/ZagonAb/PMDB-Theme) 
Interfaz diseñada específicamente para resaltar estos metadatos.

---

## ⚖️ Licencia

Este proyecto está bajo la [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.html).

## ✨ Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar o tienes algún problema con **PMDB-Scraper**, abre un **`issue`**.

---

### 💖 DONATE
I'm a programming enthusiast and passionate about free software, with a special love for classic games and the retro community. All my themes and projects are open-source and available for anyone to use. If you'd like to show your support or help me continue creating and improving these projects, you can make a voluntary donation. Every contribution, no matter how small, allows me to continue improving and maintaining these projects. 👾

[![Support on PayPal](https://img.shields.io/badge/PayPal-0070ba?style=for-the-badge)](https://paypal.me/ZagonAb)
[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/Gonzalo/donate)
