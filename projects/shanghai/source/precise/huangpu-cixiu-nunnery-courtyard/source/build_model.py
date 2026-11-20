"""Package the retained main hall and its two courtyard galleries at Cixiu'an."""
from argparse import ArgumentParser
from pathlib import Path
import json, os,struct,sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from courtyard_geometry import CLEAR, PALETTE, make_courtyard

ID='huangpu-cixiu-nunnery-courtyard'
SCOPE='榛岭街15号正院北侧大雄宝殿、东西两厢面院木廊及院内铺地。可独立编辑的玻璃院顶表现2019年报道及照片所见状态。'
META=dict(id=ID,name='慈修庵正院北殿与两厢木廊',status='original-photo-informed-exterior',
    scope=SCOPE,model_scope_zh=SCOPE,viewer_page='cixiu-nunnery.html',
    estimated='大殿、廊柱、栏杆与院顶依据图像比例估算尺寸。屋面参考2022及2024年发布的航空影像，2026年发布的影像中院顶有变。庵外的方浜中路593号另院与街门独立保留。',
    coordinate_convention='Local glTF +X points east-northeast along the main hall front, +Y is up and +Z faces into the court, toward the south-southeast.',
    source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
    copyright='Original geometry MIT. Renamed four-character inscription uses an OFL 1.1 subset. Source photographs are linked for scholarly reference.')

def verify_glazing(path):
    with path.open('rb') as stream:
        header=stream.read(20)
        assert header[:4]==b'glTF'
        doc=json.loads(stream.read(struct.unpack_from('<I',header,12)[0]))
    material=next(v for v in doc['materials']if v['name']==CLEAR)
    assert material['alphaMode']=='BLEND' and abs(material['pbrMetallicRoughness']['baseColorFactor'][3]-.20)<1e-5
    return dict(alpha_mode=material['alphaMode'],opacity=material['pbrMetallicRoughness']['baseColorFactor'][3])

if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender');parser.add_argument('--out',type=Path,required=True);parser.add_argument('--audit',type=Path,required=True)
    opts,_=parser.parse_known_args()
    os.environ['CIXIU_NATIVE_BINARY']=opts.blender
    os.environ['CIXIU_GLAZING_AUDIT']=str((opts.audit/'native-glazing.json').resolve())
    # Use the common mesh/pack/verification path. Only the native-creation run requires
    # this building's independently editable translucent material and courtyard camera.
    if '--blender' in sys.argv:sys.argv[sys.argv.index('--blender')+1]=str(SOURCE/'blender_for_courtyard.py')
    else:sys.argv.extend(['--blender',str(SOURCE/'blender_for_courtyard.py')])
    build(SOURCE,META,PALETTE,make_courtyard)
    native=json.loads((opts.audit/'native-glazing.json').read_bytes())
    results={kind:verify_glazing(opts.out/f'{ID}-{kind}.glb')for kind in ('raw','web','lod')}
    assert all(abs(v['opacity']-native['reopened_principled_alpha'])<1e-5 for v in results.values())
    (opts.audit/'delivery-glazing.json').write_text(json.dumps(dict(native=native,glb=results,passed=True),indent=2)+'\n')
