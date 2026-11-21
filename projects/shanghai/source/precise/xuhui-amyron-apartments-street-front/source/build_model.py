"""Rebuild the registered and photographed corner of the Amyron Apartments."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from street_front import PALETTE,make_front
ID='xuhui-amyron-apartments-street-front'
SCOPE='高安路14号高安公寓的六层转角弧窗、两翼较低的街面及圆端挑阳台、中央通高门廊。'
META=dict(id=ID,name='高安公寓转角弧窗与通高门廊',status='original-photo-informed-exterior',
    scope=SCOPE,model_scope_zh=SCOPE,viewer_page='amyron-apartments.html',
    estimated='中央六层和两侧五层、门廊与平面折转依天平街道2008年两张照片、2013年署名近景和路口两站视线复原。窗分格、层高和浅切段进深含估计，室内未建。',
    coordinate_convention='X runs toward the north end of the street front. Y points inward. The upper corner faces approximately east and glTF +Y is up.',
    source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
    copyright='Original MIT model. Reference photographs are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_front)
