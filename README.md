# PMDB-Scraper

## ✨ Scraper de Metadatos de Películas para Pegasus Frontend

Pegasus Movie Data Base Scraper (PMDB-Scraper) es una herramienta diseñada para extraer metadatos de películas desde **The Movie Database (TMDb)** y generar archivos de metadatos compatibles con **Pegasus Frontend**. (Esta herramienta no tiene ninguna asociación oficial con Pegasus Frontend. Es un proyecto comunitario diseñado para ayudar a quienes desean integrar su colección de películas en su sistema de juego.)

---

![screen](https://github.com/ZagonAb/Pegasus-TMDB/blob/9348a301027ce44b88fe732e965de33ea4d8b2fe/.screenshot/screen.png)
![screen1](https://github.com/ZagonAb/Pegasus-TMDB/blob/9348a301027ce44b88fe732e965de33ea4d8b2fe/.screenshot/screen1.png)
![screen2](https://github.com/ZagonAb/Pegasus-TMDB/blob/9348a301027ce44b88fe732e965de33ea4d8b2fe/.screenshot/screen2.png)

## ⚡ Características
- 🌍 Soporte de idiomas, español e inglés para el script desde `config.json`
- ✅ Obtiene metadatos de películas desde **TMDb** (título, director, género, sinopsis, etc.).
- 🏷️ Descarga imágenes como posters, screenshots y logos.
- 🎥 Descarga tráilers en distintos idiomas y resoluciones.
- 📊 Exporta los datos en **JSON** y los convierte en **TXT** (compatible con Pegasus Frontend).
- 🚀 Búsqueda en múltiples idiomas configurables.
- 🚫 Opción de ejecución manual (requiere de metadata.json previamente generado.)
- ⏳ Reintentos automáticos para descargas fallidas.

## Consejos:

- El script extrae el año incluido en los títulos de los archivos y lo usa para mejorar la precisión de la búsqueda en TMDb. Si el año está presente en el nombre del archivo, el script lo extrae y lo compara con los años de lanzamiento de las películas en los resultados de búsqueda. Esto ayuda a seleccionar la película correcta en casos donde hay múltiples coincidencias con títulos similares.

- ⚠️ Es posible que The Movie Database (TMDb) no encuentre algunos títulos por varias razones. Aquí te explico algunas causas comunes:

Errores ortográficos o de formato: Si el título de la película está mal escrito o tiene un formato incorrecto, TMDb puede no encontrarlo. Asegúrate de escribir el título correctamente y en el idioma original si es necesario.

Títulos en diferentes idiomas: Algunas películas tienen títulos diferentes en otros idiomas. Si buscas un título traducido, es posible que no aparezca. Intenta buscar el título en su idioma original o un titulo traducido oficialmente.

Contenido no disponible en la base de datos: TMDb es una base de datos colaborativa, por lo que no todos los títulos están registrados. Si es una película muy nueva, antigua o poco conocida, es posible que no esté en la base de datos.

Problemas con la API o la búsqueda: al conectarse a TMDb a través de su API, puede haber problemas técnicos o limitaciones en la búsqueda.

Restricciones regionales: Algunos títulos pueden estar disponibles solo en ciertas regiones debido a licencias o derechos de distribución. Esto puede afectar los resultados de búsqueda.

Es importante tener un orden consistente en los títulos de los archivos de video para asegurar que el script pueda encontrar la película deseada de manera efectiva. Si los títulos no siguen un formato adecuado, puede ser difícil identificar la película correctamente.

- Ejemplo de formato adecuado de títulos:

- **Die Hard (1988)** (Titilo original + año)
- **Duro de matar (1988)** (titulo traducido oficialmente + año)

Si sigues este tipo de formato, será más fácil encontrar y raspar los metadatos de las películas de manera precisa.

- ⚠️ Limitaciones en la Descarga de Tráilers:

Al descargar tráilers de YouTube, es posible que encuentres algunas limitaciones debido a restricciones impuestas por la plataforma. Estas limitaciones pueden incluir:

Videos no disponibles en tu país: Algunos tráilers pueden estar bloqueados geográficamente y no estar disponibles en tu región.

Videos eliminados: Algunos tráilers pueden haber sido eliminados por el propietario del contenido o por incumplimiento de las políticas de YouTube.

Restricciones de edad: Algunos tráilers pueden requerir que el usuario inicie sesión en YouTube para confirmar su edad.

Derechos de autor: Algunos tráilers pueden estar bloqueados debido a reclamos de derechos de autor.

El script intentará descargar el tráiler en los idiomas configurados, pero si encuentra alguna de estas limitaciones, simplemente omitirá ese tráiler y continuará con el siguiente. Esto no afectará la descarga de otros metadatos (como imágenes, descripciones, etc.), pero el tráiler no estará disponible.

---

## 🛠 Instalación

1. Clona este repositorio o descárgalo manualmente:

   ```sh
    git git@github.com:ZagonAb/PMDB-Scraper.git
   ```
      
   ```sh
    cd PMDB-Scraper-main
   ```
2. Crea y activa un entorno virtual de Python (recomendado):

    ## Linux/macOS
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    
    ## Windows
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
    
3. Instala las dependencias dentro del entorno virtual:
    ```bash
    pip install -r requirements.txt
    ```

4. Configura tu archivo `config.json` según tus necesidades. **TMDB** utiliza los códigos de idioma basados en el estándar ISO 639-1 (códigos de dos letras, como es para español o en para inglés). En muchos casos, estos códigos se combinan con códigos de país según el estándar ISO 3166-1 para formar códigos como es-ES (español de España), es-MX (español Mexico), en-US (english United States) o pt-BR (portugués de Brasil) etc...

---

## 🔑 Cómo obtener una clave API de TMDb

Para utilizar PMDB-Scraper, necesitas una clave API de **The Movie Database (TMDb)**. Sigue estos pasos:

1. Crea una cuenta en [TMDb](https://www.themoviedb.org/).
2. Accede a tu perfil y ve a la sección **Configuración > API**.
3. Crea una nueva clave API y cópiala en `config.json` bajo la clave `"api_key"`.

---

## 📂 Configuración (`config.json`)

Antes de ejecutar el scraper, es importante configurar el archivo `config.json`. Algunos de los parámetros clave son:

- **`api_key`**: Clave de API de TMDB (requerida). Obtén una en [TMDB](https://www.themoviedb.org/settings/api).
- **`ruta_peliculas`**: Ruta absoluta a la carpeta con archivos de video (ej: `/ruta/a/peliculas`).
- **`idiomas`**: Lista de idiomas para búsqueda (orden priorizado). Ej: `["es-ES", "es-MX", "en-US"]`.
- **`metadata_language`**: Idiomas para metadatos (orden priorizado).
- **`obtener_datos`**: Objetivo con campos booleanos para activar/desactivar metadatos.
- **`calidad_trailer`**: Calidad del tráiler (`480p`, `720p` etc..).
- **`timeout_descargas`**: Tiempo máximo (segundos) para descargas.
- **`max_reintentos`**: **Número máximo de intentos** si una descarga falla (ej: `3`).
- **`actualizar_manual`**: Esta opción solo funcionará si previamente ha obtenido metadatos y desea actualizar aquellas películas que no fueron encontradas o que contienen metadatos erróneos. `actualizar_manual` en (`true`), el script le permite seleccionar manualmente la película de su archivo metadata.json para ofrecerle múltiples coincidencias y pueda actualizar los metadatos correctamente, automáticamente recreará metadata.txt

**Si el tráiler no está disponible en el idioma principal configurado en `trailer_lenguaje`, buscará automáticamente en otros idiomas en el orden en que están listados.**
- Ejemplo: `"trailer_lenguaje": ["es-MX", "en-US"],` Este es mi caso, ya que no todos los trailers siempre están en español.

**En `"idiomas":` es algo similar, en mi caso los títulos de las películas en mi colección no son 100% en español, también tengo películas en ingles con títulos en ingles así que requiero de una configuración algo mas que `es-MX` **
- Ejemplo: **"idiomas": ["es-MX", "es-ES", "en-US"],**

# Si no quiere algunos de los datos solo cambie de true a false.
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
        "trailer": false
    },
    "calidad_trailer": "480p",
    "trailer_lenguaje": ["en-US"],
    "buscar_series": false,
    "timeout_descargas": 10,
    "max_reintentos": 3,
    "actualizar_manual": false
}
```
- Una vez teminada la configuracion del archivo `config.json`
- Ejecuta el script principal `pmdb-scraper.py`

```sh
python3 pmdb-scraper.py
```
---


## 📂 Estructura de directorio creada

Cuando se ejecuta PMDB-Scraper, se genera la siguiente estructura de directorios dentro de la carpeta de películas:

```
/media
 ├── boxFront/   (Posters de películas)
 ├── screenshot/ (Capturas de pantalla)
 ├── wheel/      (Logos de películas)
 ├── video/      (Tráilers descargados)
```

---
## 🎯 Ejemplo de Salida

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

1. Exportar los datos a Pegasus Frontend.
2. Utilizar la función `actualizar_manual` en futuras ejecuciones.
3. Una vez obtenidos los metadatos, si desea modificar el archivo `metadata.txt `, se recomienda realizar los mismos cambios en el archivo  `metadata.json` para mantener la consistencia entre ambos archivos en futuras extracciones de metadatos.
---

## [(PMDB-Theme)](https://github.com/ZagonAb/PMDB-Theme) Interfaz diseñada específicamente para resaltar estos metadatos.
---

## ⚖️ Licencia

🔗 Este proyecto está bajo la [(CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)
---

## ✨ Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar **PMDB-Scraper**, abre un **`issue`**.

---
