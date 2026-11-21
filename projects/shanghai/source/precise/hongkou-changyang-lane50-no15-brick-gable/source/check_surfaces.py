"""First surface reached on the independently decoded raw, near, and far facades."""
import os,runpy
from pathlib import Path
from math import pi,cos,sin
from brick_gable import *
root=Path(os.environ['SHANGHAI_PROJECT_ROOT']) if 'SHANGHAI_PROJECT_ROOT'in os.environ else Path(__file__).resolve().parents[4]
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def probe(label,origin,direction,wanted,start,end):
        h=reader.ray(origin,direction,3.3)
        passed=(h is None)if not wanted else bool(h and h['material']in wanted and start<=h['distance_m']<=end)
        rows.append(dict(part=label,origin=origin,direction=direction,expected=wanted,min_m=start,max_m=end,hit=h,passed=passed))
    def front(label,x,z,material,start,end):
        probe(label,[x,-1,z],[0,1,0],material,start,end)
    for side in (-1,1):
        for z in (1.14,1.68,2.16):front('Segment of front brick pier',side*1.357,z,[*BRICKS,MORTAR],.98,1.01)
        for z in (3.51,4.03,4.52):front('Upper lateral brick face',side*1.334,z,[*BRICKS,MORTAR],.98,1.01)
        for z in (.93,1.94):front('Lower opening lined with brick',side*1.044,z,[SHADOW],.91,.95)
        for z in (3.61,4.08,4.56):front('Window jamb returns',side*.899,z,[SHADOW],.92,.98)
        front('Arched upper fixed light',side*.31,5.03,[GLASS],1.12,1.18)
    for x,z in ((-.42,3.82),(-.50,4.30)):
        front('Fixed lower left glazing',x,z,[GLASS],1.12,1.18)
    for x,z in ((.42,3.82),(.50,4.30),(.32,4.05),(.61,4.56)):
        d=1.107+(x-.738)*.6494
        front('Forward glass of open right leaf',x,z,[GLASS],d-.014,d+.014)
    for z in (3.65,4.16,4.61):
        front('Projecting free stile of open leaf',.169,z,[WOOD],.69,.77)
        front('Shadow in gap beside open leaf',.085,z,[DIM],1.25,1.29)
    for side in (-1,1):
        front('Top-light rail',side*.26,4.868,[WOOD],1.04,1.10)
    for z in (3.68,4.04,4.53,5.17):front('Casement or top-light centre upright',0,z,[WOOD],1.035,1.105)
    for spring,span,rise,band in ((2.67,.92,.34,.145),(4.91,.79,.42,.15)):
        for degree in (12,28,48,69,102,132,155,173):
            a=degree*pi/180
            front('Radially laid brick voussoir',(span+band*.5)*cos(a),spring+(rise+band*.5)*sin(a),[RUBBED],.869,.908)
    for degree in (9,41,71,103,142,172,203,231,262,294,322,352):
        a=degree*pi/180
        front('Outer ring of circular gable medallion',.35*cos(a),5.998+.35*sin(a),[RUBBED],.827,.854)
        front('Individual spoke in circle',.217*cos(a),5.998+.217*sin(a),BRICKS,.833,.869)
    for j in range(8):
        a=2*pi*(j+.43)/8
        front('Raised outer roundel key',.291*cos(a),5.998+.291*sin(a),BRICKS,.770,.793)
    for sign in (-1,1):
        for z in (1.25,1.75,2.32):
            probe('Inner side return from the covered porch',[sign*.46,.56,z],[sign,0,0],[SHADOW],.448,.472)
    front('Dark central inset of medallion',0,5.998,[SHADOW],.895,.925)
    for sign in (-1,1):
        for i in range(8):front('Stepped binding below gable coping',sign*(i+.5)*.189,6.68-i*.102,[RUBBED],.83,.885)
    for z in (1.2,1.61,2.05,2.41):
        front('Set-back dark entrance leaf',-.07,z,[DARK],1.6,1.81)
    for x,z in [(-.45,2.72),(0,2.83),(.35,2.75)]:
        front('Shaded area under the porch vault',x,z,[DIM],1.82,1.88)
    front('Green sign for actual No. 15',1.037,2.081,[GREEN],.841,.870)
    front('White vertical stroke of numeral one',.994,2.051,[WHITE],.840,.857)
    front('White numeral five upper stroke',1.097,2.087,[WHITE],.840,.857)
    for i in range(3):
        for x in (-.70,-.27,.36,.76):
            probe('Stone entrance tread '+str(i+1),[x,-.930+.32*i,1],[0,0,-1],[STONE],1-(i+1)*.142-.012,1-(i+1)*.142+.012)
    for i in range(3):
        probe('Vertical front of stone riser '+str(i+1),[.225,-1.65,(i+1)*.142-.080],[0,1,0],[RISER],.544+.32*i,.565+.32*i)
        probe('Stone nosing of step '+str(i+1),[.225,-1.65,(i+1)*.142-.012],[0,1,0],[STONE],.543+.32*i,.562+.32*i)
    front('Open air beyond the gable shoulder',1.412,6.87,[],0,0)
    return dict(samples=rows,passed=all(s['passed']for s in rows))
