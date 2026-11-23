"""Build the reconstructed timber gate inside Fudan University's Handan campus."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box as rect,Point
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from gate_roofs import lifted_roof,TILE,NOSE,TIMBER,DARK
ID='yangpu-fudan-old-gate-timber-paifang'
WALL='Fudan | white lime render';BASE='Fudan | cut grey stone';EDGE='Fudan | light edge stone';GATE='Fudan | reddish wooden gate';BOARD='Fudan | black lacquer';GOLD='Fudan | gold brush lettering'
def mat(rgb):return dict(color=rgb,roughness=.83)
PALETTE={TILE:mat([.073,.083,.086]),NOSE:mat([.107,.123,.127]),TIMBER:mat([.345,.153,.060]),DARK:mat([.123,.072,.042]),WALL:mat([.82,.805,.755]),BASE:mat([.385,.366,.354]),EDGE:mat([.60,.566,.519]),GATE:mat([.23,.082,.048]),BOARD:mat([.045,.037,.032]),GOLD:dict(color=[.55,.396,.173],roughness=.50,metallic=.30)}
G=json.loads((HERE.parent/'measurements/registered-gate.json').read_bytes())['geometry']
META=dict(id=ID,name='复旦大学邯郸校区老校门',heritage_id='sh-historic-b4-174',official_id='4G008',address='邯郸路220号校内燕园西侧',viewer_page='fudan-old-gate-timber-paifang.html',geometry_license='MIT',texture_license='MIT',photos_embedded=False,photo_source='https://commons.wikimedia.org/wiki/File:Fudan-building3.jpg',scope='The 2004 reconstructed gate: the three timber openings, inward-facing historic motto location, tiled eaves and roof ornaments, white flanking walls, wood plaques and central stepped approach. No reconstruction of the lost 1921 fabric or the modern street gate.')
def block(b,label,m,x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=label)
def xz(b,poly,y0,y1,matl,label):
    b.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),matl,label)
def gate_leaf(b,label,x0,x1,base,high,lod,center,side):
    z0=base+.045;y=.09;n=6 if side else 7
    for z in (z0+.105,z0+.63):
        block(b,label+'/lower rail',GATE,x0,x1,y-.067,y+.035,z-.047,z+.047)
    def ztop(x):
        local=(x-x0)/(x1-x0);peak=1-local if center>0 else local
        return high+(.0 if side else .17*peak**1.5)+.05*math.sin(math.pi*local)
    for i,x in enumerate(np.linspace(x0+.055,x1-.055,n)):
        top=ztop(x);dx=.034 if i not in (0,n-1)else .049
        poly=Polygon([(x-dx,z0),(x+dx,z0),(x+dx,top+.14),(x,top+.215),(x-dx,top+.14)])
        xz(b,poly,y-.030,y+.047,GATE,label+'/headed vertical slat '+str(i+1))
    xx=np.linspace(x0,x1,6 if lod else 12);xy=[(x,ztop(x))for x in xx]
    xz(b,Polygon(xy+[(x,z-.125)for x,z in xy[::-1]]),y-.083,y+.018,GATE,label+'/curved top rail')
def add_building(b,lod=False,inscribed=True):
    a=G['outer_post_x'];h=G['inner_post_x'];z0=G['threshold_z'];lintel=G['beam_bottom'];beam_top=G['beam_top']
    for index,x in enumerate((-a,-h,h,a)):
        dx=.109 if index in (1,2)else .112
        block(b,'gate frame / upright '+str(index+1),TIMBER,x-dx,x+dx,-.105,.142,z0,4.07)
    block(b,'gate frame / deep timber lintel',TIMBER,-a-.09,a+.09,-.100,.224,lintel,beam_top)
    for z in (lintel+.05,beam_top-.07):
        block(b,'gate frame / horizontal moulding',DARK,-a-.103,a+.103,-.137,.231,z-.024,z+.024)
    for face_y,name in [(-.149,'university name'),(.268,'courtyard motto')]:
        block(b,name+' plaque / lacquer field',BOARD,-G['plaque_half_x'],G['plaque_half_x'],face_y-.044,face_y+.044,G['plaque_bottom'],G['plaque_top'])
    add_letters=HERE.parent/'measurements/inscription-contours.json'
    if inscribed and add_letters.is_file():
        from gate_letters import add_letters_to_gate
        add_letters_to_gate(b,G)
    gateheight=1.86
    for i,(left,right) in enumerate([(-a+.11,-h-.11),(-h+.11,-.005),(.005,h-.11),(h+.11,a-.11)]):
        gate_leaf(b,'wooden leaves '+str(i+1),left,right,z0,gateheight,lod,(left+right)/2,i in (0,3))
    disk=Point(0,z0+.77).buffer(.31,quad_segs=11 if lod else 24)
    xz(b,disk,-.095,-.031,GATE,'central meeting / circular timber medallion')
    xz(b,disk.difference(disk.buffer(-.032)),-.11,-.093,DARK,'central meeting / raised roundel rim')
    for x in (-1,1):
        left=x*(a+.03);right=x*(a+1.54);lo,hi=sorted((left,right));y0=-.04;y1=.38
        block(b,'flanking wall / raised grey plinth',BASE,lo-.068,hi+.068,y0-.07,y1+.07,0,z0+.53)
        block(b,'flanking wall / chamfered plinth cap',EDGE,lo-.083,hi+.083,y0-.093,y1+.093,z0+.50,z0+.594)
        block(b,'flanking wall / white plaster field',WALL,lo,hi,y0,y1,z0+.58,3.15)
        for yy in (y0-.031,y1+.031):
            panel=rect(lo+.105,z0+.78,hi-.105,2.77)
            xz(b,panel.difference(panel.buffer(-.038,join_style=2)),yy-.018,yy+.018,EDGE,'flanking wall / moulded inset reveal')
        lifted_roof(b,(lo+hi)/2,hi-lo+.28,1.12,.17,3.00,3.38,3.43,lod,'flanking wall / hipped boundary cap',small=True)
    # Three distinct stair noses are visible on the high-resolution ground photograph.
    t=G['step_half_x'];front=G['step_foot_y']
    for i in range(3):
        y0=front+(0-front)*i/3
        block(b,'entry / stone tread '+str(i+1),EDGE,-t,t,y0,.385,0,z0*(i+1)/3)
    for side in (-1,1):
        lo,hi=sorted([side*(t+.006),side*(a+.04)])
        slope=Polygon([(front,0),(.39,0),(.39,z0),(0,z0)])
        b.prism(slope,lo,hi,lambda y,z,x:(x,y,z),BASE,'entry / inclined stone shoulder')
    front=G['front_eave_y'];rear=G['rear_beak_y'];mid=(front+rear)/2
    for y in (-.12,.24):
        for z in (3.64,3.79):
            block(b,'upper frame / supporting rail',DARK,-a-.19,a+.19,y-.063,y+.063,z,z+.10)
    for x in np.linspace(-2.8,2.8,15 if not lod else 9):
        b.tube([[x,-.14,3.83],[x,front+.10,3.91]],.045,DARK,6 if lod else 10,'upper roof / exposed rafter ends')
    for x in (-a,-h,h,a):
        poly=Polygon([(x-.20,3.56),(x+.20,3.56),(x+.27,3.71),(x+.46,3.76),(x+.46,3.86),(x-.46,3.86),(x-.46,3.76),(x-.27,3.71)])
        xz(b,poly,-.18,.27,TIMBER,'upper frame / bracket head')
    lifted_roof(b,0,8.10,rear-front,mid,3.845,G['ridge_z'],G['roof_tip_z'],lod,'main gate roof',ridge_y=G['ridge_y'])
def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true');args=cli.parse_args()
    b=Builder(PALETTE);add_building(b,args.lod);stats=b.save(args.output,META);print(stats['sha256'],stats['parts'],stats['triangles'])
if __name__=='__main__':main()
