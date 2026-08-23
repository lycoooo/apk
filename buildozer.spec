[app]
title = Trial Detect
package.name = trialdetect
package.domain = com.lyco.trialdetect
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy==2.3.0,requests

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
