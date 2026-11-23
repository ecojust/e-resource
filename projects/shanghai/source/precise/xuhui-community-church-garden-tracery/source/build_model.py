"""Build the seven-light street gable of Shanghai Community Church from measured openings."""
import argparse,math,json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,LineString,box as rect
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
ID='xuhui-community-church-garden-tracery'
BRICK='Community Church | weathered russet brick';STONE='Community Church | buff window stone';GLASS='Community Church | smoky leaded glass'
IRON='Community Church | dark lead';ROOF='Community Church | grey tile';DARK='Community Church | door recess';STEPS='Community Church | stair stone'
PALETTE={BRICK:{'color':[.36,.15,.086],'roughness':.91},STONE:{'color':[.48,.412,.326],'roughness':.84},GLASS:{'color':[.19,.213,.198],'alpha':.69,'roughness':.35},
         IRON:{'color':[.085,.081,.070],'metallic':.28,'roughness':.65},ROOF:{'color':[.178,.17,.153],'roughness':.91},DARK:{'color':[.095,.071,.047],'roughness':.88},STEPS:{'color':[.32,.30,.27],'roughness':.9}}
BOOK=json.loads((HERE.parent/'measurements/church-registration.json').read_bytes());G=BOOK['parameters'];A=BOOK['survey']
META={'id':ID,'name':'国际礼拜堂临衡山路七扇尖窗山墙','heritage_id':'sh-historic-b1-028','official_id':'1D002','address':'上海市徐汇区衡山路，房管局名录登记58号，教堂简介用53号','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://www.ccctspm.org/churchinfo/199','photo_source':'https://commons.wikimedia.org/wiki/Category:Shanghai_Community_Church','viewer_page':'community-church-garden-tracery.html','camera_views':json.loads((HERE/'cameras.json').read_bytes()),'scope':'Street-facing high brick gable, seven lights, tracery, buttresses and a short roof section. The low entrance profile is taken from the landscape project historical comparison. The adjoining court, residential wing and modern fence are outside the model.'}
def xyz(u,z,d):return (u,-d,z)
def archpath(a,spring,top,n):
    h=top-spring;offset=(h*h-a*a)/(2*a);radius=offset+a
    result=[]
    for x in np.linspace(-a,a,n):
        z=spring+math.sqrt(max(0,radius*radius-(abs(x)+offset)**2))
        result.append((float(x),z))
    return result
def arched(a,bottom,spring,top,n):return Polygon([(-a,bottom),(a,bottom),*reversed(archpath(a,spring,top,n))])
def strip(b,name,shape,back,front,mat):
    b.prism(shape,back,front,xyz,mat,name)
def rectangle(b,name,x0,x1,y0,y1,z0,z1,mat):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],mat,label=name)
def add_building(b,lod=False):
    n=21 if lod else 43;pitch=G['light_pitch'];a=pitch*3.5;tip=G['opening_peak_z'];spring=G['outside_arch_z']-.69;bottom=5.35
    face=G['window_plane_y'];half=A['width_between_caps']/2;shoulder=A['cap_z']-.65;peak=A['peak_z']
    opening=arched(a,bottom,spring,tip,n);outer=opening.buffer(.31,join_style='round',quad_segs=4)
    def door(w,z):
        points=[(-w,.25),(w,.25),(w,z-.32),(.76*w,z-.08),(0,z),(-.76*w,z-.08),(-w,z-.32)]
        return Polygon(points)
    portal=door(1.39,3.59)
    body=Polygon([(-half,.10),(half,.10),(half,shoulder),(.105,peak),(-.105,peak),(-half,shoulder)])
    strip(b,'street gable / brick wall and continuous openings',body.difference(outer).difference(portal),-1.16,-face,BRICK)
    strip(b,'pointed arch / outer stone surround',outer.difference(opening),-1.16,-face+.13,STONE)
    inner=opening.buffer(-.059,join_style='round');strip(b,'pointed arch / recessed bevel',opening.difference(inner),-face-.10,-face+.060,STONE)
    strip(b,'seven lights / translucent glazing',inner,-face-.162,-face-.142,GLASS)
    web=[]
    for i in range(1,7):
        x=(i-3.5)*pitch
        web.append(rect(x-.041,bottom,x+.041,tip+.08))
    heights=[G['outside_arch_z'],G['paired_arch_z'],G['paired_arch_z'],G['central_arch_z'],G['paired_arch_z'],G['paired_arch_z'],G['outside_arch_z']]
    for i,z in enumerate(heights):
        x=(i-3)*pitch
        crown=[(x+u,v)for u,v in archpath(pitch/2,z-.23,z,n)]
        web.append(LineString(crown).buffer(.052,cap_style='flat'))
    for x in [-pitch,pitch]:
        z=G['oculus_center_z'];w=pitch*.42;h=.465
        ring=[]
        for t in np.linspace(0,math.tau,26 if lod else 50,endpoint=False):
            ring.append((x+w*math.cos(t),z+h*math.sin(t)*(1-.18*abs(math.cos(t)))))
        web.append(LineString(ring+[ring[0]]).buffer(.049,join_style='round'))
        for sign in [-1,1]:web.append(rect(x+sign*pitch*.24-.026,z+.23,x+sign*pitch*.24+.026,tip))
    strip(b,'seven lights / mullions, crowns and paired cusps',unary_union(web).intersection(inner),-face-.122,-face+.004,STONE)
    rectangle(b,'window / projecting lower sill',-a-.23,a+.23,face-.26,face+.31,bottom-.16,bottom-.015,STONE)
    for side in [-1,1]:
        x=side*half;name=('left'if side<0 else 'right')+' buttress'
        # Two shallow set-offs form the stepped front seen below the cap on oblique photographs.
        for j,(z0,z1,w,front)in enumerate([(.10,5.13,.78,-.32),(5.13,9.56,.69,-.18),(9.56,A['cap_z']-.19,.61,-.07)]):
            rectangle(b,name+' / brick stage '+str(j+1),x-w/2,x+w/2,front,1.00,z0,z1,BRICK)
        rectangle(b,name+' / stone coping',x-.338,x+.338,-.103,1.03,A['cap_z']-.19,A['cap_z'],STONE)
    # Historic comparison shows the shallow rectangular entrance hood below the sill.
    strip(b,'historical doorway / masonry hood',door(1.68,3.83).difference(portal),-face+.015,.49,STONE)
    rectangle(b,'historical doorway / dark recessed door',-1.37,1.37,1.48,1.54,.24,3.31,DARK)
    for i in range(2):
        front=-.87+i*.34;back=front+.35 if i==0 else face+.13
        rectangle(b,'historical doorway / step '+str(i+1),-1.80+i*.12,1.80-i*.12,front,back,0,.12*(i+1),STEPS)
    for side in [-1,1]:
        f=side;points=[(0,peak-.09),(f*(half+.10),shoulder-.10),(f*(half+.10),shoulder-.27),(0,peak-.26)]
        strip(b,('left' if side<0 else 'right')+' / short return roof slope',Polygon(points),-3.82,-1.08,ROOF)
        rectangle(b,('left' if side<0 else 'right')+' / first return wall',side*half-.11,side*half+.11,1.05,3.82,.1,shoulder-.24,BRICK)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--lod',action='store_true');args=ap.parse_args()
    b=Builder(PALETTE);add_building(b,args.lod);b.save(args.output,META)
if __name__=='__main__':main()
