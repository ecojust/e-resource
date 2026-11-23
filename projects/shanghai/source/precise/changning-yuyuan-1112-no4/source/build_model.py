"""The two exposed elevations of the projecting southeast wing at 4, Lane 1112, Yuyuan Road."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

import corner_and_lane
import street_control
import numbered_gate
import roof_and_court
import finishes

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder

class SurfaceBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in finishes.STEMS:finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        Builder.save(self,path,metadata)
        return finishes.writer.embed_normals(path)


ID='changning-yuyuan-1112-no4'
META=dict(id=ID,name='愚园路1112弄4号蒋光鼐旧居',address='上海市长宁区愚园路1112弄4号',register='3M009',formal_id='sh-historic-b3-107',number='4',viewer_page='yuyuan-1112-no4.html',
          scope='4号南凸翼、弧形压顶、临弄窗墙、门牌、公告箱、院门与两片屋顶。后端遮挡面依据俯视近似。北栋20号另记。',geometry_license='MIT', photos_embedded=False)
META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())
WALL='aged warm lime render'
LINTEL='light ochre cast stone'
BELT='banded grey base'
DARK='oxide brown joinery'
LIGHT='pale painted steel'
GLASS='blue grey glazing'
SHADOW='deep opening reveal'
PALETTE={key:dict(color=color,roughness=r) for key,color,r in [
    (WALL,[.715,.668,.552],.95),(LINTEL,[.564,.527,.433],.89),(BELT,[.365,.344,.295],.92),
    (DARK,[.128,.079,.055],.63),(LIGHT,[.641,.677,.652],.62),(GLASS,[.119,.169,.166],.27),(SHADOW,[.089,.09,.075],.93),('indigo awning cloth',[.086,.106,.157],.89)]}
FEATURES=json.loads((HERE/'window-readings.json').read_bytes())
CAMERA=json.loads((HERE/'camera-2011.json').read_bytes())

def homography(uv,xz):
    system=[];target=[]
    for (u,v),(x,z) in zip(uv,xz):
        system.extend([[u,v,1,0,0,0,-x*u,-x*v],[0,0,0,u,v,1,-z*u,-z*v]])
        target.extend((x,z))
    return np.r_[np.linalg.lstsq(system,target,rcond=None)[0],1.].reshape(3,3)

def on_plane(pixel,axis,value):
    center=np.array(CAMERA['principal_point_px'])
    v=np.array(CAMERA['world_to_camera_rotation']).T@np.r_[(np.array(pixel)-center)/CAMERA['focal_pixels'],1.]
    c=np.array(CAMERA['camera_origin_m'])
    return c+v*(value-c[axis])/v[axis]

def wing_openings(side):
    reg=FEATURES['sources'][side]
    if side=='street-wing':
        matrix=homography(*street_control.wing_registration())
        def position(p):
            q=matrix@[*p,1.]
            return q[:2]/q[2]
    else:
        def position(p):
            v=on_plane(p,0,reg['constant_x_m'])
            return (-v[1],v[2])
    return {key:Polygon([position(p) for p in points]) for key,points in FEATURES[side].items()}

def joinery(extrude,opening,key,lod):
    x0,z0,x1,z1=opening.bounds
    glass=opening.buffer(-.087,join_style='mitre')
    paint=LIGHT if key in {'front-arch-left','front-arch-middle','side-mid-arch'} else DARK
    extrude(opening.difference(glass),-.226,-.132,paint,key+'/rebated perimeter')
    # The segmental openings have a continuous transom. The raised shoulders remain open around the upper light.
    narrow=key.endswith(('slit','narrow'))
    xs=[] if narrow else ([.50] if lod else [.30,.68])
    zs=[.73] if 'arch' in key or narrow else ([.71] if lod else [.36,.72])
    if key=='corner_upper_window' and not lod:
        xs=[.24,.49,.74];zs=[.17,.34,.51,.69,.87]
    for j,t in enumerate(xs):
        x=x0+(x1-x0)*t
        extrude(glass.intersection(box(x-.028,z0-.02,x+.028,z1+.02)),-.215,-.149,paint,f'{key}/vertical bar {j+1}')
    for j,t in enumerate(zs):
        z=z0+(z1-z0)*t
        extrude(glass.intersection(box(x0-.02,z-.028,x1+.02,z+.028)),-.206,-.143,paint,f'{key}/transom {j+1}')
    if lod:
        extrude(glass,-.255,-.237,GLASS,key+'/glazing')
    else:
        cuts=[box(x0+(x1-x0)*t-.027,z0-.1,x0+(x1-x0)*t+.027,z1+.1) for t in xs]
        cuts.extend(box(x0-.1,z0+(z1-z0)*t-.027,x1+.1,z0+(z1-z0)*t+.027) for t in zs)
        panes=glass.difference(unary_union(cuts))
        for j,p in enumerate(getattr(panes,'geoms',[panes])):
            extrude(p,-.255,-.237,GLASS,f'{key}/pane {j+1}')
    sill=box(x0-.091,z0-.096,x1+.095,z0-.009)
    extrude(sill,-.047,.132,LINTEL,key+'/drip sill')

def wing(b,lod):
    for side in ['street-wing','west-wing-return']:
        front=side=='street-wing'
        mapper=(lambda u,z,d:(u,-3.30-d,z)) if front else (lambda u,z,d:(5.53-d,-u,z))
        left,right=(5.53,14.98) if front else (-.67,3.30)
        def extrude(shape,back,face,material,label):
            b.prism(shape,back,face,mapper,material,side+'/'+label)
        openings=wing_openings(side)
        field=box(left,4.25,right,11.27).difference(unary_union(list(openings.values())))
        extrude(field,-.37,0,WALL,'wall with open reveals')
        for key,shape in openings.items():
            joinery(extrude,shape,key,lod)
        extrude(box(left,.0,right,4.245),-.37,-.007,BELT,'ground floor behind enclosure')
        for j,(z0,z1,depth,material) in enumerate([
            (3.50,3.55,.072,BELT),(3.90,3.98,.089,BELT),(4.17,4.25,.142,LINTEL)
        ]):
            extrude(box(left,z0,right,z1),-.03,depth,material,f'horizontal belt course {j+1}')
        profile=json.loads((HERE.parent/'measurements/front-cornice-four-stations.json').read_bytes())
        elevations=[profile['registered_roof_lip_elevation_m'],*profile['median_absolute_course_edges_m']]
        depths=[.272,.25,.22,.17,.12]
        materials=[BELT,LINTEL,BELT,LINTEL,BELT]
        maximum_overhang=(street_control.P['west_to_east_eave_width']-street_control.P['waist_frontage_width'])/(2*street_control.WING_SCALE)
        for j,(upper,lower,depth,material) in enumerate(zip(elevations,elevations[1:],depths,materials)):
            z0=(lower-street_control.OFFSET)/street_control.SCALE
            z1=(upper-street_control.OFFSET)/street_control.SCALE
            over=maximum_overhang*depth/depths[0] if front else 0.
            extrude(box(left-over,z0,right+over,z1),-.03,depth,material,f'photographed eave course {j+1}')
    return b

def build(lod=False):
    b=wing(Builder({**PALETTE,**numbered_gate.PALETTE,**roof_and_court.PALETTE}),lod)
    corner_and_lane.add(b,sys.modules[__name__],lod)
    street_control.apply(roof_and_court.court(b,sys.modules[__name__],lod))
    roof_and_court.roof(b,sys.modules[__name__],lod)
    numbered_gate.add(b,sys.modules[__name__],lod)
    result=SurfaceBuilder({**b.palette,**finishes.PALETTE})
    for part in b.parts:result.add(part['vertices'],part['triangles'],part['material'],part['label'])
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--lod',action='store_true')
    args=parser.parse_args()
    print(build(args.lod).save(args.output,META)['sha256'])
