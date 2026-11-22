"""Model the canted window tower on the Beijing Road street side of the Ji residence."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from street_tower import PALETTE,add_geometry
ID='jingan-ji-garden-residence-south-bay'
SCOPE='北京西路1510号纪氏花园住宅临街三面折角窗塔，含钢窗分格、花环浮雕、托块檐口、顶层浅拱窗与红瓦坡帽。'
META=dict(id=ID,name='纪氏花园住宅临街折角窗塔',viewer_page='ji-garden-residence-south-bay.html',
 scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed street window tower',source_register=f'source/precise/{ID}/reference-review.json',
 estimated='南端三个折面按原城平面配准。楼层、收边、凸出线脚、瓦帽标高按影像比例估算；花叶纹内部的叶数与截面近似。',
 interiors_modeled=False,coordinate_convention='Metres, Z up. Positive X follows the central street-facing facet towards northeast, positive Y points into the residence.',
 copyright='Original geometry under MIT. Photographs are separately attributed and were used as visual references.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    parser.add_argument('--audit',type=Path,required=True)
    options,remaining=parser.parse_known_args()
    os.environ['JI_TOWER_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--audit',str(options.audit),'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)
    import json
    record=options.audit/'geometry-native.json'
    proof=json.loads(record.read_bytes())
    assert proof['native_reopened_and_compared']['tower_reopened']['active_camera']=='Ji residence Street corner'
    proof['render']='Cycles, 14 samples, from reopened blend. OIDN RT sRGB postfilter.'
    record.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
