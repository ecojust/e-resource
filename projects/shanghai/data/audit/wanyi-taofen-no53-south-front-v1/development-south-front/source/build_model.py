"""Build the 2026 Wanyi Fang no.53 public museum frontage."""
from pathlib import Path
import sys
source=Path(__file__).resolve().parent
tools=next(parent/'tools' for parent in source.parents if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from museum_front import PALETTE,add_building

ID='huangpu-wanyi-taofen-museum-no53-south-front'
scope='2026年7月公布的万宜坊53号南院门、横向金色馆名、三段上亮、二层绿窗、局部坡瓦及共享老虎窗的西半。'
META=dict(id=ID,name='万宜坊韬奋纪念馆53号院门与南立面',viewer_page='wanyi-taofen-no53-south-front.html',
          status='photo-informed-exterior-study',scope=scope,model_scope_zh=scope,reference_height_m=9.19,
          estimated='院墙及窗跨比例取2026年7月报道正面照片。立面进深、高度、坡瓦和开启角度按图像估算。字形以OFL字库表现可辨馆名。',source_register='source/precise/'+ID+'/reference-review.json',
          coordinate_convention='Metres; centre of no.53 main south wall; positive X east along the row, positive Y into the house.',
          interiors_modeled=False,copyright='Original geometry. No photographs or photographic textures. Included subset of Noto Serif CJK SC uses SIL OFL 1.1.')
if __name__=='__main__':
    import package_architectural_model
    package_architectural_model.PREVIOUS=source/'native'
    build(source,META,PALETTE,add_building)
