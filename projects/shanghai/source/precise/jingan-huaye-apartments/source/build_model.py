"""Package the independently identified main apartment house of the Huaye compound."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from huaye_geometry import PALETTE,add_apartments

ID='jingan-huaye-apartments'
SCOPE='华业公寓H形主楼及中央红瓦塔。以2019年俯拍和2015年地面照片估计窗墙、阳台和退台，四层配楼、连廊及室内另计。'
META={'id':ID,'name':'华业公寓主楼（H形住宅与中央红瓦塔）','status':'original-photo-informed-exterior',
      'viewer_page':'huaye-apartments.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,
      'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
      'coordinate_convention':'Local X is camera right along the southwest elevation (southeast, bearing 146 degrees). Local Y points inward, bearing 56 degrees. GLB Y is up and Z is outward.',
      'copyright':'Original geometry and procedural materials MIT. No photographic pixels embedded.'}

if __name__=='__main__':build(SOURCE,META,PALETTE,add_apartments)
