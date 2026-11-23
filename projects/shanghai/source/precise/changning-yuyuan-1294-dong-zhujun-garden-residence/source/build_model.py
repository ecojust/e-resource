"""Build the numbered eastern gable and the three-bay south loggia of building 18."""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from photo_architecture import Builder, opening
from crown_builder import CrownBuilder
import finishes
from roof import add_roof

ID='changning-yuyuan-1294-dong-zhujun-garden-residence'
DASH='coarse grey-brown pebble dash'; BRICK='warm red facing brick'; STONE='pale precast cement'; TILE='terracotta roof'
GREEN='bottle-green timber'; GLASS='shadowed green glazing'; WOOD='dark painted door'; METAL='dark iron'; IVORY='pale enamel'; INK='dark raised numerals'
PALETTE=dict(finishes.PALETTE)
for key,colour,roughness in [(GREEN,[.068,.192,.144],.62),(GLASS,[.092,.153,.137],.28),(WOOD,[.084,.105,.091],.70),(METAL,[.102,.098,.08],.61),(IVORY,[.83,.80,.67],.73),(INK,[.08,.09,.07],.71)]:
    PALETTE[key]=dict(color=colour,roughness=roughness)
META=dict(id=ID,heritage_id='sh-historic-b3-105',protection_number='3M007',name='董竹君旧居18号楼南面券廊与题号山墙',address='长宁区愚园路1294号，新华村原1号，区政府18号楼',scope='南向三开间低拱券、两层院廊及贯层红砖柱、标号18的东开间山墙、其前门窗与西外阶，保留山墙背后的可辨坡屋盖。',geometry_license='MIT',photos_embedded=False,viewer_page='yuyuan-1294-dong-zhujun-garden-residence.html')
if (HERE/'cameras.json').exists():META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())

class SurfaceBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in finishes.STEMS:finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        Builder.save(self,path,metadata)
        return finishes.writer.embed_normals(path)

def front(b,poly,ynear,yfar,mat,name):
    b.prism(poly,-yfar,-ynear,lambda x,z,d:(x,-d,z),mat,name)
def rect(b,x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)

def aperture_frame(b,x,y,z,w,h,cols,rows,name,door=False):
    outer=box(x-w/2,z,x+w/2,z+h)
    frame=outer.difference(outer.buffer(-.072,join_style='mitre'))
    front(b,frame,y+.075,y+.16,WOOD if door else GREEN,name+'/rebated outer casing')
    for i in range(1,cols):
        cx=x+w*(i/cols-.5)
        rect(b,cx-.019,cx+.019,y+.102,y+.154,z+.068,z+h-.068,WOOD if door else GREEN,name+'/mullion '+str(i))
    for i in range(1,rows):
        zz=z+h*i/rows
        rect(b,x-w/2+.073,x+w/2-.073,y+.096,y+.133,zz-.017,zz+.017,WOOD if door else GREEN,name+'/transom '+str(i))
    for i in range(cols):
        for j in range(rows):
            l=x-w/2+w*i/cols+(.075 if i==0 else .020)
            r=x-w/2+w*(i+1)/cols-(.075 if i==cols-1 else .020)
            lo=z+h*j/rows+(.075 if j==0 else .018)
            hi=z+h*(j+1)/rows-(.075 if j==rows-1 else .018)
            rect(b,l,r,y+.158,y+.183,lo,hi,WOOD if door and j<rows-1 else GLASS,f'{name}/recessed panel {i+1}.{j+1}')

