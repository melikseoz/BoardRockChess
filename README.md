
# Hunter–Human–Target (Canvas Fire Build)

Exported directly from the Canvas document. Uses Pygame.

## Install
```bash
uv sync
```

## Run
```bash
uv run main.py
```

## Controls
- Movement: **QWE / ASD / ZXC** (8 directions)
- **S** = Skip turn
- **O** = Toggle obstacles
- **R** = Restart round
- **ESC** = Quit

## Power-ups
Randomly appearing power-ups add temporary twists:

- **Speed** – green arrow; move two tiles per turn for two turns.
- **Time Stop** – red turtle; skips the opponent's next two turns.

## Android
The project ships with a `buildozer.spec` configuration for [Buildozer](https://github.com/kivy/buildozer).
To create an Android APK:

```bash
# requires Linux
uv run buildozer -v android debug
```

The packaged APK will appear in the `bin/` directory.
