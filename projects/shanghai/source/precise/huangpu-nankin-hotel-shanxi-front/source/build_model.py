"""Rebuild the west entrance and its photographed run of chevron balconies."""
import argparse
import json
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
import entrance
from hotel_stonework import (Frontage, PALETTE as WALL_PALETTE, STONE, TRIM,
                             PLINTH, SILL, REVEAL, SHOP_GLASS, sash, balcony)

ID='huangpu-nankin-hotel-shanxi-front'
SCOPE='山西南路现状入口及门上方相邻六开间，含两层钝角阳台、铁栏、门廊雨篷和门前邮筒。'
META={'id':ID,'name':'南京饭店山西南路入口与钝角阳台','viewer_page':'nankin-hotel-shanxi-front.html',
      'scope':SCOPE,'model_scope_zh':SCOPE,'status':'registered-west-entrance-and-original-balconies','reference_height_m':22.07,
      'source_register':'source/precise/'+ID+'/reference-review.json','coordinate_convention':'Metres. X along the west wall from its southern endpoint, Y towards South Shanxi Road, Z up.',
      'estimated':'入口沿街里程用四个2019年街景机位交会。高度、窗进深和铁栏小样按照片比例估计。',
      'interiors_modeled':'门扇与入口浅凹廊；营业空间未测。','copyright':'Original geometry. Street photographs remain at the reference sources.'}

def linear_component(value):
    srgb=value/255.
    return srgb/12.92 if srgb<=.04045 else ((srgb+.055)/1.055)**2.4

def entry_materials():
    materials={}
    for name,chip in entrance.MATERIALS.items():
        metal=any(k in name for k in ('bronze','burnished','canopy'))
        color=[linear_component(int(chip[i:i+2],16)) for i in (1,3,5)]
        materials[name]={'color':color,'roughness':.43 if metal or 'glass' in name else .66,'metallic':.34 if metal else 0.}
    return materials

PALETTE={**WALL_PALETTE,**entry_materials()}

def street_level(front, dims, detail):
    left,right=dims['extent']
    z0,z1=entrance.OPENING['z']
    x0,x1=entrance.OPENING['x']
    shops=dims['shop_openings']
    cuts=[(x0,z0,x1,z1),*shops]
    front.punched_wall('Street grey stone facing',(left,0,right,z1),cuts,-.52,0,PLINTH)
    for i,opening in enumerate(shops):
        sash(front,'Shop window '+str(i+1),opening,0,detail,SHOP_GLASS)
    # The rebuilt granite plaque wall shows slab joints passing behind its metal frame.
    for z in (1.12,2.16,3.23,4.29):
        for i,(a,b) in enumerate(dims['granite_piers']):
            front.box('Shop facing bed joints '+str(i+1),REVEAL,a,b,.001,.009,z,z+.018)
    for i,(a,b) in enumerate(dims['granite_piers']):
        front.box('Grey foot course '+str(i+1),PLINTH,a,b,-.01,.07,.015,.19)
    entrance.build(front,detail=detail)

def floor_band(front, name, start, end, face, z):
    front.box(name+' bed',SILL,start,end,face-.22,face+.09,z-.095,z+.06)
    front.box(name+' drip',TRIM,start,end,face-.16,face+.15,z-.037,z+.015)

def upper_level(front,dims,index,floor,detail):
    left,right=dims['extent']
    z0,z1=floor['height']
    face=floor['face_y']
    holes=[]
    for x in dims['bay_axes']:
        if 'balcony_depth' in floor:
            # Separate window heads and the low return of their common stone balcony.
            pair=dims['balcony_pair_width']
            gap=dims['balcony_window_pier']
            spans=[(x-pair/2,x-gap/2),(x+gap/2,x+pair/2)]
        else:
            spans=[(x-width/2,x+width/2) for x,width in
                    [(x-dims['plain_window_separation']/2,dims['plain_window_width']),
                     (x+dims['plain_window_separation']/2,dims['plain_window_width'])]]
        for a,b in spans:
            holes.append([a,floor['sill'],b,floor['head']])
    front.punched_wall('Level '+str(index)+' upper wall',(left,z0,right,z1),holes,face-.44,face)
    for i,hole in enumerate(holes):
        name='L'+str(index)+' window '+str(i+1)
        sash(front,name,hole,face,detail)
        if detail:
            a,z,b,_=hole
            front.box(name+' sill',SILL,a-.035,b+.035,face-.10,face+.065,z-.065,z)
    if 'balcony_depth' in floor:
        for i,x in enumerate(dims['bay_axes']):
            balcony(front,'L'+str(index)+' balcony '+str(i+1),x,dims['balcony_width'],floor['deck'],face,floor['balcony_depth'],dims['balcony_shoulder'],floor['masonry_top'],floor['iron_top'],detail)
    if floor.get('band'):
        floor_band(front,'Level '+str(index)+' string course',left,right,face,z1-.05)

def add_building(builder,lod):
    config=json.loads((SOURCE/'dimensions.json').read_bytes())
    left,right=config['extent']
    front=Frontage(builder)
    street_level(front,config,not lod)
    floor_band(front,'Shop cornice',left,right,0.,entrance.OPENING['z'][1])
    for index,level in enumerate(config['floors'],start=2):
        upper_level(front,config,index,level,not lod)
    previous=0
    for level in config['floors']:
        current=level['face_y']
        if current<previous:
            front.box('Setback terrace',SILL,left,right,current-.12,previous,level['height'][0]-.13,level['height'][0])
        previous=current
    for i,profile in enumerate(config['pilasters']):
        x,low,high,width,reach=profile
        front.box('Stepped pier '+str(i+1),TRIM,x-width/2,x+width/2,-.05,reach,low,high)
        front.box('Pier terminal '+str(i+1),SILL,x-width*.36,x+width*.36,-.035,reach+.055,low-.18,low+.20)

if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    selected,rest=options.parse_known_args()
    os.environ['NANKIN_HOTEL_BLENDER']=selected.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