def numbered_face(b,lod):
    xmin,xmax=-3.69,3.69
    openings=[(.22,.10,1.91,2.25,2,3,'ground entrance',True),(-1.61,.87,.83,.84,2,2,'entrance left light',False),
              (-.42,4.37,2.13,1.35,3,3,'first-floor casement',False),(-.82,7.87,2.39,1.76,4,3,'second-floor casement',False),
              (.13,11.34,2.15,1.58,5,4,'attic casement',False)]
    cut=unary_union([box(x-w/2,z,x+w/2,z+h)for x,z,w,h,*_ in openings])
    outline=Polygon([(xmin,0),(xmax,0),(xmax,10.72),(0,14.66),(xmin,10.72)])
    front(b,outline.difference(cut),0,.32,DASH,'east gable/wall, with perforated door and window reveals')
    for x,z,w,h,cols,rows,name,door in openings:
        aperture_frame(b,x,0,z,w,h,cols,rows,name,door)
        if not door:
            rect(b,x-w/2-.068,x+w/2+.068,-.104,.011,z-.086,z+.007,STONE,name+'/external sill')
            if name=='attic casement':
                rect(b,x-w/2-.08,x+w/2+.08,-.086,.002,z+h,z+h+.09,STONE,name+'/lintel')
                for side in (-1,1):
                    xx=x+side*(w/2+.047);rect(b,xx-.047,xx+.047,-.055,0,z,z+h,STONE,name+'/pale side reveal '+str(side))
    # The south photograph shows a two-storey brick pier on either side of the gable field.
    for side in [-1,1]:
        xx=side*2.97
        rect(b,xx-.30,xx+.30,-.148,.005,2.94,10.63,BRICK,'paired continuous brick pier '+str(side))
        rect(b,xx-.35,xx+.35,-.19,.015,2.78,2.97,STONE,'brick pier springing '+str(side))
        for i in range(8):
            near=xx+side*.29
            rect(b,near-.089,near+.089,-.149,-.117,3.13+i*.91,3.42+i*.91,BRICK,'brick bonding key '+str(side)+'-'+str(i))
    for name,y0,z0,z1,r in [('projecting entry hood',-.59,2.63,2.79,2.80),('lower moulding',-.28,2.57,2.64,2.64)]:
        rect(b,-r,r,y0,.03,z0,z1,STONE,name)
    for side in [-1,1]:
        rect(b,side*2.42-.23,side*2.42+.23,-.171,.04,0,2.58,STONE,'entrance stone pier '+str(side))
        rect(b,side*2.42-.27,side*2.42+.27,-.213,.07,0,.29,STONE,'entrance pier shoe '+str(side))
    rect(b,-3.70,3.70,-.08,.04,0,.13,STONE,'east gable/low plinth')
    # The district photograph resolves both numerals separately on a round pale tablet.
    front(b,Point(0,3.25).buffer(.337,quad_segs=12 if lod else 24),-.170,-.068,IVORY,'house number/circular enamel tablet')
    def ink(points,width,name):
        front(b,LineString(points).buffer(width/2,cap_style='round',join_style='round'),-.197,-.168,INK,'house number/'+name)
    ink([(-.135,3.33),(-.092,3.39),(-.092,3.11)],.048,'digit one')
    for zz,rx,rz in [(3.32,.071,.075),(3.184,.085,.087)]:
        pts=[(.074+rx*math.cos(i*math.tau/24),zz+rz*math.sin(i*math.tau/24))for i in range(25)]
        ink(pts,.045,'digit eight loop '+str(zz))
    for side in [-1,1]:
        b.tube([(side*3.61,-.123,10.64),(side*3.61,-.123,1.34),(side*3.55,-.23,.26)],.054,METAL,8 if lod else 12,'east gable/rainwater pipe '+str(side))
        for i in range(3):
            rect(b,side*3.61-.085,side*3.61+.085,-.176,.002,1.65+i*3.16,1.70+i*3.16,METAL,'pipe bracket '+str((side,i)))

def garden_gallery(b,lod):
    left,right=-13.65,-3.69
    grid=[left+i*(right-left)/3 for i in range(4)]
    mids=[(u+v)/2 for u,v in zip(grid,grid[1:])]
    portals=[opening(x,-.001,2.60,2.69,.75,12 if lod else 26) for x in mids]
    front(b,box(left,0,right,3.16).difference(unary_union(portals)),.54,.91,BRICK,'garden loggia/three low brick arches and deep returns')
    for i,(center,p) in enumerate(zip(mids,portals)):
        arch=opening(center,.24,2.81,2.63,.78,12 if lod else 26)
        trim=arch.difference(p).intersection(box(center-1.5,1.89,center+1.5,3))
        front(b,trim,.485,.54,STONE,f'garden loggia/arched extrados {i+1}')
        for xx in (center-1.30,center+1.30):
            rect(b,xx-.108,xx+.108,.428,.94,1.86,1.97,STONE,f'garden loggia/impost {i+1} at {xx:.2f}')
    for z,w in [(3.19,.17),(6.80,.185),(10.49,.20)]:
        rect(b,left-.08,right+.04,.39,2.96,z-w/2,z+w/2,STONE,'garden loggia/solid landing or soffit '+str(z))
        rect(b,left-.13,right+.04,.28,.42,z-.035,z+.045,STONE,'garden loggia/protruding drip '+str(z))
    for i,x in enumerate(grid):
        rect(b,x-.218,x+.218,.54,.96,3.28,10.385,BRICK,'garden loggia/through two floors brick pier '+str(i+1))
        for z in (3.28,6.91,10.26):
            rect(b,x-.244,x+.244,.511,.987,z,z+.095,BRICK,'garden loggia/pier offset '+str((i,z)))
    for j,x in enumerate(mids):
        for i,z in enumerate((3.29,6.92)):
            front(b,box(x-1.426,z,x+1.426,z+.654),.56,.74,BRICK,'garden loggia/parapet '+str((j,i)))
            rect(b,x-1.44,x+1.44,.509,.791,z+.654,z+.750,STONE,'garden loggia/rail coping '+str((j,i)))
    # In the numbered photograph the gallery at the landing also has thin pale
    # arched frames. The substantial low brick arches below belong to another floor.
    for bay,cx in enumerate(mids):
        channel=opening(cx,3.33,2.78,2.69,.81,12 if lod else 28).difference(opening(cx,3.326,2.66,2.621,.78,12 if lod else 28))
        front(b,channel,.476,.542,STONE,'first-floor verandah/slender arch and jambs '+str(bay+1))
        for x in (cx-1.373,cx+1.373):
            rect(b,x-.048,x+.048,.442,.555,5.18,5.31,STONE,'first-floor verandah/arch spring collar '+str(x))
        rect(b,cx-.073,cx+.073,.438,.546,5.945,6.115,STONE,'first-floor verandah/short key '+str(bay+1))
    # The shaded background is a separate recessed plane. Only the front bay margins are modelled.
    cut=unary_union([box(x-.693,z,x+.693,z+2.02) for x in mids for z in (.15,3.40,7.04)])
    front(b,box(left,0,right,10.46).difference(cut),2.91,3.17,DASH,'garden loggia/recessed rear masonry with actual openings')
    for i,x in enumerate(mids):
        for j,z in enumerate((.15,3.40,7.04)):
            aperture_frame(b,x,2.91,z,1.386,2.02,2,3,'gallery recess '+str((i,j)),True)
    # Only the western termination and the visible roof return are closed here.
    rect(b,left-.015,left+.245,.94,3.17,0,10.465,DASH,'western wing/end return')
    rect(b,3.418,3.691,.32,3.18,0,10.69,DASH,'numbered eastern wall/short return')
    for x in (left+.15,right-.14):
        b.tube([(x,.437,10.48),(x,.437,.32)],.048,METAL,6 if lod else 10,'gallery/cast downpipe '+str(x))
    for i in range(3):
        cx=mids[i];rect(b,cx-1.29,cx+1.29,.96,2.90,.002,.072,STONE,'garden loggia/arched bay floor '+str(i))

