"""Material names and original textures used when opening the editable scene in Blender."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
MATERIAL = 'Guiren | grey running-bond brick'
TEXTURES = {
    'Guiren | grey running-bond brick': SOURCE / 'guiren-grey-brick.jpg',
    'Guiren | russet band brick': SOURCE / 'guiren-russet-brick.jpg',
    'Guiren | green address plate': SOURCE / 'guiren-address-plate.png',
    'Guiren windows | shaded glass': SOURCE / 'guiren-window-glass.png',
    'Guiren windows | cool reflected glass': SOURCE / 'guiren-window-glass.png',
    'Guiren windows | grey-green lower glass': SOURCE / 'guiren-window-glass.png',
}
TEXTURE = TEXTURES[MATERIAL]
