"""Projected brick and exposed pebble finishes of the Yefeng Art Society facade."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
PLASTER = 'Gongyuanfang No. 24 | exposed pebble aggregate'
RED = 'Gongyuanfang No. 24 | old red running bond'
DARK = 'Gongyuanfang No. 24 | weathered red facing'
TEXTURES = {PLASTER: SOURCE/'pebble-dash.jpg', RED: SOURCE/'red-brick.jpg', DARK: SOURCE/'weathered-brick.jpg'}
TILE_METRES = {PLASTER:(.57,.57), RED:(1.92,1.008), DARK:(1.92,1.008)}
