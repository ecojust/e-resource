"""Build the six-sided eastern brick tower and paired end windows of the Daxin Tobacco Company residence."""
from pathlib import Path
import json,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from brickwork import BRICK,END,TRIM,CLAY,CLOVE,PALE,FRAME,GLASS,DIM,CURTAIN,METAL,IRON,YARD,SHADE
from tower import tower
from east_wing import east_wing
from finishes import apply

ID='jingan-daxin-tobacco-northeast-tower'
META={'id':ID,'name':'观渡庐东北砖塔与短翼成对拱窗','viewer_page':'daxin-tobacco-northeast-tower.html',
      'scope':'北京西路1094弄2号大新烟草公司旧址，现存南立面的东北六边形砖塔、灰色围边和紧邻的东端双券窗墙。',
      'model_scope_zh':'取两组塔身窗、交替实窗与盲拱、灰色塔帽、檐托、短翼窗券、低女儿墙及可见的院侧设备。东侧大门、长立面其余开间、西端人字山墙、院墙与住宅内部另计。',
      'status':'photo-measured partial historic structure','source_reference_only':True}

def finish(rgb,rough=.88,metal=0):
    c=[v/255 for v in rgb];return {'color':[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c],'roughness':rough,'metallic':metal}

PALETTE={BRICK:finish((160,84,60)),END:finish((160,84,60)),TRIM:finish((143,82,62)),CLAY:finish((162,90,66)),CLOVE:finish((140,77,58)),PALE:finish((159,152,142)),
         FRAME:finish((52,48,42),.57),GLASS:finish((93,107,105),.28,.16),DIM:finish((109,119,111),.37,.13),CURTAIN:finish((125,125,115),.75),METAL:finish((137,138,123),.63,.28),IRON:finish((72,67,59),.65,.32),YARD:finish((132,127,113)),SHADE:finish((183,176,158),.76)}

def add_geometry(builder,lod):
    fit=json.loads((SOURCE.parent/'measurements/three-camera-fit.json').read_bytes());outline=tower(builder,fit,lod);east_wing(builder,outline,fit,lod);apply(builder)

if __name__=='__main__':
    import argparse,os
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--blender',default='blender');paths,remaining=parser.parse_known_args();os.environ['DAXIN_BLENDER']=paths.blender
    sys.argv=[sys.argv[0],*remaining,'--blender',str(SOURCE/'blender_preview.py')];build(SOURCE,META,PALETTE,add_geometry)
