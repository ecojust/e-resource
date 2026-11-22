from pathlib import Path
import street_shops_and_roof,continental_street_wall,continental_window_sashes,pointed_piers
MATERIAL=continental_street_wall.BRICK
TEXTURE=Path(continental_street_wall.PALETTE[MATERIAL]['texture'])
TEXTURES={k:Path(a['texture']) for module in (street_shops_and_roof,continental_street_wall,continental_window_sashes,pointed_piers) for k,a in module.PALETTE.items() if 'texture' in a}
