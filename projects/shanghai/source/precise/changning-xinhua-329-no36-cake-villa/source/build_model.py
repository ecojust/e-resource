"""Reconstruct the photographed garden-facing portion of No. 36, Lane 329."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from shapely.geometry import box as rectangle,Polygon
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
ID='changning-xinhua-329-no36-cake-villa'
PLASTER='Cake house | pale mineral render';BRICK='Cake house | brown face brick'
GLASS='Cake house | garden glass';BLOCK='Cake house | translucent glass blocks'
IRON='Cake house | pale steel';STONE='Cake house | grey stair and sill'
ROOF='Cake house | weathered red tile';GUTTER='Cake house | dark roof edge'
RECESS='Cake house | shadowed internal return'
PALETTE={PLASTER:{'color':[.66,.61,.54],'roughness':.89},BRICK:{'color':[.27,.15,.115],'roughness':.92},
        GLASS:{'color':[.112,.180,.189],'alpha':.60,'roughness':.20},BLOCK:{'color':[.33,.38,.36],'alpha':.81,'roughness':.46},
        IRON:{'color':[.60,.57,.51],'roughness':.60,'metallic':.15},STONE:{'color':[.34,.32,.29],'roughness':.91},
        ROOF:{'color':[.34,.16,.112],'roughness':.85},GUTTER:{'color':[.099,.082,.071],'roughness':.81},
        RECESS:{'color':[.115,.108,.084],'roughness':.90}}
PARAM=json.loads((HERE.parent/'measurements/garden-registration.json').read_bytes())['parameters']
META={'id':ID,'name':'新华路329弄36号双层圆形住宅庭院立面','official_id':'3M014','heritage_id':'sh-historic-b3-112','address':'上海市长宁区新华路329弄36号','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://www.shcn.gov.cn/col7343/20241227/1275366.html','photo_source':'https://www.meet-in-shanghai.net/en/guide/xinhua-road-a-witness-to-urban-life-development-over-past-century-160847/','viewer_page':'xinhua-329-no36-cake-villa.html','camera_views':json.loads((HERE/'cameras.json').read_bytes()),'scope':'Garden-facing sector of the round house. Central garden door, two fields of glass blocks, recessed three-bay balcony, brick flanks and visible radial roof slopes. Rear rooms and internal fountain are outside the observed sector. Neither photograph has a documented exposure date.'}

def face_axes(i):
    a=i*PARAM['bay_angle'];r=PARAM['radius']
    tangent=np.array([math.cos(a),math.sin(a),0]);inside=np.array([-math.sin(a),math.cos(a),0])
    centre=np.array([r*math.sin(a),r*(1-math.cos(a)),0])
    def xyz(u,z,d):return centre+tangent*u-inside*d+[0,0,z]
    return tangent,inside,xyz

def facade(b,i,lod):
    tan,inside,xyz=face_axes(i);p=PARAM
    h=p['radius']*math.tan(p['bay_angle']/2);mid=p['balcony_floor'];head=p['opening_top'];crown=p['upper_opening_top']
    tag=f'garden bay {i:+d}'
    def bar(name,u0,u1,z0,z1,d0,d1,mat):
        b.box(xyz((u0+u1)/2,(z0+z1)/2,(d0+d1)/2),[u1-u0,d1-d0,z1-z0],mat,basis=[tan,inside,[0,0,1]],label=tag+' / '+name)
    def sheet(name,holes,z0,z1,d0,d1,mat):
        poly=rectangle(-h,z0,h,z1)
        for hole in holes:poly=poly.difference(rectangle(*hole))
        b.prism(poly,d0,d1,xyz,mat,tag+' / '+name)
    central=abs(i)<=1
    brick=abs(i)==2
    width=p['door_width'] if i==0 else p['block_window_width'] if central else 1.24
    bottom=p['door_sill']if i==0 else p['block_sill'] if central else .86
    if brick:
        sheet('brick floor fields',[],.14,6.41,-.26,-.035,BRICK)
        bar('pale waist',-h,h,mid-.37,mid-.06,-.03,.018,PLASTER)
        return
    if central or abs(i) in (3,4):
        lower_open=(-width/2,bottom,width/2,head)
        sheet('lower pierced frame',[lower_open],.13,mid-.22,-.27,0,PLASTER)
        glazed_blocks=abs(i)==1
        if glazed_blocks:
            bar('glass-block field',-width/2+.012,width/2-.012,bottom+.012,head-.012,-.14,-.115,BLOCK)
            cols,rows=(8,13)
            for k in range(1,cols): 
                u=width*(k/cols-.5);bar('vertical glass block joint '+str(k),u-.011,u+.011,bottom,head,-.112,-.093,IRON)
            for k in range(1,rows):
                z=bottom+(head-bottom)*k/rows;bar('horizontal glass block joint '+str(k),-width/2,width/2,z-.012,z+.012,-.111,-.094,IRON)
        else:
            bar('recessed steel and glass filling',-width/2+.012,width/2-.012,bottom+.012,head-.012,-.17,-.143,GLASS)
            zlist=[bottom+.032,head-.030,p['door_transom'],bottom+.90]if i==0 else [bottom+.025,head-.025,bottom+.55*(head-bottom)]
            for k,z in enumerate(zlist):bar('horizontal sash '+str(k),-width/2,width/2,z-.027,z+.027,-.14,-.097,IRON)
            for k,u in enumerate([-width/2+.023,0,width/2-.023]):bar('vertical sash '+str(k),u-.024,u+.024,bottom,head,-.141,-.097,IRON)
            bar('shaded window return',-width/2,width/2,bottom,head,-.49,-.45,RECESS)
        upper_width=width+.024 if central else width
        upper_base=mid if central else mid+.40
        sheet('upper opening with full reveals',[(-upper_width/2,upper_base,upper_width/2,crown)],mid-.218,6.41,-.28,0,PLASTER)
        if central:
            bar('balcony deck',-h,h,mid-.16,mid,-1.13,-.13,STONE)
            bar('gallery inner shade',-h,h,mid,crown,-1.35,-1.31,RECESS)
            bar('recessed upper garden glazing',-upper_width*.43,upper_width*.43,mid+.06,crown-.15,-1.29,-1.26,GLASS)
            for k,u in enumerate([-.42*upper_width,0,.42*upper_width]):
                bar('rear frame '+str(k),u-.026,u+.026,mid+.06,crown-.15,-1.25,-1.22,IRON)
            bar('balcony foot',-upper_width/2,upper_width/2,mid,mid+.075,-.033,.030,STONE)
            zrail=p['rail_top']
            bar('guard rail',-upper_width/2,upper_width/2,zrail-.032,zrail+.032,-.039,.028,IRON)
            count=8 if i==0 else 6
            for k in range(count+1):
                u=(k/count-.5)*(upper_width-.06);bar('guard post '+str(k),u-.017,u+.017,mid+.072,zrail-.02,-.028,.010,IRON)
        else:
            bar('high return window',-width/2,width/2,upper_base,crown,-.15,-.123,GLASS)
            for k,u in enumerate([-width/2+.02,0,width/2-.02]):bar('upper return window stile '+str(k),u-.018,u+.018,upper_base,crown,-.122,-.094,IRON)
            bar('upper return dividing rail',-width/2,width/2,upper_base+.62,upper_base+.653,-.122,-.094,IRON)
            bar('rear of return light',-width/2,width/2,upper_base,crown,-.36,-.33,RECESS)
    else:
        sheet('outer visible pier',[],.14,6.41,-.28,0,PLASTER)

def roof_section(b,lod):
    r=PARAM['radius'];ang=PARAM['bay_angle'];segments=12 if lod else 30
    lo,hi=-5.5*ang,5.5*ang;aa=np.linspace(lo,hi,segments+1)
    def point(a,rad,z):return [rad*math.sin(a),r-rad*math.cos(a),z]
    def ring(name,inner,outer,zinner,zouter,thick,mat):
        points=[]
        for a in aa:points.extend([point(a,inner,zinner-thick),point(a,outer,zouter-thick),point(a,inner,zinner),point(a,outer,zouter)])
        faces=[]
        for i in range(segments):
            k=i*4;faces.extend([(k,k+4,k+5,k+1),(k+2,k+3,k+7,k+6),(k+1,k+5,k+7,k+3),(k,k+2,k+6,k+4)])
        faces.extend([(0,1,3,2),(4*segments,4*segments+2,4*segments+3,4*segments+1)])
        b.add(points,faces,mat,name)
    ring('garden sector / clay roof',.18,r+.46,8.75,6.54,.10,ROOF)
    ring('garden sector / deep eaves soffit',r-.27,r+.45,6.455,6.455,.085,PLASTER)
    ring('garden sector / outside gutter',r+.41,r+.48,6.565,6.565,.11,GUTTER)
    for k in range(-5,6,2):
        a=k*ang;b.tube([point(a,.19,8.77),point(a,r+.44,6.565)],.034,ROOF,6 if lod else 9,'garden roof / hip tile '+str(k))

def add_building(b,lod=False):
    for i in range(-5,6):facade(b,i,lod)
    roof_section(b,lod)
    rise=PARAM['door_sill']/3
    for k in range(3):
        width=2.30+(2-k)*.18;front=-.92+k*.278;back=front+.28 if k<2 else .17
        b.box([0,(front+back)/2,(k+1)*rise/2],[width,back-front,(k+1)*rise],STONE,label='entrance / garden step '+str(k+1))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--lod',action='store_true');a=ap.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);b.save(a.output,META)
if __name__=='__main__':main()
