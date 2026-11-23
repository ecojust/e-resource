"""Model the photograph-recorded brick stair hall at the former Furu Hospital."""
from pathlib import Path
import argparse, json, sys
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).absolute().parent
PROJECT=next(x for x in HERE.parents if (x/'tools/package_architectural_model.py').exists())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
ID='changning-furu-hospital-stepped-stair-hall'
brick='Furu | dark red facing brick'
stone='Furu | chalk grey cement'
frame='Furu | dark green rolled steel'
glass='Furu | green grey glass'
dark='Furu | opening shadow'
PALETTE={brick:dict(color=[.43,.185,.149],roughness=.92),stone:dict(color=[.68,.675,.614],roughness=.88),frame:dict(color=[.104,.149,.120],roughness=.64),glass:dict(color=[.235,.339,.290],roughness=.30,alpha=.71),dark:dict(color=[.061,.072,.061],roughness=.9)}
META=dict(id=ID,model_id=ID,name='私立妇孺医院旧院临街楼梯间与阶梯钢窗',viewer_page='furu-hospital-stepped-stair-hall.html',heritage_id='sh-historic-b3-108',official_id='3M010',geometry_license='MIT',photos_embedded=False,scope='The projecting stair hall as documented in the Changning authority photograph. The hospital name on the historic facade records an earlier use.')
data=json.loads((HERE.parent/'measurements/plate-readings.json').read_bytes())

def image_to_wall():
    a=[];b=[]
    for (u,v),(x,z) in zip(data['facade_control_pixels'], data['facade_control_local_xz']):
        a.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*z,-v*z]])
        b.extend([x,z])
    return np.r_[np.linalg.solve(a,b),1].reshape(3,3)

def section(b,shape,front,back,material,name):
    b.prism(shape,-back,-front,lambda x,z,d:(x,-d,z),material,name)

def add_building(b,lod=False):
    matrix=image_to_wall()
    def xz(u,v):
        pt=matrix@[u,v,1];return pt[:2]/pt[2]
    def openings(row):
        windows=[]
        for a,c,t,f in zip(row['edge_u'][:-1],row['edge_u'][1:],row['top_v'],row['bottom_v']):
            z0=xz((a+c)/2,f)[1];z1=xz((a+c)/2,t)[1]
            x0=xz(a,(t+f)/2)[0];x1=xz(c,(t+f)/2)[0]
            windows.append(box(x0,z0,x1,z1))
        return windows
    sets=[openings(k) for k in data['ascending_sashes_bottom_to_top']+[data['lower_partial_stepped_light']]]
    all_open=unary_union([w for row in sets for w in row])
    section(b,box(0,3.2,4.95,17.3).difference(all_open),0,.25,brick,'street face/four staggered masonry openings')
    u,v=data['oculus_px']['centre'];center=xz(u,v)
    radius=xz(u+data['oculus_px']['radius_x'],v)[0]-center[0]
    ring=Point(*center).buffer(radius,resolution=7 if lod else 15)
    section(b,box(0,0,4.95,3.2).difference(ring).difference(all_open),0,.26,stone,'plinth/circular punched window')
    section(b,ring.difference(ring.buffer(-.034)),.075,.115,frame,'plinth/circular steel surround')
    section(b,ring.buffer(-.034),.129,.15,dark,'plinth/recessed oculus')
    for i,row in enumerate(sets):
        for j,shape in enumerate(row):
            inner=shape.buffer(-.035,join_style='mitre')
            if inner.is_empty:continue
            a,h,c,k=inner.bounds
            label=f'landing {i+1} / light {j+1}'
            section(b,shape.difference(inner),.085,.128,frame,label+' perimeter')
            section(b,inner,.14,.16,glass,label+' glazing')
            if i<4:
                z=h+(k-h)*.49
                section(b,box(a,z-.014,c,z+.014),.094,.121,frame,label+' horizontal rail')
                if not lod:
                    x=a+(c-a)*.49
                    section(b,box(x-.010,h,x+.010,k),.105,.134,frame,label+' vertical division')
    def slab(x0,x1,y0,y1,z0,z1,mat,label):
        b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],mat,label=label)
    for side in [(0,.23),(4.72,4.95)]:
        x0,x1=side
        slab(x0,x1,.25,1.44,0,3.2,stone,'side plinth / '+str(x0))
        slab(x0,x1,.25,1.44,3.2,17.3,brick,'side return / '+str(x0))
    slab(-.05,5.,-.075,1.46,17.3,17.40,stone,'stair parapet/top coping')
    a=xz(457,96)[1];slab(-.036,4.99,-.055,.28,a-.035,a+.045,stone,'stair parapet/horizontal cement line')
    a=xz(455,147)[1];tip=xz(579,169)[0]
    slab(-.15,tip,-.53,.27,a-.14,a+.055,stone,'upper landing/projecting concrete eyebrow')
    slab(-.15,.24,.27,1.46,a-.14,a+.055,stone,'upper landing/eyebrow return')

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',required=True,type=Path);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args();b=Builder(PALETTE);add_building(b,args.lod)
    result=b.save(args.output,META);print(result['parts'],result['triangles'],result['sha256'])
if __name__=='__main__':main()
