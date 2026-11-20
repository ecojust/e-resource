"""Build Science Hall No. 1 garden galleries and southern roof planes."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from garden import PALETTE, add_garden

ID='huangpu-science-hall-building-one'
SCOPE='南昌路47号上海科学会堂一号楼面向花园的南立面，包括五处突出的亭顶、四段三开间窗廊、中央时钟山花、露台、花园台阶及可见南半坡红瓦屋顶。'
META=dict(id=ID,name='上海科学会堂一号楼（南花园五亭立面）',viewer_page='science-hall-one.html',scope=SCOPE,model_scope_zh=SCOPE,
    status='historic-garden-elevation-with-aerial-and-restoration-references',estimated='两层原法国总会及法国学堂南面，屋脊、窗廊与门廊按1927、2014照片及三期航片估计。',
    coordinate_convention='GLB +Z faces south-southeast into the garden; +X northeast along the facade; +Y up.',
    interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',copyright='Original mesh MIT. All reference photographs retain their own rights.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_garden)
