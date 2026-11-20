"""Build the 1923 Shanghai Cotton Exchange and the former natural history museum entrance."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from exchange_geometry import PALETTE,make_exchange

ID='huangpu-cotton-exchange-building'
SCOPE='延安东路260号华商纱布交易所的南侧街面、西南转角穹顶塔和原上海自然博物馆铁门。后翼及两处屋面间的低部按三期航片概化。高架桥和西邻延河大楼另计。'
META=dict(id=ID,name='华商纱布交易所（上海自然博物馆旧馆）',status='original-photo-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,
          viewer_page='cotton-exchange.html',estimated='柱距、退深、穹顶和屋面标高按历史街照及原馆照片估计，展厅内部未复原。',
          coordinate_convention='Local GLB +X follows East Yanan Road toward the northeast, +Y is up, +Z faces the southern street.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original architectural geometry MIT. Renamed lettering subset SIL OFL 1.1. Historical and modern photographs are referenced separately.')
if __name__=='__main__':
    from final_preview import finish
    build(SOURCE,META,PALETTE,make_exchange)
    finish()
