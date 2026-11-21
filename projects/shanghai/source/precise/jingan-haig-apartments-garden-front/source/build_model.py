"""Build the garden-facing elevation of the restored Haig Court in Shanghai."""
from pathlib import Path
import argparse
import os
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from garden_front import PALETTE,build_garden_front
ID='jingan-haig-apartments-garden-front'
SCOPE='以2025年修缮后实照为准的海格公寓南面，包括四列七层弧顶阳台、双浅山墙、两端三跨石柱敞廊及中央题名拱门。'
META=dict(id=ID,name='海格公寓主楼南向花园立面',viewer_page='haig-apartments-garden.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='restored-garden-front-june-2025',source_register='source/precise/'+ID+'/reference-review.json',
          estimated='52.84米南墙依底图1554。修缮资料公布38米高，楼层分带、洞口与栏杆尺寸依照片估计；北翼、室内及花园另计。',interiors_modeled=False,
          coordinate_convention='Author X east along the main south wall; Y into the building; Z up. glTF +Z faces the entrance court.',
          copyright='Original geometry and materials under MIT. Reference photographs linked separately.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['HAIG_COURT_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,build_garden_front)
