[app]
title = Sweet Waters Pub POS
package.name = sweetwaterspub
package.domain = com.sweetwaterspub

source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,txt

version = 3.1.0

requirements = python3,kivy,fpdf2

orientation = portrait
fullscreen = 1

android.permissions = INTERNET

android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

p4a.bootstrap = sdl2

android.archs = arm64-v8a

log_level = 0

presplash_color = #16213e

[buildozer]
warn_on_root = 0
