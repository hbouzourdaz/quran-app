from __future__ import annotations

from typing import Dict


LANGUAGE_LABELS = {
    "fr": "Français",
    "en": "English",
}

RTL_LANGUAGES: set = set()

QUALITY_LABELS = {
    "fr": {
        "360p": "360p",
        "720p": "720p",
        "1080p": "1080p",
        "Audio only": "Audio uniquement",
    },
    "en": {
        "360p": "360p",
        "720p": "720p",
        "1080p": "1080p",
        "Audio only": "Audio only",
    },
}

STATUS_LABELS = {
    "fr": {
        "downloading": "Téléchargement en cours",
        "complete": "Terminé",
        "failed": "Échoué",
        "unknown": "Inconnu",
    },
    "en": {
        "downloading": "Downloading",
        "complete": "Complete",
        "failed": "Failed",
        "unknown": "Unknown",
    },
}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "fr": {
        "app_title": "Hakim Downloader",
        "home_title": "Accueil",
        "downloads_title": "Historique",
        "settings_title": "Paramètres",
        "success_title": "Succès",
        "success_message": "Le téléchargement est terminé. Voulez-vous voir la vidéo ?",
        "view_video": "Voir",
        "close": "Fermer",
        "footer_text": "Hakim Downloader v1.0\n© 2026 Hakim Bouzourdaz. Tous droits réservés.",
        "home_headline": "Téléchargement simple",
        "home_subtitle": "Collez le lien et choisissez la qualité.",
        "url_hint": "Lien de la vidéo",
        "url_helper": "Supporte YT, FB, Insta, X, TikTok",
        "fetch": "Récupérer",
        "paste": "Coller",
        "preview_empty_title": "Aucune vidéo",
        "preview_empty_meta": "Les détails apparaîtront ici.",
        "quality": "Qualité : {quality}",
        "download": "Télécharger",
        "idle": "Prêt",
        "invalid_url": "Lien invalide.",
        "fetching_metadata": "Récupération...",
        "clipboard_detected": "Lien détecté",
        "ready_download": "Prêt.",
        "fetch_before_download": "Récupérez d'abord.",
        "starting_download": "Démarrage...",
        "downloading": "Téléchargement",
        "processing": "Traitement",
        "finalizing": "Finalisation",
        "complete": "Terminé : {name}",
        "notification_complete_title": "Terminé",
        "refresh": "Actualiser",
        "clear": "Effacer",
        "history_empty": "Aucun historique",
        "untitled": "Sans titre",
        "open_folder": "Ouvrir",
        "no_path": "Aucun chemin",
        "open_folder_failed": "Erreur : {error}",
        "download_folder": "Dossier de téléchargement",
        "browse": "Parcourir",
        "save_path": "Enregistrer",
        "default_quality": "Qualité : {quality}",
        "default_quality_short": "Qualité par défaut",
        "prefer_audio": "Audio uniquement",
        "clipboard_autofill": "Détection automatique",
        "completion_notifications": "Notifications",
        "dark_theme": "Thème sombre",
        "language": "Langue : {language}",
        "language_short": "Langue",
        "ffmpeg_hint": "Chemin ffmpeg",
        "save_ffmpeg": "Enregistrer ffmpeg",
        "file_picker_unavailable": "Sélecteur indisponible",
        "folder_create_failed": "Erreur de dossier",
        "folder_saved": "Dossier enregistré",
        "ffmpeg_saved": "Chemin enregistré",
        "ffmpeg_missing": "FFmpeg est requis mais introuvable. Installez-le ou réglez le chemin dans les Paramètres.",
    },
    "en": {
        "app_title": "Hakim Downloader",
        "home_title": "Home",
        "downloads_title": "History",
        "settings_title": "Settings",
        "success_title": "Success",
        "success_message": "Download complete. Do you want to view the video?",
        "view_video": "View",
        "close": "Close",
        "footer_text": "Hakim Downloader v1.0\n© 2026 Hakim Bouzourdaz. All rights reserved.",
        "home_headline": "Easy download",
        "home_subtitle": "Paste a link and choose quality.",
        "url_hint": "Video URL",
        "url_helper": "Supports YT, FB, Insta, X, TikTok",
        "fetch": "Fetch",
        "paste": "Paste",
        "preview_empty_title": "No video",
        "preview_empty_meta": "Details will appear here.",
        "quality": "Quality: {quality}",
        "download": "Download",
        "idle": "Idle",
        "invalid_url": "Invalid URL.",
        "fetching_metadata": "Fetching...",
        "clipboard_detected": "Link detected",
        "ready_download": "Ready.",
        "fetch_before_download": "Fetch data first.",
        "starting_download": "Starting...",
        "downloading": "Downloading",
        "processing": "Processing",
        "finalizing": "Finalizing",
        "complete": "Complete: {name}",
        "notification_complete_title": "Complete",
        "refresh": "Refresh",
        "clear": "Clear",
        "history_empty": "No history",
        "untitled": "Untitled",
        "open_folder": "Open",
        "no_path": "No path",
        "open_folder_failed": "Error: {error}",
        "download_folder": "Download folder",
        "browse": "Browse",
        "save_path": "Save",
        "default_quality": "Quality: {quality}",
        "default_quality_short": "Default quality",
        "prefer_audio": "Audio only",
        "clipboard_autofill": "Auto-detect link",
        "completion_notifications": "Notifications",
        "dark_theme": "Dark theme",
        "language": "Language: {language}",
        "language_short": "Language",
        "ffmpeg_hint": "ffmpeg path",
        "save_ffmpeg": "Save ffmpeg",
        "file_picker_unavailable": "Picker unavailable",
        "folder_create_failed": "Folder error",
        "folder_saved": "Folder saved",
        "ffmpeg_saved": "Path saved",
        "ffmpeg_missing": "FFmpeg is required but not found. Please install it or set the path in Settings.",
    },
}


def normalize_language(language: str) -> str:
    return language if language in TRANSLATIONS else "fr"


def is_rtl(language: str) -> bool:
    return normalize_language(language) in RTL_LANGUAGES


def tr(lang: str, key: str, **values) -> str:
    lang = normalize_language(lang)
    text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key, key)
    return text.format(**values) if values else text


def quality_label(language: str, quality: str) -> str:
    language = normalize_language(language)
    return QUALITY_LABELS.get(language, QUALITY_LABELS["en"]).get(quality, quality)


def status_label(language: str, status: str) -> str:
    language = normalize_language(language)
    key = (status or "unknown").lower()
    return STATUS_LABELS.get(language, STATUS_LABELS["en"]).get(key, status.title())
