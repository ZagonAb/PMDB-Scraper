# PMDB-Scraper

## ✨ Movie Metadata Scraper for Pegasus Frontend

Pegasus Movie Data Base Scraper (PMDB-Scraper) is a tool designed to extract movie metadata from **The Movie Database (TMDB)** and generate metadata files compatible with **Pegasus Frontend**. (This tool has no official association with Pegasus Frontend. It is a community project created to help users integrate their movie collections into their gaming systems.)

---

![screen](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen.png)
![screen1](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen1.png)
![screen2](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen2.png)

---

## ⚠️ Notice

This tool uses the API from [TMDb](https://www.themoviedb.org/) (The Movie Database) but is **not endorsed or certified** by TMDb. Movie data is provided under the [TMDb Terms of Use](https://www.themoviedb.org/documentation/api/terms-of-use).

[<img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_2-d537fb228cf3ded904ef09b136fe3fec72548ebc1fea3fbbd1ad9e36364db38b.svg" width="100" alt="TMDb Logo">](https://www.themoviedb.org/)

---

## ⚡ Features

* 🌍 Language support (Spanish and English) configurable via `config.json`
* ✅ Fetches movie metadata from **TMDB** (title, director, genre, synopsis, etc.)
* 🏷️ Downloads images such as posters, screenshots, and logos
* 🎥 Downloads trailers in multiple languages and resolutions
* 📊 Exports data in **JSON** and converts it into **TXT** (Pegasus Frontend compatible)
* 🚀 Multi-language configurable search
* 🚫 Manual execution mode (requires a previously generated `metadata.json`)
* ⏳ Automatic retries for failed downloads

---

## 🛠️ Installation and Requirements

### 1. Clone the repository

```sh
git clone git@github.com:ZagonAb/PMDB-Scraper.git
cd PMDB-Scraper
```

### 2. Prerequisites

#### FFmpeg (Required on all systems)

FFmpeg is required to extract technical information from video files.

##### Installation on Linux:

```bash
sudo apt-get update && sudo apt-get install ffmpeg
```

##### Installation on Windows:

1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the ZIP file
3. Copy the path to the `bin` folder (example: `C:\ffmpeg\bin`)
4. Add the path to the system PATH environment variables:

   * Search for "Environment Variables" in the Windows menu
   * Edit system variables
   * Select "PATH" and click "Edit"
   * Add the FFmpeg `bin` folder path
5. Verify installation by opening PowerShell and running:

   ```
   ffmpeg -version
   ```

### 3. Python Dependencies

#### On Linux:

1. Create and activate a virtual environment (recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

#### On Windows:

**You may skip creating a virtual environment and install dependencies directly.**

```bash
pip install -r requirements.txt
```

### 4. TMDB API Configuration

To use PMDB-Scraper, you need an API key from **The Movie Database (TMDB)**:

1. Create an account at [TMDB](https://www.themoviedb.org/)
2. Go to **Settings > API** in your profile
3. Create a new API key and copy it into `config.json` under `"api_key"`

### 5. Run the script

```bash
python pmdb-scraper.py
```

---

## 📂 Configuration (`config.json`)

Before running the scraper, configure the `config.json` file with the following parameters:

* **`api_key`**: TMDB API key (required)
* **`ruta_peliculas`**: Absolute path to the movie folder (e.g. `/path/to/movies`)
* **`idiomas`**: Search language list (priority order). Example: `["es-ES", "es-MX", "en-US"]`
* **`metadata_language`**: Metadata language (priority order)
* **`obtener_datos`**: Boolean fields to enable/disable metadata types
* **`calidad_trailer`**: Trailer quality (`480p`, `720p`, etc.)
* **`timeout_descargas`**: Maximum download time (seconds)
* **`max_reintentos`**: Maximum retry attempts if a download fails (e.g. `3`)
* **`actualizar_manual`**: Manually update movies with incorrect or missing metadata

**Language configuration notes:**

* For `trailer_lenguaje`, if the trailer is not available in the primary language, it will automatically search the next listed languages.

  * Example: `"trailer_lenguaje": ["es-MX", "en-US"]`
* In `idiomas`, configure according to the language of your movie titles.

  * Example: `"idiomas": ["es-MX", "es-ES", "en-US"]` if you have mixed Spanish and English titles

**Configuration example:**

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

## 📝 Tips for Best Results

* **File naming format**: The script extracts the year included in filenames to improve search accuracy. Recommended formats:

  * `Die Hard (1988)` (Original title + year)
  * `Duro de matar (1988)` (Official translated title + year)

* **⚠️ Reasons why TMDB may not find some titles:**

  * Spelling or formatting errors in filenames
  * Titles in different languages (try the original title)
  * Content not available in TMDB’s database
  * API issues or search limitations
  * Regional restrictions due to licensing or distribution rights

* **⚠️ Trailer download limitations:**

  * Videos unavailable in your country (geo-blocking)
  * Videos removed by the owner or policy violations
  * Age restrictions requiring login
  * Copyright restrictions

The script will skip problematic trailers and continue processing the remaining metadata.

---

## 📂 Generated Directory Structure

When running PMDB-Scraper, the following structure will be created inside the movie folder:

```
/media
 ├── boxFront/   (Movie posters)
 ├── screenshot/ (Screenshots)
 ├── wheel/      (Movie logos)
 ├── video/      (Downloaded trailers)
```

---

## 🎯 Output Example

```sh
=== Operation Summary ===
Generated file: metadata.json
Total files processed: 10
Movies found: 8
Movies not found: 2

=== Downloaded Images ===
- Posters: 8
- Screenshots: 7
- Logos: 5
- Downloaded trailers: 6
```

---

## 📄 File Generation

The script generates a `metadata.json` file containing all collected information, which is required for:

1. Exporting data to Pegasus Frontend
2. Using the `actualizar_manual` feature in future runs
3. If you modify `metadata.txt`, it is recommended to apply the same changes to `metadata.json` to maintain consistency in future extractions

---

## [(PMDB-Theme)](https://github.com/ZagonAb/PMDB-Theme)

Interface specifically designed to highlight this metadata.

---

## ⚖️ License

This project is licensed under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.html).

---

## ✨ Contributions

Contributions are welcome! If you want to improve or encounter any issues with **PMDB-Scraper**, please open an **`issue`**.

---

### 💖 DONATE
I'm a programming enthusiast and passionate about free software, with a special love for classic games and the retro community. All my themes and projects are open-source and available for anyone to use. If you'd like to show your support or help me continue creating and improving these projects, you can make a voluntary donation. Every contribution, no matter how small, allows me to continue improving and maintaining these projects. 👾

[![Support on PayPal](https://img.shields.io/badge/PayPal-0070ba?style=for-the-badge)](https://paypal.me/ZagonAb)
[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/Gonzalo/donate)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-29abe0?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/zagonab)
