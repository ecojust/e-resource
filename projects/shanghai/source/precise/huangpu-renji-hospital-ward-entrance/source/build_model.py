"""Build the documented entrance elevation of Renji Hospital West, building 2."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from courtyard import PALETTE, add_geometry

ID='huangpu-renji-hospital-ward-entrance'
SCOPE=('山东中路145号仁济医院西院2号住院楼院内入口立面。按2020、2024实照制作灰砖窗墙、'
       '上层栏廊、白色楼梯塔、拱形入口和圆形2号牌。两侧翼、完整屋面、3号和4号楼及室内另计。')
META={'id':ID,'name':'仁济医院西院2号住院楼（庭院入口立面）','viewer_page':'renji-ward-entrance.html',
      'status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,
      'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
      'coordinate_convention':'Metres. X west to east along the courtyard wall, Y into the ward block, Z up.',
      'copyright':'Original procedural architectural geometry and materials, MIT. No external photography is embedded.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_geometry)
