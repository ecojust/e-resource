"""Build the garden corner of Rong Zhai, 186 North Shaanxi Road, Shanghai."""
import json
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from garden_tower import tower,WALL,TRIM,ACCENT,FRAME,GLASS,SHADOW,IRON,FLOOR,ROOF,RIB,OCHRE
from copper_roof import dome
from colonnade import veranda
from garden_plaster import apply as apply_plaster

ID='jingan-rong-residence-garden-tower'
META={'id':ID,'name':'荣氏花园住宅花园角塔与首间柱廊',
      'viewer_page':'rong-residence-garden-tower.html',
      'scope':'陕西北路186号朝花园的多面角塔及紧邻的首间双层柱廊。含三个开窗折面、深窗、花环、圆顶和尖饰、独立柱与屋面栏杆。',
      'model_scope_zh':'按2017年修缮后花园照片制作，用2015年街面照片对照折角、花饰和圆顶。相邻柱廊各间、其余主屋、院墙及室内另计。',
      'status':'photo-measured partial historic structure','source_reference_only':True}


def finish(rgb,rough=.9,metal=0):
    unit=[v/255 for v in rgb]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in unit]
    return {'color':linear,'roughness':rough,'metallic':metal}


PALETTE={WALL:finish((220,215,193)),TRIM:finish((231,225,204)),ACCENT:finish((193,183,157)),
         FRAME:finish((57,55,48),.59,.16),GLASS:finish((105,121,117),.29,.19),
         SHADOW:finish((181,174,149)),IRON:finish((65,65,57),.64,.36),
         FLOOR:finish((176,168,147)),ROOF:finish((140,89,72),.74,.34),
         RIB:finish((113,76,61),.73,.56),OCHRE:finish((87,58,48),.63,.52)}


def add_geometry(builder,lod):
    dimensions=json.loads((SOURCE.parent/'measurements/two-photo-fit.json').read_bytes())
    east,side,_=tower(builder,dimensions,lod)
    veranda(builder,dimensions,east,side,lod)
    dome(builder,dimensions,lod)
    apply_plaster(builder,dimensions)


if __name__=='__main__':
    import argparse
    import os
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    paths,remaining=parser.parse_known_args()
    os.environ['RONG_GARDEN_BLENDER']=paths.blender
    sys.argv=[sys.argv[0],*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)
