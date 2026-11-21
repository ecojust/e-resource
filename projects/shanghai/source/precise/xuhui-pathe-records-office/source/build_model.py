"""Rebuild the former Pathe record-company offices at 811 Hengshan Road."""
import argparse
import json
import os
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box

SOURCE=Path(__file__).resolve().parent
PROJECT=next(folder for folder in SOURCE.parents if (folder/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as package
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade
from brickwork import BRICK,texture_coordinates
from north_elevation import build_north
from roofscape import build_roofs

ID='xuhui-pathe-records-office'
META=dict(id=ID,name='东方百代唱片公司办公楼（百代小楼）',viewer_page='pathe-records-office.html',
          heritage_group='4D031',heritage_address='衡山路811号',status='four-photographed-exteriors',
          scope='北阶梯高窗与扇贝雨篷、南柱廊与双层券窗、东西两侧、低翼及坡瓦屋顶。')
D=json.loads((SOURCE.parent/'measurements/building-dimensions.json').read_bytes())['model_parameters_m']

def material(rgb,roughness=.83,metallic=0.):
    def linear(v):
        s=v/255
        return s/12.92 if s<.04045 else ((s+.055)/1.055)**2.4
    return {'color':[linear(v)for v in rgb],'roughness':roughness,'metallic':metallic}

PALETTE={
 BRICK:dict(color=[1.,1.,1.],roughness=.94,texture=str(SOURCE/'pathe-red-brick.png')),
 'Warm dressed stone':material((207,197,178)),
 'Warm white enamel':material((225,215,193)),
 'Dark window frames':material((52,54,51),.43,.19),
 'Daylit glazing':material((116,131,134),.29,.23),
 'Inner opening':material((43,43,39)),
 'Entrance glazing':material((55,57,53),.26,.13),
 'Old roof clay':material((154,88,61)),
 'Weathered tile troughs':material((128,79,64)),
 'Dark eaves timber':material((78,58,53)),
 'Forged metal':material((58,57,54),.48,.28),
 'Panelled entrance doors':material((87,65,48)),
 'Stair flight behind the light':material((72,74,72),.64),
 'Bronze details':material((130,101,64),.60,.35),
 'Lantern glass':material((155,160,145),.4,.18),
 'Green enamel plaque':material((44,99,72),.48),
 'Stone joints':material((156,147,132)), 
}


def eaves_and_stones(b,dimensions,lod):
    half=dimensions['width']/2;depth=dimensions['wall_depth'];z=dimensions['wall_eave']
    # Side walls meet on the building corners. Separate strips wrap the quoins onto both faces.
    faces=[
        (Facade(b,(-half,0),(half,0),'North eaves'),[-half,half],True),
        (Facade(b,(half,0),(half,depth),'West eaves'),[-depth/2,depth/2],False),
        (Facade(b,(-half,depth),(-half,0),'East eaves'),[-depth/2,depth/2],False)]
    for face,(lo,hi),front in faces:
        fields=[(lo,hi)] if not front else [(lo,dimensions['north_tower_center']-dimensions['north_tower_width']/2),
                                            (dimensions['north_tower_center']+dimensions['north_tower_width']/2,hi)]
        for a,c in fields:
            width=c-a;mid=(a+c)/2
            for dz,h,d,color in ((-.080,.16,.25,'Warm dressed stone'),(.001,.09,.56,'Dark eaves timber')):
                face.box(mid,z+dz,width,h,d,d/2-.055,color,'Mouldings below tile ends')
            count=max(2,round(width/1.14))
            for u in np.linspace(a+.26,c-.26,count):
                start=face.point(u,z-.59,.022);end=face.point(u,z-.012,.45)
                vector=end-start;length=float(np.linalg.norm(vector));tangent=vector/length;side=face.t
                normal=np.cross(tangent,side)
                b.box((start+end)/2,(.12,.14,length),'Dark eaves timber',[side,normal,tangent],'Deep eaves • angled timber brackets')
                face.box(u,z-.58,.155,.14,.17,.048,'Warm dressed stone','Deep eaves • pale corbel shoes')
        for sign in (-1,1):
            for i in range(19):
                # The corner keys pass the timber fascia and the plinth between the two storeys.
                ht=.335;u=lo if sign<0 else hi
                width=.275 if i%2 else .415
                face.box(u-sign*width/2,.67+i*.335,width,ht-.012,.052,.012,'Warm dressed stone','Alternating corner keys')
    wing=dimensions['garden_east_width']
    for x0,x1,y in ((half,-half+wing,depth),(-half+wing,-half,depth+dimensions['garden_wing_projection'])):
        face=Facade(b,(x0,y),(x1,y),'Southern eaves')
        face.box(0,z-.085,face.length,.16,.25,.073,'Warm dressed stone','Ashlar fascia')
        face.box(0,z+.001,face.length,.085,.48,.178,'Dark eaves timber','Timber fascia')
        for u in np.linspace(-face.length/2+.28,face.length/2-.28,max(3,round(face.length/1.16))):
            start=face.point(u,z-.48,.018);end=face.point(u,z-.042,.424)
            span=end-start;length=np.linalg.norm(span);axis=span/length
            b.box((start+end)/2,(.12,.126,length),'Dark eaves timber',[face.t,np.cross(axis,face.t),axis],
                  'Garden roof • sloped brackets')
            face.box(u,z-.49,.152,.136,.142,.048,'Warm dressed stone','Corbel foot')
    b.box((0,depth/2,.015),(2*half,depth,.030),'Warm dressed stone',label='Ground floor • underside')
    # Shallow, closed backing planes give every real opening a shadowed reveal.
    b.box((0,depth/2,.17),(2*half-.20,depth-.22,.11),'Inner opening',label='Ground floor • interior slab')
    b.box((0,depth/2,3.99),(2*half-.28,depth-.32,.14),'Inner opening',label='Upper floor • interior slab')


def add_building(builder,lod):
    from garden_elevation import build_garden_face
    from side_elevations import build_sides
    width=D['width'];depth=D['wall_depth']
    build_north(builder,D,lod)
    south=Facade(builder,(width/2,depth),(-width/2,depth),'Garden')
    build_garden_face(builder,south,D,lod)
    build_sides(builder,D,lod)
    eaves_and_stones(builder,D,lod)
    build_roofs(builder,D,lod)
    texture_coordinates(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--blender',default='blender')
    options,args=parser.parse_known_args();os.environ['PATHE_OFFICE_BLENDER']=options.blender
    sys.argv[1:]=[*args,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
