"""Face brick, segmental heads, pilasters and the two warm bands on the former canteen."""
import json
from pathlib import Path
from math import asin, sin, cos
import numpy as np
from shapely import set_precision
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from hall_coordinates import point, LENGTH, WIDTH
from hall_windows import segment_profile, add_window
from material_names import PLASTER, RED, TEXTURES

LAYOUT = json.loads((Path(__file__).parent/'hall-layout.json').read_text())
BASE = 'Yimin canteen | grey foundation stone'
RIM = 'Yimin canteen | dark slate sill'
SLATE = 'Yimin canteen | dark brick key'
PIPE = 'Yimin canteen | painted iron rainwater pipe'
SOFFIT = 'Yimin canteen | pale grey eave underside'
TRIM = 'Yimin canteen | graphite fascia'
GABLE = 'Yimin canteen | pale render in the roof gable'
RISE = 'Yimin canteen | warm bed in lower arches'
GREYS = ['Yimin canteen | grey arch brick '+str(i+1) for i in range(4)]
REDS = ['Yimin canteen | red arch brick '+str(i+1) for i in range(4)]

def finish(rgb, rough=.85, metal=0):
    a=np.array(rgb)/255
    return dict(color=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)

PALETTE={name:dict(texture=str(file),color=[1,1,1],roughness=.92,metallic=0.) for name,file in TEXTURES.items()}
for name,rgb in [(BASE,[155,153,152]),(RIM,[83,80,79]),(SLATE,[77,71,67]),(SOFFIT,[170,168,166]),(TRIM,[94,94,99]),(GABLE,[217,211,205]),(RISE,[150,106,85])]:
    PALETTE[name]=finish(rgb)
PALETTE[PIPE]=finish([72,73,72],.65,.2)
for name,rgb in zip(GREYS+REDS,[(100,100,98),(89,88,87),(108,106,104),(98,96,95),(159,104,82),(153,98,79),(166,111,88),(148,98,81)]):
    PALETTE[name]=finish(rgb)

def section(b,face,shape,d0,d1,mat,label):
    if shape.is_empty:return
    shape=set_precision(shape,1e-7).simplify(2e-7,preserve_topology=True)
    if shape.geom_type=='Polygon':
        if shape.area>1.e-7:
            b.prism(shape,-d1,-d0,lambda u,z,d:point(face,u,-d,z),mat,label)
    elif hasattr(shape,'geoms'):
        for poly in shape.geoms:section(b,face,poly,d0,d1,mat,label)

def profile(o,segments):
    return segment_profile(o['center'],o['width'],o['sill'],o['spring'],o['crown'],segments)

def add_arch(b,face,o,tag,lod):
    """Radial brick joints follow the same circular segment as the outer jamb."""
    c=o['center'];half=o['width']/2;rise=o['crown']-o['spring']
    radius=(half*half+rise*rise)/(2*rise);angle=asin(half/radius);cy=o['crown']-radius
    ground=o['level']=='ground';door=o['kind']=='double-door'
    thickness=.235 if door else (.178 if ground else .152)
    def arc(t,a):return [c+(radius+a)*sin(t),cy+(radius+a)*cos(t)]
    def slice_(a,b,d0,d1,n):
        v=np.linspace(a,b,n)
        return Polygon([arc(t,d0)for t in v]+[arc(t,d1)for t in v[::-1]])
    section(b,face,slice_(-angle,angle,0,thickness,29 if not lod else 13),-.012,.045,RISE if ground else PLASTER,tag+' arch bed')
    n=(21 if door else 15) if not lod else (13 if door else 9)
    bounds=np.linspace(-angle,angle,n+1)
    for i,(a,z)in enumerate(zip(bounds,bounds[1:])):
        gap=(z-a)*.035
        shape=slice_(a+gap,z-gap,.002,thickness-.004,3)
        section(b,face,shape,-.023,-.009,(REDS if ground else GREYS)[i%4],tag+' radial brick heads')

def pier_axes(face,rows):
    width=LENGTH if face in ('canal','street')else WIDTH
    upper=sorted([r['center'] for r in rows if r['level']=='upper'])
    if len(upper)<2:return []
    return [(.19,.38),*[(float((l+r)/2),.56 if width==WIDTH else .50)for l,r in zip(upper,upper[1:])],(width-.19,.38)]

def add_facade(b,face,rows,lod=False):
    width=LENGTH if face in ('canal','street')else WIDTH
    wall_top=LAYOUT['eave'];band=LAYOUT['band_top'];tag=face.title()
    openings=[profile(o,12 if lod else 28)for o in rows]
    cuts=unary_union(openings)
    def overlay(z0,z1,d0,d1,mat,label):
        section(b,face,box(0,z0,width,z1).difference(cuts),d0,d1,mat,tag+' '+label)
    overlay(0,wall_top,0,.39,PLASTER,'brick wall and reveals')
    overlay(0,.29,-.034,.002,BASE,'foundation course')
    overlay(1.02,1.145,-.013,.003,RED,'lower sill course')
    overlay(band-.67,band-.42,-.012,.002,RED,'lower string band')
    overlay(band-.20,band+.055,-.029,.002,RED,'upper string band')
    # Three recessed courses below the projecting eave are visible above every upper sash.
    for i in range(3):
        overlay(wall_top-.355+i*.081,wall_top-.318+i*.081,-.020-i*.009,.003,PLASTER,'corbelled eave courses')
    for u,pw in pier_axes(face,rows):
        shape=box(max(0,u-pw/2),.29,min(width,u+pw/2),wall_top)
        section(b,face,shape.difference(cuts),-.102,.003,PLASTER,tag+' brick pilasters')
        for a,z in [(1.02,1.145),(band-.67,band+.055)]:
            section(b,face,shape.intersection(box(0,a,width,z)).difference(cuts),-.116,-.098,RED,tag+' banded pilaster')
        section(b,face,box(u-pw*.165,band-.475,u+pw*.165,band-.155),-.127,-.111,SLATE,tag+' dark inset brick squares')
        section(b,face,box(u-pw/2,.02,u+pw/2,.29),-.109,.005,BASE,tag+' pilaster plinths')
    for o in rows:
        key=tag[:2].upper()+str(o['number'])+' '+o['level']
        add_arch(b,face,o,key,lod)
        if o['kind']=='window':
            c=o['center'];lo=o['sill'];half=o['width']/2
            section(b,face,box(c-half-.068,lo-.089,c+half+.068,lo),-.12,.19,RIM,key+' sloped sill nose')
        add_window(b,face,o['number'],o['level'],o,lod)

def downpipe(b,face,u,zmax,lod=False):
    sides=8 if lod else 12;tag=face.title()+' drain'
    def tube(a,c,rad,label):
        pts=[]
        for z in (a,c):
            pts.extend(point(face,u+rad*cos(t),-.16+rad*sin(t),z)for t in np.arange(sides)*2*np.pi/sides)
        faces=[list(range(sides-1,-1,-1)),list(range(sides,2*sides))]+[[i,(i+1)%sides,(i+1)%sides+sides,i+sides]for i in range(sides)]
        b.add(pts,faces,PIPE,label)
    tube(.23,zmax,.064,tag+' downpipe')
    for z in [.78,3.46,5.45,7.1]:tube(z,z+.061,.075,tag+' socket collars')
