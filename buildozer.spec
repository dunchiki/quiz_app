[app]

title = Quiz App
package.name = quizapp
package.domain = com.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,csv,ttf,otf
source.exclude_dirs = .git,.venv,venv,__pycache__,app_tests,.pytest_cache,.mypy_cache

version = 0.1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 34
android.minapi = 24
android.sdk = 34
android.ndk = 25b
android.accept_sdk_license = True

# Android 13+ で戻るボタン挙動の差異を避けるために SDL2 の推奨設定に合わせる
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
