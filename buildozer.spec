[app]
title = Sweet Waters Pub POS
package.name = sweetwaterspub
package.domain = com.sweetwaterspub

source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,txt

version = 3.2.1

requirements = python3,kivy

orientation = portrait
fullscreen = 1

android.permissions = VIBRATE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

p4a.bootstrap = sdl2

android.archs = arm64-v8a, armeabi-v7a
android.split = 1
android.compress = 1
android.reduce_resource_usage = 1

log_level = 0

presplash_color = #16213e

[buildozer]
warn_on_root = 0
