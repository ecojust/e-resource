"""Facade of the shared lane entrance as photographed in 2015."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from gatehouse_upper_windows import openings
from material_names import MATERIAL

def finish(rgb,roughness,metallic=0.0):
    c=np.array(rgb,dtype=float)/255.
    linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    return dict(color=linear.tolist(),roughness=roughness,metallic=metallic)

STONE='Yongjia gatehouse | pale grey projecting bands'
EDGE='Yongjia gatehouse | weathered rendered arris'
IRON='Yongjia gatehouse | painted steel rack'
FLOOR='Yongjia gatehouse | dark underside of projecting tray'
SEAM='Yongjia gatehouse | recessed horizontal joints'
PALETTE={STONE:finish((153,151,143),.91),EDGE:finish((112,110,105),.94),
         IRON:finish((155,158,154),.66,.23),FLOOR:finish((91,91,83),.93),
         SEAM:finish((105,104,98),.94)}

def survey():
    path=Path(__file__).resolve().parents[1]/'measurements/measured-frontage-lines.json'
    return {k:v['median_m'] for k,v in json.loads(path.read_bytes())['observations'].items()}

def plate(b,area,y0,y1,mat,label):
    # Use depth toward the street so the local polygon axes form a right-handed frame.
    b.prism(area,-y1,-y0,lambda x,z,depth:(x,-depth,z),mat,label)

def block(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],mat,label=label)

def rail(b,pts,width,thick,mat,label):
    # Miter the horizontal short sides into the long front run; no rail crosses the two windows.
    from shapely.geometry import LineString
    shape=LineString([p[:2] for p in pts]).buffer(width/2,cap_style=2,join_style=2)
    z=pts[0][2]
    b.prism(shape,z-thick/2,z+thick/2,lambda x,y,h:(x,y,h),mat,label)

def rack(b,lod):
    # The photographed steel rack spans the space between the window frames.
    # Four white-painted folded rails and their short returns are separately editable.
    left,right=-.74,.27;outer=-.49
    for i,z in enumerate((4.976,5.112,5.251,5.395)):
        path=[(left+.038,-.012,z),(left,outer+.051,z),(left+.041,outer,z),
              (right-.052,outer,z),(right,outer+.061,z),(right-.030,-.012,z)]
        rail(b,path,.022,.037,IRON,f'Middle rack horizontal grille {i+1}')
    block(b,left-.022,right+.022,outer-.026,.015,4.853,4.936,FLOOR,'Middle rack folded lower tray')
    for i,x in enumerate((left+.037,.06,right-.044)):
        block(b,x-.012,x+.012,outer-.007,outer+.019,4.930,5.423,IRON,f'Middle rack vertical strap {i+1}')
    for i,x in enumerate([left+.1,right-.1]):
        b.tube([(x,-.016,4.566),(x,outer+.035,4.863)],.014,IRON,sides=7 if lod else 12,label=f'Middle rack lower bracket {i+1}')

def add_gatehouse_fabric(b,lod=False):
    v=survey();left=v['left_party_edge'];right=v['right_party_edge']
    top=v['medium_parapet_top'];zwest=v['west_raised_coping'];zeast=v['east_raised_coping']
    shoulder_l=-2.38;shoulder_r=1.68
    boundary=Polygon([(left,0),(right,0),(right,zeast),(shoulder_r,zeast),(shoulder_r,top),
                      (shoulder_l,top),(shoulder_l,zwest),(left,zwest)])
    width=3.463
    face=boundary.difference(box(-width/2,-.01,width/2,2.934))
    for row in openings():
        face=face.difference(box(row['left'],row['bottom'],row['right'],row['top']))
    # The bonded side strips have shallow shadow joints. The central surface
    # remains continuous between, above and underneath the two apertures.
    gaps=[]
    for i,z in enumerate([.90,1.80,2.69,3.65,4.33,5.02,5.76,6.48]):
        for tag,a,c in [('west',left,-1.87),('east',1.72,right)]:
            slit=box(a-.002,z-.010,c+.002,z+.010)
            if z>3.0:
                face=face.difference(slit)
                gaps.append((tag,a,c,z,i))
    plate(b,face,.0,.444,MATERIAL,'Grey gatehouse wall with independent upper openings and passage')
    for tag,a,c,z,i in gaps:
        block(b,a,c,.016,.041,z-.011,z+.011,SEAM,f'{tag} lime joint backing {i+1}')
    # Façade coping has a raised end on either side of the longer central run.
    for tag,a,c,z in [('West',left,shoulder_l,zwest),('Middle',shoulder_l,shoulder_r,top),('East',shoulder_r,right,zeast)]:
        block(b,a,c,-.069,.47,z-.055,z+.016,EDGE,tag+' stepped parapet coping')
    for tag,a,c,z,dz,front,mat in [
        ('Broad top cornice bed',left-.025,right+.025,v['cornice_lower'],.052,-.062,EDGE),
        ('Top cornice outer fillet',left-.046,right+.046,v['cornice_lower']+.046,.051,-.119,STONE),
        ('Top cornice weathering lip',left-.060,right+.060,v['cornice_upper']-.034,.042,-.154,STONE),
        ('Continuous raised apron below the two windows',-1.91,1.67,v['sill_course_bottom'],.086,-.104,EDGE),
        ('Raised sill course cap',-1.95,1.70,v['sill_course_top']-.042,.044,-.149,STONE),
        ('Lower recessed apron frame',-1.91,1.71,max(3.58,v['panel_band_foot']),.060,-.057,EDGE),
        ('Lower apron weathering ledge',-1.955,1.746,v['panel_band_top']-.041,.045,-.095,STONE)]:
        block(b,a,c,front,.013,z,z+dz,mat,tag)
    rack(b,lod)
