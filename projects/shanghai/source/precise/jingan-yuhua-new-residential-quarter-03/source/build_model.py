"""Author No. 3's pictured entrance and adjacent elevation in Shanghai's Yuhua estate."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from elevation import PALETTE, add_geometry

ID='jingan-yuhua-new-residential-quarter-03'
SCOPE='富民路182弄裕华新村3号临弄院门和2014年照片所见的楼面，包括两层砖带窗、凸出砖砌竖片、退台横窗、半圆顶窗及浅檐。另一住宅单元、完整屋顶、隐蔽面及室内另计。'
META={'id':ID,'name':'裕华新村3号（临弄院门与可见楼面）','viewer_page':'yuhua-residence-03.html',
      'status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,
      'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
      'coordinate_convention':'Metres. X goes from photographed left to right, Y increases into the visible residence, Z up. GLB axis order is X,Z,-Y.',
      'copyright':'Original procedural architectural geometry and materials, MIT. External photographs used as references only.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_geometry)
