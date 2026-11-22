"""Original repeat-sampled textures available both in Blender and the mesh builder."""
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
PLASTER='Postal courtyard | pale lime render'
PLINTH='Postal courtyard | sand-faced stone'
TEXTURES={PLASTER:SOURCE/'postal-lime-render.jpg',PLINTH:SOURCE/'postal-sand-stone.jpg'}
for tone in ('shaded glass','grey-green glass','sky-reflecting glass'):
    TEXTURES['Postal office windows | '+tone]=SOURCE/'postal-window-glass.png'
