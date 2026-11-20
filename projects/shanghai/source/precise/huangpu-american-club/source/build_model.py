"""Package the photographed Foochow Road frontage of the former American Club."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from elevation import PALETTE, add_geometry

ID = 'huangpu-american-club'
SCOPE = ('福州路209号美国花旗总会临街七开间立面，含四柱门廊、铁栏阳台、'
         '白石窗楣、顶层拱窗及两侧转角首跨。原生后段、背面、完整屋面与室内另计。')
META = {'id':ID, 'name':'美国花旗总会（福州路209号主立面）','viewer_page':'american-club.html',
        'status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,
        'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
        'coordinate_convention':'Metres, X from photographed left to right, Y into the building, Z up.',
        'copyright':'Original procedural architecture and materials, MIT. No external pixels or geometry.'}
if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_geometry)
