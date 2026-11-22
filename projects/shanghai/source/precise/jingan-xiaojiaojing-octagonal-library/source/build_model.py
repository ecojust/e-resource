"""Export the two-storey octagonal library with independent courtyard and roof cameras."""
from pathlib import Path
import argparse,os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from pavilion import PALETTE, add_geometry
ID='jingan-xiaojiaojing-octagonal-library'
SCOPE='院南两层八角藏书阁，绿琉璃八脊攒尖顶、下层挑檐和斗拱、朝院门窗及如意形窗饰。'
META=dict(id=ID,name='小校经阁八角藏书楼',viewer_page='xiaojiaojing-octagonal-library.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='photo-informed courtyard library',source_register=f'source/precise/{ID}/reference-review.json',
          estimated='八个檐角按航片拟合，二层墙间宽按公布建筑面积估算。立面高度、门轴、各面窗格和瓦当、斗拱局部按照片投影近似。',
          interiors_modeled=False,coordinate_convention='Metric Z up. The level courtyard entrance lies on the negative-Y face.',
          copyright='Original geometry under MIT. Photographs are credited to the cited sources and are excluded from the model.')
if __name__=='__main__':
    args=argparse.ArgumentParser(add_help=False)
    args.add_argument('--blender',default='blender');args.add_argument('--audit',type=Path,required=True);options,remaining=args.parse_known_args()
    os.environ['LIBRARY_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--audit',str(options.audit),'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)

    import json
    evidence=options.audit/'geometry-native.json'
    result=json.loads(evidence.read_bytes())
    assert result['native_reopened_and_compared']['library_reopened']['active_camera']=='Library Courtyard doorway'
    result['render']='Cycles 14 samples, editable file reopened, OIDN denoised.'
    evidence.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