def add_stair(b,lod):
    # Gao's photograph resolves square posts with double caps and two pierced rectangular rails.
    x0,x1=-6.61,-5.01; y0,y1=-5.05,-.15;rise=3.06;n=18
    for i in range(n):
        lo=y0+(y1-y0)*i/n;hi=y0+(y1-y0)*(i+1)/n
        rect(b,x0,x1,lo,hi,0,(i+1)*rise/n,STONE,'external stair/riser and tread '+str(i+1))
        if not lod:rect(b,x0-.012,x1+.012,lo-.024,lo+.024,(i+1)*rise/n-.029,(i+1)*rise/n+.001,STONE,'external stair/tread nosing '+str(i+1))
    rect(b,x0,x1,y1,.57,0,rise,STONE,'external stair/top landing')
    def side(poly,x,thickness,mat,name):
        b.prism(poly,x,x+thickness,lambda y,z,d:(d,y,z),mat,name)
    for j,xx in enumerate([x0-.13,x1-.05]):
        side(Polygon([(y0,0),(y1,0),(y1,rise+.18),(y0,.18)]),xx,.18,STONE,'external stair/stringer '+str(j+1))
        for k,t in enumerate([0,.49,1.]):
            yy=y0+t*(y1-y0);zz=t*rise+(.37 if k==0 else 0)
            rect(b,xx-.085,xx+.265,yy-.173,yy+.173,.14,zz+1.045,STONE,'external stair/square newel '+str((j,k)))
            for h,r,w in [(1.045,.073,.46),(1.118,.065,.41),(1.183,.05,.34)]:
                rect(b,xx+.09-w/2,xx+.09+w/2,yy-w/2,yy+w/2,zz+h,zz+h+r,STONE,'external stair/stepped newel cap '+str((j,k,h)))
        for k,(a,c)in enumerate([(.045,.453),(.534,.961)]):
            ya=y0+a*(y1-y0);yc=y0+c*(y1-y0);za=a*rise;zc=c*rise
            panel=Polygon([(ya,za+.19),(yc,zc+.19),(yc,zc+.96),(ya,za+.96)])
            for t in (.26,.70):
                yy=ya+t*(yc-ya);zz=za+t*(zc-za)
                hole=Polygon([(yy-.13,zz+.49),(yy+.13,zz+.65),(yy+.13,zz+.85),(yy-.13,zz+.69)])
                panel=panel.difference(hole)
            side(panel,xx+.018,.148,STONE,'external stair/raked pierced rail '+str((j,k)))
            side(Polygon([(ya,za+.96),(yc,zc+.96),(yc,zc+1.026),(ya,za+1.026)]),xx-.008,.201,STONE,'external stair/raked coping '+str((j,k)))

def build(lod=False):
    b=Builder(dict(PALETTE))
    numbered_face(b,lod)
    garden_gallery(b,lod)
    add_stair(b,lod)
    add_roof(b,lod,TILE,STONE,BRICK)
    result=SurfaceBuilder(PALETTE)
    for p in b.parts:result.add(p['vertices'],p['triangles'],p['material'],p['label'])
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--lod',action='store_true');args=parser.parse_args()
    print(build(args.lod).save(args.output,META)['sha256'])
