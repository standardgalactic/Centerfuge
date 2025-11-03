# Yarncrawler Framework

This archive collects runnable, cross‑platform prototypes for the following projects:
- **yarncrawler/**: Blender still-image generator (no animation)
- **blastoids/**: retro vector cockpit shooter prototype (pygame)
- **spherepop/**: bubble‑based programming language demo (pure Python)
- **entropy_edge/**: CLI 4X strategy prototype (pure Python)
- **semantic_infrastructure/**: semantic merge prototype (pure Python)
- **music/**: audio metadata and simple pygame visualizer
- **essays/**: short Markdown essays

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
# Try any project:
python blastoids/blastoids_game.py
python spherepop/spherepop.py examples/hello_spherepop.sp
python entropy_edge/entropy_edge.py --help
python semantic_infrastructure/semantic_merge.py --help
python music/glitch_audio_player.py
# Blender-based (requires Blender installed on PATH):
python yarncrawler/yarncrawler_blender_gen.py --outdir out --scenes all --render
```
