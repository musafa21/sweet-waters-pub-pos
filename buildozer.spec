[app]
title = Sweet Waters Pub POS
package.name = sweetwaterspub
package.domain = com.sweetwaterspub

source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,txt
source.include_patterns = assets/*,data/*

requirements = python3,kivy,kivymd,fpdf2,openpyxl,pillow

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

# Gradle build dependencies
android.gradle_dependencies = 

# P4A bootstrap
p4a.bootstrap = sdl2

# Icon and presplash
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

# Android specific
android.arch = arm64-v8a
android.release_artifact = aab

# Window
window_icon = 
window_title = Sweet Waters Pub POS

# Log level
log_level = 2

# Presplash color
presplash_color = #2c3e50

[buildozer]
warn_on_root = 0
