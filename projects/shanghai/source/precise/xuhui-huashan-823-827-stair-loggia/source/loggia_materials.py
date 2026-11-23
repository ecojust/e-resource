"""The three-gabled block's shaded stair hall and its construction details."""
from wing_finishes import PALETTE as WALLS,ROUGHCAST
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.append(str(PROJECT/'source/precise/xuhui-yanqing-159-garden-residence/source'))
from residence_materials import finish
LIME='Huashan 823 | sheltered warm cement'
CEMENT='Huashan 823 | weathered tread and landing'
BEAM='Huashan 823 | shaded stair soffit'
STEEL='Huashan 823 | dark green steel'
GREEN='Huashan 823 | dark painted landing door'
GLASS='Huashan 823 | muted window glass'
TILE='Huashan 823 | red brown gable capping'
SHADE='Huashan 823 | deepest visible recess'
PALETTE={**WALLS,LIME:finish((189,186,171),.90),CEMENT:finish((154,149,137),.89),
         BEAM:finish((125,126,117),.89),STEEL:finish((57,67,61),.63,.12),
         GREEN:finish((64,83,74),.77),GLASS:finish((69,85,86),.30,.13),
         TILE:finish((139,103,84),.90),SHADE:finish((52,54,49),.96)}
