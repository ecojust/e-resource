"""Build the garden-front elevation of the lost residence listed at 80 North Shaanxi Road."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from twin_towers import PALETTE,facade
ID='jingan-chen-bingqian-historic-residence'
SCOPE='依据标明原托益住宅的早期正面照片，表现两端折坡角塔、上下两层各八跨的券廊，以及花木上方可辨的中央低矮轮廓。下部花园、完整门厅、室内和背立面待考。'
META={'id':ID,'name':'陈炳谦宅（原托益住宅）双塔与券廊历史正立面','viewer_page':'chen-bingqian-historic-residence.html','scope':SCOPE,'model_scope_zh':SCOPE,
      'reference_height_m':20.15,'estimated':'市房管局注约1994年灭失。地方文史作者记约1900年建；原照片拍摄年未详。模型宽高、色彩与截断进深按照片估算。',
      'status':'historical-photo-informed-facade-study','source_register':'source/precise/'+ID+'/reference-review.json','coordinate_convention':'Local X runs across the photographed elevation, Z is vertical; the end towers and the garden-facing arcade project toward negative Y.',
      'interiors_modeled':False,'copyright':'Original geometric interpretation of the photographed envelope. No third-party pixels or geometry are embedded.'}
if __name__=='__main__':build(HERE,META,PALETTE,facade)
