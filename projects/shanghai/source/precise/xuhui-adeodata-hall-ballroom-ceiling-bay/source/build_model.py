"""Rebuild the near and distant meshes of one historical ceiling bay."""
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from ceiling import PALETTE,build_ceiling
ID='xuhui-adeodata-hall-ballroom-ceiling-bay'
SCOPE='一枚亮色圆顶饰及其阶状外圈、一跨的横向线脚、两侧凹弧天棚与起拱檐线。'
META=dict(id=ID,name='天赐大宅舞厅圆形顶饰与弧肋',viewer_page='adeodata-ballroom-ceiling-bay.html',scope=SCOPE,model_scope_zh=SCOPE,source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=True,status='detached historical interior fragment',estimated='按原黑白内景中的轮廓重建，圆饰直径取2.60米作展示标尺，未见尺寸图，灰度材质代表照片明暗。',coordinate_convention='Object-local display metres. X crosses the bay, Y follows the ceiling ribs, Z is upward. Camera looks up from the historical interior side.',copyright='Original reconstruction. Historical photographs are separately credited documentary references.')
if __name__=='__main__':
    wrapper=SOURCE/'native_blender.py'
    if '--blender' in sys.argv:
        j=sys.argv.index('--blender')+1
        os.environ['ADEODATA_BLENDER']=sys.argv[j]
        sys.argv[j]=str(wrapper)
    else:
        sys.argv.extend(['--blender',str(wrapper)])
    build(SOURCE,META,PALETTE,build_ceiling)
