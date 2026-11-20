"""Reconstruct the 1930s architectural elevation on Foochow Road, Shanghai."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from elevation import PALETTE,add_frontage

ID='huangpu-central-police-station'
SCOPE='福州路185号1930年代历史街面，两端各四列与中段六列窄窗、顶层横窗、双竖带半圆饰和阶梯形女儿墙。地面层取档案照片中的浅浮雕轮廓。'
META=dict(id=ID,name='总巡捕房旧址（福州路历史街面）',viewer_page='central-police-station.html',
          status='original-archival-photo-informed-elevation',scope=SCOPE,model_scope_zh=SCOPE,
          estimated='沿街地块边线约44.8米，模型面宽44.32米。高度以及阴影带的深度由1933—1939年档案照比例估算。',
          coordinate_convention='GLB +Z toward Fuzhou Road; +X along the street toward WSW; +Y up.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original geometry MIT. No photographs or image textures embedded.')

if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_frontage)
