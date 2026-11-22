"""Build the east garden end of the Soong residence on North Shaanxi Road."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from east_gable import PALETTE,add_geometry
ID='jingan-soong-family-residence-east-gable'
SCOPE='陕西北路369号南侧主楼的东山墙、上层敞廊、两根门廊柱与南园折角百叶窗、坡顶和老虎窗。'
META=dict(id=ID,name='宋氏花园住宅主楼东山墙与南园折角窗',viewer_page='soong-family-east-gable.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='photo-informed east gable and garden bay',source_register='source/precise/'+ID+'/reference-review.json',
          estimated='进深、标高和木作尺寸为航片及实体照片比例估计，照片未详的主楼西部保留原城。',
          interiors_modeled=False,coordinate_convention='Metres, Z up. Positive X along the east gable towards north-west, positive Y into the building towards south-west. glTF positive Z faces the street.',
          copyright='Original geometry and code under MIT. Reference images are separately credited and are not embedded.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    parser.add_argument('--audit',type=Path,required=True)
    options,remaining=parser.parse_known_args()
    os.environ['SOONG_GABLE_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--audit',str(options.audit),'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)
    import json
    record=options.audit/'geometry-native.json'
    proof=json.loads(record.read_bytes())
    assert proof['native_reopened_and_compared']['garden_reopened']['active_camera']=='Soong residence Garden corner'
    proof['render']='Cycles, 14 samples, from reopened blend. OIDN RT sRGB postfilter.'
    record.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
