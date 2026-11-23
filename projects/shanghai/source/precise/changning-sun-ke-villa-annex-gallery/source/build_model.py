"""Build the documented passage and timber gallery of the Sun Ke Villa annex."""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0] = [str(HERE.parent/'measurements'),str(PROJECT/'source/precise/hongkou-general-post-office/source/common')]
from fit_gallery import GalleryPlane
from photo_architecture import Builder as ArchitectureBuilder, Facade
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
import gallery_finishes

ID = 'changning-sun-ke-villa-annex-gallery'
SLUG = 'sun-ke-villa-annex-gallery'
WALL, BEAM, TILE, EDGE, FLOOR, SHADOW, GLASS, STEEL = (
    'scalloped warm render','ochre red timber','fired barrel tile','charcoal rainwater metal',
    'sandstone plinth','shadowed plaster','smoked window glass','blackened window steel')
PALETTE = {name:{'color':rgb,'roughness':rough} for name,rgb,rough in [
    (WALL,[.61,.48,.36],.90),(BEAM,[.30,.085,.040],.66),(TILE,[.47,.18,.095],.87),
    (EDGE,[.064,.061,.056],.55),(FLOOR,[.50,.43,.35],.83),
    (SHADOW,[.29,.225,.165],.95),(GLASS,[.11,.16,.17],.24),(STEEL,[.074,.067,.059],.54)]}
PALETTE.update(gallery_finishes.PALETTE)
PALETTE['patinated bronze boss']={'color':[.175,.113,.067],'roughness':.55,'metallic':.28}
PALETTE['warm inset circle']={'color':[.54,.385,.245],'roughness':.65}
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in gallery_finishes.STEMS:
            gallery_finishes.metric_uv(self.parts[-1])

    def save(self,path,metadata=None):
        ArchitectureBuilder.save(self,path,metadata)
        return gallery_finishes.writer.embed_normals(path)

META={'id':ID,'name':'孙科住宅附楼三券通道与七跨木廊','heritage_id':'sh-historic-b1-047',
      'address':'延安西路1262号（现番禺路60号园内）','viewer_page':SLUG+'.html','source':'https://m.thepaper.cn/baijiahao_14106378',
      'camera_views':json.loads((HERE/'cameras.json').read_bytes()),'photos_embedded':False,'geometry_license':'MIT','texture_license':'MIT','scope':'附楼临院面可见段：七跨红木廊、三道扁券、方形双端通道、两级筒瓦屋顶与接水斗。','estimated':'立面来自修缮资料实拍，米制取条件尺度。裁切处、楼内及门卫室另记。'}
ARCHES = [
    [(369,476),(385,466),(403,458),(422,453),(437,452),(455,454),(475,461),(487,467),(502,478)],
    [(542,475),(557,466),(576,460),(593,457),(608,456),(625,458),(641,464),(653,469),(663,476)],
    [(694,476),(708,467),(723,462),(738,458),(750,457),(763,458),(777,462),(786,467),(797,476)]]
POSTS = [(369,412),(453,415),(533,418),(609,421),(680,424),(747,427),(811,430),(870,433)]

def rectangle(plane,bounds):
    left,top,right,bottom=bounds
    x0,z1=plane.at(left,top);x1,z0=plane.at(right,bottom)
    return box(x0,z0,x1,z1)

def add_roof(b, x0, x1, depth, eaves, rise, lod):
    front,back=-.23,depth+.23
    mid=(front+back)/2
    section=Polygon([(front,eaves-.13),(mid,eaves+rise-.13),(back,eaves-.13),(back,eaves),(mid,eaves+rise),(front,eaves)])
    b.prism(section,x0,x1,lambda y,z,x:(x,y,z),TILE,'Clay roof/sheet below tile rolls')
    # Tile rolls run down the inclination visible above the long timber gallery.
    spacing=.44 if lod else .205
    count=max(2,round((x1-x0)/spacing))
    for x in np.linspace(x0+.06,x1-.06,count):
        b.tube([(x,front,eaves+.025),(x,mid,eaves+rise+.025),(x,back,eaves+.025)],.045 if lod else .057,TILE,6 if lod else 9,'Clay roof/barrel cover roll')
    b.tube([(x0,mid,eaves+rise+.065),(x1,mid,eaves+rise+.065)],.104,TILE,8 if lod else 12,'Clay roof/ridge cap')

