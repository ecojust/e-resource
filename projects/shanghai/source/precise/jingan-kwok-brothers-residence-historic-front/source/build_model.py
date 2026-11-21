"""Build the photographed bowed cornice and balustrade at 1400–1418 West Nanjing Road."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from bowed_gallery import PALETTE, make_gallery

ID='jingan-kwok-brothers-residence-historic-front'
SCOPE='南京西路1400—1418号郭氏兄弟住宅照片左侧住宅的弧形栏板、宝瓶栏杆、檐下齿饰、中央圆饰墩及照片可辨的一段柱头。'
META=dict(id=ID,name='郭氏兄弟住宅弧形檐廊',status='historical-photo-informed-architectural-detail',
          scope=SCOPE,model_scope_zh=SCOPE,viewer_page='kwok-brothers-residence-history.html',
          estimated='1926年为市级文物保护单位名单所载建造年；外观取自2014与2019年拍摄的两张照片。实际跨度、进深、转角、色彩和遮挡处的栏杆节距含估计。',
          coordinate_convention='Local ornament study, glTF +Y up and +Z toward the garden.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original MIT geometry. Documentary images are cited separately.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_gallery)
