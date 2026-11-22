from pathlib import Path
import pediment_windows,visible_wall_and_bay
MATERIAL=pediment_windows.STONE
TEXTURE=Path(pediment_windows.PALETTE[MATERIAL]['texture'])
TEXTURES={n:Path(d['texture']) for module in (pediment_windows,visible_wall_and_bay) for n,d in module.PALETTE.items() if 'texture' in d}