def add_building(b,lod=False):
    plane=GalleryPlane()
    face=Facade(b,(-13,0),(13,0),'Annex frontage')
    right=plane.x(884,440);left=plane.x(42,440)
    posts=[plane.x(x,y)for x,y in POSTS]
    # The 2024 landscape plan gives 7.2–7.4 m across the eaves.
    eaves=5.08;depth=7.1
    deck=sum(plane.z(x,y) for x,y in POSTS)/len(POSTS)
    arch_shapes=[]
    for points in ARCHES:
        edge=[plane.at(px,py) for px,py in points]
        arch_shapes.append(Polygon([(edge[0][0],-.12),*edge,(edge[-1][0],-.12)]))
    passage=rectangle(plane,(110,434,252,582))
    windows=[rectangle(plane,v)for v in [(49,305,120,361),(299,464,325,513),(834,469,873,511)]]
    gallery=box(posts[0]-.06,deck-.025,posts[-1]+.06,eaves+.1)
    outline=box(left,.02,right,eaves)
    face.prism(outline.difference(unary_union([*arch_shapes,passage,*windows,gallery])),-.33,0,WALL,'Street screen, three segmental arches and passage')
    for i,q in enumerate(windows):
        face.window(q,2 if i!=1 else 1,3,frame=STEEL,trim=False,glass=GLASS,label='Steel casement '+str(i+1))
        x0,z0,x1,_=q.bounds
        face.box((x0+x1)/2,z0-.034,x1-x0+.17,.068,.19,.035,FLOOR,'Casement sill '+str(i+1))
    # Two short masonry buttresses have a projecting sloped cap at the arch spring.
    for i,(l,r,spring,top) in enumerate([(510,541,486,460),(663,694,487,463)]):
        a=plane.x(l,spring);c=plane.x(r,spring)
        z=plane.z((l+r)/2,spring);zcap=plane.z((l+r)/2,top)
        section=Polygon([(-.005,.02),(-.20,.02),(-.17,z),(-.005,z)])
        b.prism(section,a,c,lambda y,h,x:(x,y,h),WALL,'Lower arcade/buttress '+str(i+1))
        coping=Polygon([(-.248,z-.018),(-.248,z+.065),(-.034,zcap),(.02,zcap),(.02,z-.018)])
        b.prism(coping,a-.039,c+.039,lambda y,h,x:(x,y,h),FLOOR,'Lower arcade/sloping cap '+str(i+1))
    # Flat passage extends through the wing. The garden-side light is visible from both exterior photographs.
    a,_,c,top=passage.bounds
    for x in [a-.085,c+.085]:
        b.box((x,depth/2,top/2),(.17,depth,top),SHADOW,label='Through passage/plastered cheek')
    b.box(((a+c)/2,depth/2,top+.07),(c-a,depth,.14),SHADOW,label='Through passage/flat soffit')
    b.box(((a+c)/2,depth/2,.025),(c-a,depth,.05),FLOOR,label='Through passage/threshold flags')
    # Two soffit bands and three pairs of round wall details are visible from the park sign.
    # Their function and exact metal composition are undocumented.
    for along in [1.67,4.93]:
        b.box(((a+c)/2,along,top-.037),(c-a,.17,.084),WALL,label='Through passage/cross soffit')
    station=np.asarray(json.loads((HERE.parent/'measurements/passage-station.json').read_bytes())['projection'])
    back_projection=np.linalg.inv(station[:,:3]);eye=-back_projection@station[:,3]
    for i,uv in enumerate([(957,381),(972,381),(995,382),(958,397),(974,397),(993,400)]):
        ray=back_projection@[*uv,1];centre=eye+ray*((c-.030-eye[0])/ray[0])
        _,y,z=centre
        b.tube([(c+.002,y,z),(c-.017,y,z)],.079,'patinated bronze boss',10 if lod else 20,'Through passage/round surround '+str(i+1))
        b.tube([(c-.016,y,z),(c-.030,y,z)],.039,'warm inset circle',9 if lod else 16,'Through passage/round inset '+str(i+1))
    # Ground arcade is one walkable recess, with the entry visible behind the first arch.
    u0,u1=arch_shapes[0].bounds[0],arch_shapes[-1].bounds[2]
    arcdepth=2.08
    for u in (u0-.09,u1+.09):
        b.box((u,arcdepth/2,deck/2),(.18,arcdepth,deck),SHADOW,label='Lower arcade/return')
    b.box(((u0+u1)/2,arcdepth/2,.03),(u1-u0,arcdepth,.06),FLOOR,label='Lower arcade/paving')
    rear=Facade(b,(-13,arcdepth),(13,arcdepth),'Arcade return')
    holes=[box(u0+.16,-.1,u0+1.06,2.21),box(u1-2.41,.20,u1-.25,2.20)]
    rear.prism(box(u0,0,u1,deck-.08).difference(unary_union(holes)),-.16,0,SHADOW,'Inside wall and garden opening')
    rear.window(holes[1],2,1,frame=STEEL,glass=GLASS,trim=False,label='Recessed steel screen')
    # Seven red-lacquer bays are supported on eight separate stone shoes.
    gallery_depth=1.48
    b.box(((posts[0]+posts[-1])/2,gallery_depth/2,deck-.07),(posts[-1]-posts[0]+.17,gallery_depth,.16),WALL,label='Upper gallery/balcony slab')
    tops=[];feet=[]
    for i,(u,(px,py)) in enumerate(zip(posts,POSTS)):
        foot=plane.z(px,py);feet.append(foot)
        top=eaves-.05;tops.append(top)
        face.box(u,foot-.024,.235,.12,.25,0,FLOOR,'Post shoe '+str(i+1))
        face.box(u,(foot+top)/2,.15,top-foot,.16,0,BEAM,'Timber post '+str(i+1))
    face.box((posts[0]+posts[-1])/2,eaves-.10,posts[-1]-posts[0]+.17,.20,.23,.015,BEAM,'Continuous timber plate')
    for i,(a,c) in enumerate(zip(posts,posts[1:])):
        low=(feet[i]+feet[i+1])/2+.045
        # Upper rails are read independently at the seven mid-spans.
        px,py=[(409,376),(491,381),(571,386),(645,389),(711,393),(780,396),(843,399)][i]
        high=plane.at_depth(px,py,-.02)[1]
        for z,h in [(low,.10),(high,.084)]:
            face.box((a+c)/2,z,c-a-.15,h,.089,0,BEAM,'Balcony rail bay '+str(i+1))
        n=[8,8,7,7,7,7,7][i]
        for u in np.linspace(a+.15,c-.15,n):
            face.box(u,(low+high)/2,.044,high-low-.085,.049,.002,BEAM,'Balcony upright bay '+str(i+1))
    # Dark rear openings are visible between the posts. Retain the open bay nearest the southern return.
    inner=Facade(b,(-13,gallery_depth),(13,gallery_depth),'Gallery return')
    door_centres=[(posts[2]+posts[3])/2,(posts[4]+posts[5])/2,(posts[6]+posts[7])/2]
    doors=[box(u-.38,deck-.02,u+.38,eaves-.31) for u in door_centres]
    doors.append(box(posts[5]+.13,deck-.02,posts[6]-.15,eaves-.24))
    inner.prism(box(posts[0],deck-.02,posts[-1],eaves).difference(unary_union(doors)),-.20,0,SHADOW,'Rear wall with visible openings')
    for i,q in enumerate(doors[:3]):
        x0,z0,x1,z1=q.bounds
        b.box(((x0+x1)/2,gallery_depth+.28,(z0+z1)/2),(x1-x0+.02,.12,z1-z0+.02),STEEL,label='Gallery return/shaded doorway '+str(i+1))
    for n,(x,y) in enumerate([(270,440),(886.3,440)]):
        u=plane.at_depth(x,y,-.067)[0]
        b.tube([(u,-.067,.14),(u,-.067,eaves-.38),(u,-.20,eaves-.28),(u,-.20,eaves-.12)],.058,EDGE,6 if lod else 10,'Eaves/downpipe '+str(n+1))
    # Hopper below two unequal eaves. The collector and two branches recur in both photographs.
    u=plane.at_depth(270,440,-.067)[0]
    base=plane.at_depth(270,339,-.08)[1]
    for z,w,h,depth_in in [(base+.12,.22,.24,.20),(base+.25,.31,.11,.23)]:
        face.box(u,z,w,h,depth_in,.083,EDGE,'Stepped eaves/rainwater hopper')
    b.tube([(u-.22,-.20,eaves-.18),(u-.22,-.14,base+.36),(u-.07,-.14,base+.29)],.050,EDGE,7 if lod else 12,'Stepped eaves/second inlet')
    shift=plane.x(247,291)
    add_roof(b,left-.06,shift,depth,eaves-.07,1.64,lod)
    add_roof(b,shift+.002,right+.13,depth,eaves+.033,1.92,lod)
    for a,c,z in [(left-.06,shift,eaves-.13),(shift+.002,right+.13,eaves-.027)]:
        b.box(((a+c)/2,-.205,z),(c-a,.14,.115),EDGE,label='Eaves/section trough')
    return b

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--lod',action='store_true')
    args=parser.parse_args();model=add_building(Builder(PALETTE),args.lod);report=model.save(args.output,META)
    print(json.dumps({'sha256':report['sha256'],'closed_parts':len(model.parts),'triangles':sum(len(p['triangles'])for p in model.parts)}))
