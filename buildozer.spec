[app]
# (str) Title of your application
# Name displayed on the Android home screen.
title = BoardRockChess

# (str) Package name
package.name = boardrockchess

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let's keep py and others)
source.include_exts = py,txt,md,json

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
requirements = python3, pygame

# (bool) Indicate if the application should be fullscreen
fullscreen = 1

# (str) Supported orientation (one of landscape, portrait or all)
orientation = landscape

[buildozer]
# (int) Log level (0 = error, 1 = warning, 2 = info, 3 = debug (default))
log_level = 2

# (bool) Warn if another OS uses root; Android packaging typically needs Linux
warn_on_root = 1
