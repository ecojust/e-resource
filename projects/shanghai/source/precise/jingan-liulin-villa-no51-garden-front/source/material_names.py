from pathlib import Path
import court_gate,entrance_portal,garden_approach,residence_wings
MATERIAL=residence_wings.BRICK
TEXTURE=Path(residence_wings.PALETTE[MATERIAL]['texture'])
TEXTURES={key:Path(surf['texture']) for module in (court_gate,entrance_portal,garden_approach,residence_wings) for key,surf in module.PALETTE.items() if 'texture' in surf}
