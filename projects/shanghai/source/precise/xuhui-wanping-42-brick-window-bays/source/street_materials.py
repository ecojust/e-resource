"""Materials for 42 Wanping Road. Brick texture generation is kept in brick_finishes.py."""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
PRECISE = HERE.parents[1]
sys.path.append(str(PRECISE/'xuhui-yanqing-159-garden-residence/source'))
from residence_materials import finish

YELLOW = 'Wanping 42 | ochre facing brick'
RED = 'Wanping 42 | red facing brick'
SOLDIER = 'Wanping 42 | vertical red soldier brick'
STEEL = 'Wanping 42 | red-brown steel'
GLASS = 'Wanping 42 | grey glass'
CREAM = 'Wanping 42 | cream relief'
LIME = 'Wanping 42 | warm painted plaster'
GREEN = 'Wanping 42 | dark green entrance'
STONE = 'Wanping 42 | grey plinth'
SHADE = 'Wanping 42 | shaded reveals'
RED_DOOR = 'Wanping 42 | red service doors'
PALETTE = {key:finish(rgb,rough) for key,rgb,rough in [
    (RED,(143,71,55),.91),(YELLOW,(165,132,77),.93),(SOLDIER,(139,64,48),.89),
    (STEEL,(75,57,48),.70),(GLASS,(79,86,83),.31),(CREAM,(214,207,177),.88),
    (LIME,(201,199,182),.91),(GREEN,(38,57,47),.80),(STONE,(109,109,101),.86),
    (SHADE,(48,49,43),.94),(RED_DOOR,(121,50,39),.82)]}
