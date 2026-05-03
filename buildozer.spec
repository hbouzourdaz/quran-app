[app]

title = Hakim Downloader
package.name = hakimdownloader
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json,ttf,txt
source.exclude_dirs = .git,.venv,venv,__pycache__,build,dist

version = 1.0.0
requirements = python3,kivy==2.3.1,kivymd==1.2.0,yt-dlp,plyer,certifi,requests,urllib3,pycryptodomex,mutagen,websockets,brotli,ffmpeg
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO,POST_NOTIFICATIONS,WAKE_LOCK,MANAGE_EXTERNAL_STORAGE
android.api = 35
android.minapi = 24
android.ndk = 27c
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# Use the latest python-for-android to get Android 16 (16KB page size) fixes
p4a.branch = develop

android.gradle_dependencies =
android.add_src =
android.add_jars =
android.add_aars =
android.private_storage = True

presplash.filename = assets/splash.png
icon.filename = assets/icon.png

[buildozer]

log_level = 2
warn_on_root = 1
