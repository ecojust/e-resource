"""Build the historic Basset garden elevation as a standalone photo-informed model."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from garden_front import PALETTE, make_front

ID='xuhui-huaihai-1431-historic-garden-front'
SCOPE='档案照片中的巴塞住宅花园面，两座瓦顶前翼、中央四柱弧廊与石栏、两端低矮附房的可见部分。'
META=dict(id=ID,name='淮海中路1431号巴塞住宅历史花园立面',scope=SCOPE,model_scope_zh=SCOPE,
          status='historical-photo-informed-facade-study',viewer_page='huaihai-1431-history.html',
          estimated='间距、高度、颜色与廊深按旧照比例估计，局部坐标仅供独立展件。',
          coordinate_convention='Local elevation study. glTF +Y is up. The garden face looks towards glTF +Z.',
          source_register=f'source/precise/{ID}/reference-review.json',
          interiors_modeled=False,copyright='Original MIT geometry. Archival photographs retain their respective rights.')

if __name__=='__main__':
    build(SOURCE,META,PALETTE,make_front)
