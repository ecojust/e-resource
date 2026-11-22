from pathlib import Path
SOURCE=Path(__file__).resolve().parent
PLASTER='Yimin canteen | blue grey facing brick'
RED='Yimin canteen | warm brick courses'
TILE='Yimin canteen | weathered roof tile'
TEXTURES={PLASTER:SOURCE/'canal-grey-brick.jpg',RED:SOURCE/'terracotta-bands.jpg',TILE:SOURCE/'weathered-roof-tiles.jpg'}
REPEAT={PLASTER:(1.92,.80),RED:(1.92,1.008),TILE:(1.12,1.36)}
