"""Build the east facade of the China Baptist Publication Building."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from east_front import PALETTE,add_frontage

ID='huangpu-china-baptist-publication-building'
SCOPE='圆明园路209号东立面，七组双列窗、两类凸砖壁柱、折面石柱头、中央四列小尖券、北端高起的女儿墙，以及带真光大樓四字的石质商铺基座。'
META=dict(id=ID,name='真光大楼（圆明园路东立面）',viewer_page='china-baptist-publication.html',
          status='original-architectural-elevation-and-photo-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,
          estimated='现行沿街边线约23.32米，修缮设计方带比例尺的立面图约22.8—23.5米，门窗、石饰与退进尺寸按两幅实照和图纸的比例估算。',
          coordinate_convention='GLB +Z faces Yuanmingyuan Road; +X north along the street; +Y up.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',copyright='Original geometry MIT. No photographs or drawing textures embedded.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_frontage)
