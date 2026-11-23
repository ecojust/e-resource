"""Build the paired arched street entrance of Park Apartments at 455 Middle Fuxing Road."""
from pathlib import Path
import sys
import os
from argparse import ArgumentParser
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from arch_passage import PALETTE, add_building
ID='huangpu-park-apartments-twin-arched-passage'
NAME='派克公寓455弄双拱题名门廊'
SCOPE='复兴中路455号公寓面向马路的两个浅券拱、题名、檐上栏杆和两侧门槛。'
META={'id':ID,'name':NAME,'viewer_page':'park-apartments-twin-arched-passage.html','status':'photo-informed-park-apartments-arched-passage','model_scope_zh':SCOPE,'scope':SCOPE,'interiors_modeled':False,'source_register':'source/precise/'+ID+'/reference-review.json','estimated':'2015年署名北面照片与2019、2021街景结合测量。两个站的相机高度有约0.7米系统差，右门边部分被树遮挡，栏杆卷花和字面厚度近似。','coordinate_convention':'Metres, Z up. X follows the north street front to the west; Y increases from the projecting pier toward the court. Elevation is referenced to the threshold.','copyright':'Original architectural geometry and hand-drawn letters under MIT. Reference photographs are credited and not embedded.'}
if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['PARK_338_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
