"""Package the observed bank of river windows, curved corners and open roof pavilion."""
from pathlib import Path
import argparse
import os
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from apartments import PALETTE,build_apartments
ID='hongkou-embankment-building-riverfront'
SCOPE='北苏州路河滨大楼临河长翼、两处圆弧翼端、中段圆角与开敞亭冠、两翼之间的入口庭院窗墙。沿岸曲折外轮廓和竖向褐砖窗带按修后实照制作。'
META=dict(id=ID,name='河滨大楼临苏州河立面',viewer_page='embankment-riverfront.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='photographed-river-elevation-and-entrance-court',source_register='source/precise/'+ID+'/reference-review.json',
          estimated='沿河轮廓按两个具名地图来源与两期航片配准。十层可见立面、逐层窗口及洗石子横带按照片估算，保留街背、内院以外与未逐层确认的加建。',interiors_modeled=False,
          coordinate_convention='Local X runs to the northeast along the river elevation, local Y runs inland toward the northwest, Z is up. glTF +Z faces the river.',
          copyright='Original architecture mesh and materials under MIT. Photographs are linked for architectural reference.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['EMBANKMENT_RIVERFRONT_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,build_apartments)
