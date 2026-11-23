"""The two photographed angled metal ends and their different unfinished wall penetrations."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from street_portal import FRAME
from register_street import Camera
from photo_architecture import Facade

METAL='Xinlefang | weathered flue metal'
INSIDE='Xinlefang | dark wall cavity'
RIM='Xinlefang | dark metal fixture collars'
SILVER='Xinlefang | pale metal end faces'
FOAM='Xinlefang | ochre packing at rectangular service hole'
BED='Xinlefang | exposed grey bedding mortar'
RED='Xinlefang | exposed red masonry behind upper finish'
PALETTE={METAL:{'color':[.31,.301,.279],'metallic':.54,'roughness':.59},
         RIM:{'color':[.105,.090,.079],'roughness':.59,'metallic':.48},
         SILVER:{'color':[.64,.625,.594],'roughness':.25,'metallic':.59},
         INSIDE:{'color':[.049,.045,.043],'roughness':.86},FOAM:{'color':[.41,.204,.060],'roughness':.94},
         BED:{'color':[.31,.283,.255],'roughness':.95},RED:{'color':[.38,.204,.162],'roughness':.9}}
# Picks in a downsampled 1120 × 630 inspection view; transformed to full original pixels for projection.
PORTS={
 'upper roughcast':{'ring':[(532,101),(536,99),(539,98),(543,100),(548,97),(550,99),(551,108),(549,111),(545,111),(542,114),(537,114),(533,111),(531,107)],'back':(542,105),'mouth':(2550*1120/5312,463*630/2988),'radius':.081,'length':.215},
 'middle brickwork':{'ring':[(545,257),(557,256),(563,254),(566,255),(566,270),(562,272),(558,272),(555,275),(547,274),(546,271)],'back':(554,263),'mouth':(2607*1120/5312,1212*630/2988),'radius':.081,'length':.202},
}
def project(c,uv,depth):return c.wall((uv[0]*5312/1120,uv[1]*2988/630),depth)
def cutouts(cam):
    return {key:Polygon([project(cam,p,0)[[0,2]]for p in v['ring']]).buffer(0) for key,v in PORTS.items()}

def pipe(b,start,end,radius,sides,label):
    tangent=end-start;tangent/=np.linalg.norm(tangent)
    right=np.cross(tangent,[0.,0.,1.]);right/=np.linalg.norm(right)
    up=np.cross(tangent,right)
    plate=[]
    for centre,rad in [(start,radius),(end,radius),(start,radius-.008),(end,radius-.008)]:
        for angle in np.arange(sides)*2*np.pi/sides:
            plate.append(centre+rad*(np.cos(angle)*right+np.sin(angle)*up))
    faces=[]
    for i in range(sides):
        j=(i+1)%sides
        faces.extend([(i,j,j+sides,i+sides),(2*sides+j,2*sides+i,3*sides+i,3*sides+j),
                      (i+sides,j+sides,j+3*sides,i+3*sides),(j,i,i+2*sides,j+2*sides)])
    b.add(plate,faces,METAL,label+' / open annular tube')
    # Both mouths show a bright shallow dished end and a dark rim in the
    # original image. Their use is unknown. Model what the photograph resolves.
    for fraction,width,r in [(.16,.030,1.21),(.42,.018,1.12),(.76,.018,1.04)]:
        c=start+(end-start)*fraction
        b.tube([c,c+tangent*width],radius*r,RIM,sides,label+' / separate body collar')
    inset=end-.006*tangent
    angles=np.arange(sides)*2*np.pi/sides
    disc=[inset+(radius-.007)*(np.cos(a)*right+np.sin(a)*up)for a in angles]
    disc.extend([v-.015*tangent for v in disc.copy()])
    disc.extend([inset-.009*tangent,inset-.015*tangent])
    shell=[]
    for i in range(sides):
        j=(i+1)%sides
        shell.extend([(2*sides,i,j),(2*sides+1,j+sides,i+sides),(i,i+sides,j+sides,j)])
    b.add(disc,shell,SILVER,label+' / bright dished end')

def add_flues(b,lod=False):
    cam=Camera('2018');face=Facade(b,(-1,0),(1,0),'143-1 exposed penetrations')
    for key,hole in cutouts(cam).items():
        cfg=PORTS[key];l,lo,r,hi=hole.bounds
        face.prism(hole,-.148,-.133,INSIDE,key+' / shaded rear')
        face.prism(hole.buffer(.012,join_style=2).difference(hole.buffer(-.030)), -.038,.012,
                   BED if key.startswith('upper') else RED,key+' / chipped edges')
        if key.startswith('upper'):
            for j,(a,c)in enumerate([(l+.009,l+.111),(l+.124,l+.228),(l+.239,r-.008)]):
                if c>a:face.prism(hole.intersection(box(a,lo+.016,c,lo+(hi-lo)*(.51 if j!=2 else .70))),
                                   -.080,-.037,RED,key+' / exposed masonry')
        else:
            vertices=[(l+.032,lo+.020),(r-.015,lo+.018),(r-.009,lo+.11),((l+r)/2,lo+.155),(l+.045,lo+.082)]
            face.prism(hole.intersection(Polygon(vertices)),-.086,-.024,FOAM,key+' / ochre gap filling')
        start=project(cam,cfg['back'],.045);end=project(cam,cfg['mouth'],-cfg['length'])
        pipe(b,start,end,cfg['radius'],12 if lod else 24,key)
