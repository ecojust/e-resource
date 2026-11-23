"""Construct the river-facing dormitory and stair tower of Mann Hall, ECUPL."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
ID='changning-st-johns-mann-hall-river-front'
URL='https://www.ecupl.edu.cn/2022/1101/c13514a193941/page.htm'
m=json.loads((HERE.parent/'measurements/river-registration.json').read_bytes())
W=m['width'];DEPTH=m['depth'];B1,B2,EAVE,RIDGE,FRACTION,PROJ,TW,OZ=m['parameters'];CX=W*FRACTION
GREY='Mann Hall | grey facing brick';BAND='Mann Hall | reddish brick string course';STONE='Mann Hall | pale lintel and sill';GLASS='Mann Hall | recessed window glass';FRAME='Mann Hall | cream-painted sash';SHUTTER='Mann Hall | dark shutter';ROOF='Mann Hall | dark grey pan tiles';EAVEWOOD='Mann Hall | weathered timber soffit';DARK='Mann Hall | dark reveals'
def surface(c,rough):return dict(color=c,roughness=rough)
PALETTE={GREY:surface([.235,.216,.20],.93),BAND:surface([.225,.093,.054],.9),STONE:surface([.64,.588,.49],.84),FRAME:surface([.735,.697,.61],.72),GLASS:dict(color=[.095,.147,.158],alpha=.73,roughness=.29),SHUTTER:surface([.118,.137,.121],.85),EAVEWOOD:surface([.129,.079,.049],.85),ROOF:surface([.075,.070,.064],.91),DARK:surface([.045,.052,.050],.99)}
META=dict(id=ID,name='圣约翰大学思孟堂43号楼临河窗墙',heritage_id='sh-historic-b2-060',official_id='2M006',address='万航渡路1575号华东政法大学长宁校区，房管局名录原址1175号',source=URL,photo_source=URL,geometry_license='MIT',texture_license='MIT',photos_embedded=False,viewer_page='st-johns-mann-hall-river-front.html',scope='River-facing ten bays of campus building 43, with projecting stair tower, masonry oculus, stepped eaves and visible side returns. The western courtyard arcade and hidden interior are outside this component.',camera_views=json.loads((HERE/'cameras.json').read_bytes()))
def wall(b,poly,front,back,mat,label,side=None):
    def xyz(x,z,d):
        if side=='north':return W+d,x,z
        if side=='south':return -d,-x,z
        return x,-d,z
    b.prism(poly,-back,-front,xyz,mat,label)
def block(b,x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)
def arch(x,z,w,h,rise,n):
    xs=np.linspace(-w/2,w/2,n)
    radius=w*w/(8*rise)+rise/2
    return Polygon([(x-w/2,z),(x+w/2,z),*[(x+u,z+h-radius+np.sqrt(max(0.,radius*radius-u*u)))for u in xs[::-1]]])
def window(b,outer,front,lod,name,side=None,pair=True,shutters=False):
    x0,z0,x1,z1=outer.bounds;xc=(x0+x1)/2
    def extrusion(p,a,c,m,k):wall(b,p,a,c,m,name+' / '+k,side)
    inner=outer.buffer(-.071,join_style=2)
    extrusion(outer.difference(inner),front+.08,front+.17,FRAME,'sash surround')
    extrusion(inner,front+.19,front+.214,GLASS,'recessed glass')
    extrusion(inner,front+.48,front+.50,DARK,'unlit room')
    bars=[box(xc-.030,z0,xc+.030,z1)]if pair else []
    bars.append(box(x0,z1-.51,x1,z1-.47))
    if not lod and pair:
        for dx in [-.25,.25]:
            xx=xc+dx*(x1-x0);bars.append(box(xx-.015,z1-.49,xx+.015,z1))
    extrusion(inner.intersection(unary_union(bars)),front+.12,front+.18,FRAME,'sash divisions')
    extrusion(box(x0-.085,z0-.105,x1+.085,z0),front-.105,front+.2,STONE,'projecting sill')
    if shutters:
        for k,d in enumerate([x0-.40,x1+.06]):
            extrusion(box(d,z0+.11,d+.34,z1-.29),front-.074,front-.012,SHUTTER,'shutter '+str(k+1))
            if not lod:
                for j in range(6):
                    z=z0+.22+j*.17
                    extrusion(box(d+.034,z,d+.306,z+.025),front-.096,front-.070,EAVEWOOD,'shutter slat '+str(k+1)+'-'+str(j+1))
def roof(b,x0,x1,y0,y1,eave,ridge,mat,name):
    # Only the photographically attested front slope and two hipped ends reach its ridge.
    inset=min((y1-y0)*.89,(x1-x0)*.31)
    plan=[(x0,y0),(x1,y0),(x1,y1),(x1-inset,y1),(x0+inset,y1),(x0,y1)]
    top=[eave,eave,eave,ridge,ridge,eave]
    v=[(x,y,z-.16)for (x,y),z in zip(plan,top)]+[(x,y,z)for (x,y),z in zip(plan,top)]
    faces=[(0,1,3,4),(1,2,3),(0,4,5)]
    b.add(v,[tuple(reversed(t))for t in faces]+[tuple(k+6 for k in t)for t in faces]+[(i,(i+1)%6,(i+1)%6+6,i+6)for i in range(6)],mat,name)
    return inset
def add_building(b,lod=False):
    n=9 if lod else 21
    spans=[(0,CX-TW/2),(CX+TW/2,W)]
    for k,(a,c) in enumerate(spans):
        holes=[]
        for i in (range(5)if k==0 else range(6,10)):
            x=W*(i+.5)/10
            for j,(sill,height) in enumerate([(max(.24,B1-2.25),1.56),(B1+.70,1.88),(B2+.72,1.85)]):
                name=f'river bay {i+1:02} / floor {j+1}'
                hole=arch(x,sill,1.25 if j else 1.18,height,.06,n)
                holes.append(hole);window(b,hole,0,lod,name,shutters=(j>0))
                if j==0:
                    wall(b,box(x-.72,sill+height+.015,x+.72,sill+height+.085),-.065,.03,STONE,name+' / lintel')
        wall(b,box(a,0,c,EAVE).difference(unary_union(holes)),0,.42,GREY,'river half '+str(k+1)+' / cut brick wall')
        for j,z in enumerate([B1,B2]):
            block(b,a,c,-.121,.20,z-.16,z+.045,BAND,f'river half {k+1} / string course {j+1}')
            block(b,a,c,-.19,.21,z+.045,z+.095,STONE,f'river half {k+1} / stone drip {j+1}')
    front=-PROJ;clean=[]
    circle=Point(CX,OZ).buffer(.65,quad_segs=6 if lod else 14);clean.append(circle)
    wall(b,circle.buffer(.205,quad_segs=4).difference(circle),front-.092,front+.05,BAND,'river stair / genuine brick oculus ring')
    wall(b,circle.difference(circle.buffer(-.065)),front+.095,front+.17,FRAME,'river stair / pale oculus frame')
    wall(b,circle.buffer(-.065),front+.18,front+.202,GLASS,'river stair / round glazing')
    wall(b,circle.buffer(-.064),front+.48,front+.5,DARK,'river stair / oculus backing')
    for j,z in enumerate([1.32,4.98]):
        hole=arch(CX,z,1.29,1.82,.09,n);clean.append(hole)
        window(b,hole,front,lod,'river stair / intermediate landing '+str(j+1))
        surround=hole.buffer(.16,join_style=2).difference(hole).intersection(box(CX-1,z+1.65,CX+1,z+2.2))
        wall(b,surround,front-.084,front+.03,BAND,'river stair / landing eyebrow '+str(j+1))
    wall(b,box(CX-TW/2,0,CX+TW/2,EAVE+.17).difference(unary_union(clean)),front,front+.30,GREY,'river stair / pierced projecting frontage')
    for sign in [-1,1]:
        x=CX+sign*(TW/2-.14)
        block(b,x-.14,x+.14,front+.30,.42,0,EAVE+.17,GREY,'river stair / side return '+str(sign))
    for j,(step,mat,h) in enumerate([(.06,EAVEWOOD,.09),(.18,STONE,.08),(.26,EAVEWOOD,.07)]):
        z=EAVE+.11*j
        block(b,-step,W+step,-step,.45,z,z+h,mat,'main eave / layer '+str(j+1))
        block(b,CX-TW/2-step,CX+TW/2+step,front-step,.28,z+.17,z+.17+h,mat,'stair eave / layer '+str(j+1))
    inset=roof(b,-.54,W+.54,-.51,DEPTH/2,EAVE+.32,RIDGE,ROOF,'river roof / hipped slope')
    b.tube([(inset-.54,DEPTH/2,RIDGE+.024),(W+.54-inset,DEPTH/2,RIDGE+.024)],.082,ROOF,8 if lod else 12,'main roof / ridge roll')
    roof(b,CX-TW/2-.33,CX+TW/2+.33,front-.39,1.60,EAVE+.49,EAVE+1.71,ROOF,'stair roof / hipped cross slope')
    for side in ['south','north']:
        length=DEPTH/2
        room=[];desc=side+' wing / '
        for j,z in enumerate([B1+.62,B2+.65]):
            for idx,y in enumerate([1.86,4.98]):
                # The northern night view exposes an arched bay. In the daytime southern return the smaller openings are squarer.
                u=y if side=='north'else -y
                hole=arch(u,z,1.31 if side=='south'else 1.34,2.04,.63 if side=='north'else .05,n)
                room.append(hole);window(b,hole,0,lod,desc+'return window '+str(j*2+idx+1),side,side=='south')
                if side=='north':
                    extr=hole.buffer(.195,join_style=2).difference(hole).intersection(box(u-1.0,z+1.37,u+1.0,z+2.3))
                    wall(b,extr,-.101,.01,BAND,desc+'arch of window '+str(j*2+idx+1),side)
        a,c=(0,length)if side=='north'else(-length,0)
        wall(b,box(a,0,c,EAVE).difference(unary_union(room)),0,.38,GREY,desc+'cut return wall',side)
        for j,z in enumerate([B1,B2,EAVE]):
            wall(b,box(a,z-.12,c,z+.09),-.15,.18,BAND if j<2 else STONE,desc+'belt '+str(j+1),side)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);b.save(a.output,META)
if __name__=='__main__':main()
