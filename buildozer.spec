[app]
title = Sweet Waters Pub POS
package.name = sweetwaterspub
package.domain = com.sweetwaterspub

source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,txt

version = 2.0.0

requirements = python3,kivy,fpdf2

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

p4a.bootstrap = sdl2

android.arch = arm64-v8a

log_level = 0

presplash_color = #16213e

[buildozer]
warn_on_root = 0
