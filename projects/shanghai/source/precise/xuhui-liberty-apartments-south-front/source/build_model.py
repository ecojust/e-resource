"""Rebuild the registered and photographed south elevation of Liberty Apartments."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from south_front import PALETTE,make_front
ID='xuhui-liberty-apartments-south-front'
SCOPE='五原路258号自由公寓南向四开间，中央九层三道白色竖肋、折角窗和两翼较低的退台。'
META=dict(id=ID,name='自由公寓南面退台、中央三肋与转角窗',status='original-photo-informed-exterior',
    scope=SCOPE,model_scope_zh=SCOPE,viewer_page='liberty-apartments.html',
    estimated='徐汇区文化局记1933年，杨浦图书馆记1937年。2013年摄影与2020、2021年路口影像可核南面上部外形。下层细部分布、窗扇、层高及浅切面进深为近似，院门、树木、北部和室内待考。',coordinate_convention='X runs east-northeast along the main front, Y inward toward the north-northwest. glTF +Y is up.',source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,copyright='Original MIT geometry. Reference photographs are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_front)
