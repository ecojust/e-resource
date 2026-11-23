"""Build the east entrance span of Joffre Terrace in Shanghai."""
from pathlib import Path
import sys
import os
from argparse import ArgumentParser
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from east_passage import PALETTE, add_building
ID='huangpu-joffre-terrace-east-passage'
NAME='淮海坊茂名南路总弄题名过街楼'
SCOPE='市表淮海中路927弄，展示茂名南路100号总弄东口的扁梁、三字题名及跨在弄道上的两层四窗。'
META={
    'id':ID,'name':NAME,'viewer_page':'joffre-terrace-east-passage.html','status':'photo-informed-joffre-terrace-east-passage',
    'ground_collision_mode':'overhead-connector','model_scope_zh':SCOPE,'scope':SCOPE,'estimated':'2015年原照与2020年四个实景站对照。窗框和装饰剖面为照片估算，开间之外的两排住宅没有纳入本片。',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'coordinate_convention':'Metres, Z up. Positive X runs north along Maoming South Road. Positive Y faces into the lane to the west. Heights refer to the street pavement.',
    'copyright':'Original authored architectural geometry and drawn lettering: MIT. No documentary imagery is embedded.'
}
if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    parser.add_argument('--gltfpack',default='gltfpack')
    options,rest=parser.parse_known_args()
    os.environ['JOFFRE_GLTFPACK']=options.gltfpack
    os.environ['JOFFRE_330_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--gltfpack',str(SOURCE/'pack_overhead.py'),'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
