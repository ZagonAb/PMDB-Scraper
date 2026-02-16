# PMDB-Scraper

**PMDB-Scraper (Pegasus Movie Data Base Scraper)** is a tool that retrieves movie metadata from **The Movie Database (TMDB)** and generates metadata files compatible with **Pegasus Frontend**.

This is a **community project** and is **not officially affiliated with Pegasus Frontend**. Its goal is to help users integrate local movie collections into their gaming or media setups powered by Pegasus.

---

## Preview

![screen](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen.png)
![screen1](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen1.png)
![screen2](https://github.com/ZagonAb/PMDB-Scraper/blob/98e992cf3b4fc97f58b3a31d618951a404c8a30b/.screenshot/screen2.png)

---

## Disclaimer

This product uses the TMDb API but is **not endorsed or certified by TMDb**.

Movie data is provided according to the
[TMDb Terms of Use](https://www.themoviedb.org/documentation/api/terms-of-use).

[<img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_2-d537fb228cf3ded904ef09b136fe3fec72548ebc1fea3fbbd1ad9e36364db38b.svg" width="100" alt="TMDb Logo">](https://www.themoviedb.org/)

---

## Features

* Multi-language support (Spanish and English interface)
* Fetches movie metadata from TMDB:

  * title, director, genres, synopsis, ratings, and more
* Downloads artwork:

  * posters
  * screenshots/backdrops
  * logos
* Trailer downloading with selectable language and resolution
* JSON export with automatic conversion to Pegasus-compatible TXT format
* Configurable multi-language search priority
* Manual update mode using existing metadata
* Automatic retry system for failed downloads

---

## Requirements

### FFmpeg (Required)

FFmpeg is used to extract technical information from video files.

#### Linux

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### Windows

1. Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract the archive
3. Add the `bin` folder to your system PATH
4. Verify installation:

```bash
ffmpeg -version
```

---

## Installation

### 1. Clone the repository

```bash
git clone git@github.com:ZagonAb/PMDB-Scraper.git
cd PMDB-Scraper
```

### 2. Install Python dependencies

#### Linux (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows

```bash
pip install -r requirements.txt
```

---

## TMDB API Setup

1. Create an account at [https://www.themoviedb.org](https://www.themoviedb.org)
2. Navigate to **Settings → API**
3. Generate an API key
4. Add it to `config.json`:

```json
"api_key": "YOUR_TMDB_API_KEY"
```

---

## Usage

Run the scraper:

```bash
python pmdb-scraper.py
```

---

## Configuration (`config.json`)

Main configuration options:

| Option              | Description                       |
| ------------------- | --------------------------------- |
| `api_key`           | TMDB API key                      |
| `ruta_peliculas`    | Absolute path to movie directory  |
| `idiomas`           | Search languages (priority order) |
| `metadata_language` | Metadata language                 |
| `obtener_datos`     | Enable/disable metadata fields    |
| `calidad_trailer`   | Trailer resolution                |
| `timeout_descargas` | Download timeout (seconds)        |
| `max_reintentos`    | Retry attempts                    |
| `actualizar_manual` | Manual metadata update mode       |

### Language Notes

* Trailer language falls back automatically if unavailable.
* Configure search languages based on movie title language.

Example:

```json
"idiomas": ["es-MX", "es-ES", "en-US"]
```

---

## Recommended File Naming

For best matching accuracy, include the release year:

```
Die Hard (1988)
Duro de matar (1988)
```

---

## Known Limitations

### Metadata matching issues may occur due to:

* Filename spelling errors
* Language differences
* Missing entries in TMDB
* API limitations
* Regional licensing restrictions

### Trailer download limitations

Some trailers may be skipped if:

* Geo-blocked in your region
* Removed by the uploader
* Age-restricted
* Copyright-restricted

The scraper will continue processing remaining metadata automatically.

---

## Generated Directory Structure

```
/media
 ├── boxFront/   Movie posters
 ├── screenshot/ Screenshots
 ├── wheel/      Logos
 ├── video/      Trailers
```

---

## Example Output

```
=== Operation Summary ===
Generated file: metadata.json
Processed files: 10
Movies found: 8
Movies missing: 2

=== Downloaded Assets ===
Posters: 8
Screenshots: 7
Logos: 5
Trailers: 6
```

---

## Generated Files

The scraper creates a `metadata.json` file used for:

* Exporting data to Pegasus Frontend
* Manual update mode
* Maintaining consistency when editing metadata manually

If you modify `metadata.txt`, it is recommended to apply the same changes to `metadata.json`.

---

## Related Project

**PMDB-Theme**
[https://github.com/ZagonAb/PMDB-Theme](https://github.com/ZagonAb/PMDB-Theme)

A user interface designed specifically to showcase generated metadata.

---

## License

Licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

---

## Contributing

Contributions are welcome!

If you find a bug or want to improve PMDB-Scraper, please open an **issue** or submit a pull request.

---

### 💖 DONATE
I'm a programming enthusiast and passionate about free software, with a special love for classic games and the retro community. All my themes and projects are open-source and available for anyone to use. If you'd like to show your support or help me continue creating and improving these projects, you can make a voluntary donation. Every contribution, no matter how small, allows me to continue improving and maintaining these projects. 👾

[![Support on PayPal](https://img.shields.io/badge/PayPal-0070ba?style=for-the-badge)](https://paypal.me/ZagonAb)
[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/Gonzalo/donate)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-29abe0?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/zagonab)
