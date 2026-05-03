# Kivy Video Downloader

A KivyMD desktop and Android video downloader powered by `yt-dlp`.

## Features

- Fetches metadata and thumbnails before download.
- Supports YouTube, Facebook, Instagram, Twitter/X, TikTok, and any other site supported by `yt-dlp`.
- Downloads 360p, 720p, 1080p, or MP3 audio.
- Uses background threads so the UI stays responsive.
- Resumes interrupted downloads through `yt-dlp` partial files.
- Saves settings and download history locally.
- Supports dark/light theme, clipboard URL detection, and completion notifications.
- Includes Arabic/English UI language switching and bundles the Rubik font.

## Desktop Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Install `ffmpeg` and make sure it is on your `PATH` for audio extraction and best-quality video merging. You can also set the ffmpeg path in the app settings screen.

## Build Android APK

Buildozer runs on Linux or macOS. On Windows, use WSL2 and keep the project inside the Linux filesystem for best results.

```bash
python3 -m pip install --user buildozer cython
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
buildozer android debug
```

The debug APK will be created under `bin/`. Install it with:

```bash
buildozer android deploy run logcat
```

## Notes

- Some platforms require login, cookies, or block automated downloads. The app reports those failures from `yt-dlp`.
- For the most reliable extractor support, update `yt-dlp` regularly.
- Android storage rules vary by OS version. The default folder is `Download/Kivy Video Downloader` when accessible, with app-private storage as a fallback.
- MP3 extraction and separate video/audio merging require ffmpeg. The Buildozer spec includes the `ffmpeg` python-for-android recipe.
- The bundled Rubik font is stored in `assets/fonts/` under the Open Font License.
