
# Hunter–Human–Target (Canvas Fire Build)

Exported directly from the Canvas document. Uses Pygame.

## Install
```bash
pip install pygame
```

## Run
```bash
python main.py
```

## Controls
- Movement: **QWE / ASD / ZXC** (8 directions)
- **S** = Skip turn
- **O** = Toggle obstacles
- **R** = Restart round
- **ESC** = Quit

## Android
The project ships with a `buildozer.spec` configuration for [Buildozer](https://github.com/kivy/buildozer).
To create an Android APK:

```bash
# install buildozer and its dependencies (requires Linux)
pip install buildozer
buildozer -v android debug
```

The packaged APK will appear in the `bin/` directory.
