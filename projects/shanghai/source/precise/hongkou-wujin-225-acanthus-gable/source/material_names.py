"""Masonry finishes for the photographed courtyard."""
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
PLASTER='Wujin courtyard | weathered blue-grey brick'
RED='Wujin courtyard | warm unpainted brick'
WHITE='Wujin courtyard | whitewashed brick'
TEXTURES={PLASTER:SOURCE/'blue-grey-brick.jpg',RED:SOURCE/'red-brick.jpg',WHITE:SOURCE/'painted-brick.jpg'}
