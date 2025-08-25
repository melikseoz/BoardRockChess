
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

## Configuration
Gameplay options can be tweaked by editing `config.json`. In addition to grid
and fire settings, you can now control power-up behavior:

- `powerup_length`: number of turns a collected power-up remains effective
- `powerup_lifetime`: how many sub-turns a power-up stays on the map
- `powerup_spawn_chance`: chance per sub-turn to spawn a power-up
- `powerup_max`: maximum simultaneous power-ups on the board

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
# requires Linux
uv run buildozer -v android debug
```

The packaged APK will appear in the `bin/` directory.
