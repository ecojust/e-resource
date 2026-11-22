from pathlib import Path
import historic_window_front,central_tablet,street_balcony
MATERIAL=historic_window_front.WALL
TEXTURE=Path(historic_window_front.PALETTE[MATERIAL]['texture'])
TEXTURES={k:Path(s['texture']) for module in (historic_window_front,central_tablet,street_balcony) for k,s in module.PALETTE.items() if 'texture' in s}
