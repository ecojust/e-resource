"""Build the independently identified Jianye Li central lane gate."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from gate import PALETTE,add_gate

ID='xuhui-jianye-li-main-lane-gate'
SCOPE='建国西路建业里总弄门楼的两侧石柱、平券退进门洞、两樘木窗、回纹额枋、阶梯式女儿墙、五字凸额与2020年实见的小铜牌。'
META=dict(id=ID,name='建业里总弄沿街门楼',viewer_page='jianye-li-main-gate.html',
          scope=SCOPE,model_scope_zh=SCOPE,status='documented-post-renovation-street-gate',
          estimated='三处2020年街面相机用于交会估算门宽，其他尺寸参考2014年照片投影和2020年门面细节。石材、字体、深度与颜色均为近似值。',
          coordinate_convention='GLB +Z faces Jianguo West Road, +X runs east along the street and +Y is up.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original mesh MIT. Reference photos retain their source rights. Sign font subset SIL OFL 1.1.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_gate)
