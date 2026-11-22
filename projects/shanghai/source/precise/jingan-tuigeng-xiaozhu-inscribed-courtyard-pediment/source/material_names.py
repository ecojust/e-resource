"""Material names and original textures used when opening the editable scene in Blender."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
MATERIAL = 'Limestone | inscribed field'
TEXTURES = {
    'Lime plaster | buff-grey wall': SOURCE / 'lime-aggregate.jpg',
    'Cast stone | rounded arc moulding': SOURCE / 'cut-stone-grain.jpg',
    'Limestone | inscribed field': SOURCE / 'cut-stone-grain.jpg',
    'Limestone | raised geometrical key': SOURCE / 'cut-stone-grain.jpg',
    'Limestone | positive running script': SOURCE / 'cut-stone-grain.jpg',
}
TEXTURE = TEXTURES[MATERIAL]
