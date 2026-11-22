"""Repeat-sampled original exterior materials for the Changshu Road lane frontage."""
from pathlib import Path
S=Path(__file__).resolve().parent
PLASTER='Rongkang | grey pebble render'
PAVE='Rongkang | worn stone paving'
TEXTURES={PLASTER:S/'rongkang-grey-roughcast.jpg',PAVE:S/'rongkang-paved-stone.jpg',
          'Rongkang | reflected blue-grey glass':S/'rongkang-window-glass.png',
          'Rongkang | glass in shade':S/'rongkang-window-glass.png'}

for name in ['street shop glazing','dark shop glazing','warm showroom glazing']:
    TEXTURES['Rongkang | '+name]=S/'rongkang-shop-glass.jpg'
