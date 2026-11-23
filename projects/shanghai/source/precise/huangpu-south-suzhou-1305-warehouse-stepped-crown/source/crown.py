"""Photographic reconstruction of the three-bay upper frontage at 1305 South Suzhou Road."""
from math import cos, sin, tau
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient

BRICK='Light yellow running-bond brick'
PIER='Warm-grey rendered pier'
EDGE='Grey cast-cement step and rim'
FACE='Rubbed face of the cement ornament'
DISC='Pale roundel centre'
LETTER='Pale cement numerals'
PALETTE={}
for name,colour in [(BRICK,(255,255,255)),(PIER,(123,119,107)),(EDGE,(116,112,99)),(FACE,(145,140,125)),(DISC,(172,170,154)),(LETTER,(147,126,95))]:
    PALETTE[name]={'color':[(c/255)**2.2 for c in colour],'roughness':.89}
PALETTE[BRICK]['texture']=str(Path(__file__).with_name('brick-bond.png'))
SCALE_X=9.23/690
SCALE_Z=.01355
BASE=484
def xz(u,v):
    return (u-371)*SCALE_X,(BASE-v)*SCALE_Z

def relief(b,points,front,back,material,label):
    shape=orient(Polygon([xz(u,v) for u,v in points]),1)
    assert shape.is_valid and shape.area>1e-5,label
    b.prism(shape,-back,-front,lambda x,z,d:(x,-d,z),material,label)
def rect(b,l,r,top,bottom,front,back,mat,label):
    relief(b,[(l,top),(r,top),(r,bottom),(l,bottom)],front,back,mat,label)

def ring(b,lod):
    # The exposed front and sloping returns form one closed annulus.
    cx,cz=xz(378,285)
    profile=[(.579,.012),(.579,-.062),(.60,-.116),(.63,-.154),(.735,-.154),(.766,-.106),(.772,-.052),(.760,.012)]
    vertices=[];faces=[];count=40 if lod else 96
    for radius,y in profile:
        vertices.extend((cx+radius*cos(tau*i/count),y,cz+radius*sin(tau*i/count)) for i in range(count))
    for row in range(len(profile)):
        nex=(row+1)%len(profile)
        for i in range(count):
            j=(i+1)%count
            faces.append((row*count+i,row*count+j,nex*count+j,nex*count+i))
    b.add(vertices,[tuple(reversed(f)) for f in faces],EDGE,'Roundel | moulded annular rim')
    angles=[(378+.59/SCALE_X*cos(tau*i/count),285-.59/SCALE_Z*sin(tau*i/count)) for i in range(count)]
    relief(b,angles,-.025,.012,DISC,'Roundel | recessed solid disc')

def crown_strips(b,u,head,foot,wide,name):
    # Each cap has a higher, longer central tongue with two shallower wing strips.
    rect(b,u-wide/2,u+wide/2,head+14,foot-15,-.11,.009,EDGE,name+' | outside flanges')
    rect(b,u-wide*.34,u+wide*.34,head+7,foot-8,-.157,-.107,PIER,name+' | middle step')
    rect(b,u-wide*.19,u+wide*.19,head,foot,-.205,-.155,FACE,name+' | central drop')

def arrow(b,u):
    # The lower edge is two sloping wings. Each wing carries a second stepped face.
    label=('East' if u<350 else 'West')+' | winged boss'
    def local(coords):return [(u+du,v) for du,v in coords]
    relief(b,local([(-67,385),(-28,385),(-19,369),(18,369),(27,385),(67,385),(67,420),(9,449),(0,462),(-10,449),(-67,422)]),-.10,.012,EDGE,label+' | sloping base')
    for sign in (-1,1):
        relief(b,local([(sign*11,390),(sign*61,390),(sign*61,403),(sign*31,404),(sign*31,414),(sign*14,423)]),-.152,-.097,FACE,label+(' | left wing' if sign<0 else ' | right wing'))
    relief(b,local([(-16,366),(16,366),(19,376),(10,388),(-10,388),(-20,376)]),-.178,-.097,FACE,label+' | crown')
    relief(b,local([(-10,387),(10,387),(8,448),(0,456),(-8,448)]),-.189,-.097,FACE,label+' | downstroke')

def date(b,lod):
    # Centre lines of the shallow, unboxed 1933 inscription visible above the circular rim.
    paths=[
        [(322,230),(322,209),(318,212)],
        [(332,224),(336,229),(344,228),(351,219),(353,208),(348,200),(341,198),(335,201),(332,208),(335,215),(343,216),(351,211)],
        [(360,206),(371,207),(378,210),(378,214),(371,218),(364,219),(373,219),(380,223),(380,229),(375,233),(362,232)],
        [(388,201),(401,202),(408,206),(407,212),(400,216),(393,217),(401,219),(408,223),(406,230),(399,233),(388,232)]]
    for i,coords in enumerate(paths):
        # Width and the small differences between the two threes are retained from the elevation.
        line=LineString([xz(x,y) for x,y in coords])
        shape=orient(line.buffer(.019,quad_segs=2 if lod else 4,cap_style=1,join_style=1),1)
        b.prism(shape,-.009,.045,lambda x,z,d:(x,-d,z),LETTER,f'Date | 1933, character {i+1}')

def texture_coordinates(b):
    for part in b.parts:
        if part['material']!=BRICK:continue
        xyz=np.asarray(part['vertices']);new=[];uv=[];indices=[]
        for abc in part['triangles']:
            v=xyz[list(abc)];axis=np.argmax(abs(np.cross(v[1]-v[0],v[2]-v[0])))
            first=len(new);indices.append([first,first+1,first+2]);new.extend(v.tolist())
            for x,y,z in v:
                u=(x+5.25)/10.5 if axis!=0 else (y+.5)/.9
                t=1-z/5.50 if axis!=2 else (y+.5)/.9
                uv.append([u,t])
        part.update(vertices=new,triangles=indices,texcoords=uv)

def model(b,lod=False):
    # Gable coping follows three heights. Its ends are the outside faces of the two outer pilasters.
    body=[(24,239),(68,239),(68,245),(211,245),(211,147),(535,147),(535,248),(679,248),(679,247),(714,247),(714,484),(24,484)]
    relief(b,body,.012,.32,BRICK,'Crown fragment | brick field')
    for u,top,width,end,name in [(24,190,67,374,'East outer pier'),(239,98,66,293,'East inner pier'),(496,115,68,297,'West inner pier'),(714,219,65,376,'West outer pier')]:
        rect(b,u-width/2,u+width/2,top+25,484,-.038,.015,PIER,name+' | pier body')
        crown_strips(b,u,top,end,width-11,name)
    for left,right,top,bottom,name in [(52,211,240,258,'East'),(271,465,148,168,'Centre'),(530,685,248,266,'West')]:
        rect(b,left,right,top,bottom,-.058,.32,PIER,name+' | cap of brick panel')
        rect(b,left-1,right+1,top-1,top+5,-.105,.33,EDGE,name+' | projecting roof edge')
    for u,top,foot,width,name in [(147,206,345,48,'East short pendant'),(372,113,205,39,'Central short pendant'),(599,211,354,47,'West short pendant')]:
        crown_strips(b,u,top,foot,width,name)
    rect(b,271,464,372,451,-.038,.015,PIER,'Centre | plain spandrel')
    rect(b,270,466,369,379,-.101,-.034,EDGE,'Centre | upper spandrel lip')
    rect(b,271,467,445,452,-.065,-.035,EDGE,'Centre | lower spandrel lip')
    arrow(b,145);arrow(b,613)
    ring(b,lod);date(b,lod)
    texture_coordinates(b)
