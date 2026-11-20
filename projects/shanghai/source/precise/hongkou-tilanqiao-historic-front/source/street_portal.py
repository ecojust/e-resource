"""Street elevation in the January 2015 photographs. The section ends at the decorative façade."""
from math import cos, pi
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Polygon, box

from photo_architecture import Facade
from sign_lettering import lettering_shapes

WIDTH = 17.6
HEIGHT = 10.0
FONT = Path(__file__).parent/'fonts/PlaqueSubset.otf'
PALETTE = {
    'weathered limestone': {'color':[.54,.493,.411],'roughness':.94},
    'honed buff stone': {'color':[.655,.602,.509],'roughness':.86},
    'pale arris': {'color':[.709,.661,.566],'roughness':.84},
    'darkened stone': {'color':[.414,.379,.323],'roughness':.92},
    'mortar': {'color':[.301,.245,.205],'roughness':.98},
    'brown brick': {'color':[.355,.213,.168],'roughness':.94},
    'red brick': {'color':[.433,.223,.165],'roughness':.93},
    'russet brick': {'color':[.399,.248,.194],'roughness':.93},
    'dark panel': {'color':[.108,.118,.116],'roughness':.82},
    'panel edge': {'color':[.15,.159,.145],'roughness':.76},
    'plaque porcelain': {'color':[.91,.89,.829],'roughness':.63},
    'plaque lettering': {'color':[.113,.105,.095],'roughness':.78},
    'pale marker': {'color':[.666,.69,.645],'roughness':.82},
    'relief bronze': {'color':[.278,.245,.175],'roughness':.79},
    'section': {'color':[.48,.461,.425],'roughness':1.0},
}
def panel(f,x0,x1,z0,z1,front,back,material,label):
    f.box((x0+x1)/2,(z0+z1)/2,x1-x0,z1-z0,front-back,(front+back)/2,material,label)

def surround(f,outer,inner,height,inner_height,front,back,mat,label):
    outline=box(-outer,0,outer,height).difference(box(-inner,-.1,inner,inner_height))
    f.prism(outline,back,front,mat,label)

def fluted_edge(b,side,lod):
    # Continuous grooved plan profile rather than dark strips pasted on the pier.
    x0,x1=6.72,8.71;cuts=[(6.95,.093,.13),(7.15,.105,.12),(8.14,.12,.14),(8.38,.10,.12),(8.59,.071,.10)]
    pts=[(x0,-.34)]
    for center,r,depth in cuts:
        for j in range(5 if lod else 9):
            t=j/(4 if lod else 8);pts.append((center+(2*t-1)*r,-.34+depth*(1-cos(2*pi*t))*.5))
    pts.extend([(x1,-.34),(x1,.77),(x0,.77)])
    shape=Polygon([(side*x,y)for x,y in pts])
    b.prism(shape,1.48,HEIGHT,lambda x,y,z:(x,y,z),'weathered limestone','Edge piers/continuous fluted stone profiles')
    for i in range(4):
        z0=1.48*i/4;z1=z0+1.48/4-.014
        b.box((side*7.74,.18,(z0+z1)/2),(2.065,1.13,z1-z0),'honed buff stone',label='Edge piers/bonded plinth blocks')
    b.box((side*7.75,-.008,1.49),(2.04,.72,.075),'darkened stone',label='Edge piers/neck of base')
    b.box((side*8.73,.29,4.98),(.14,.97,9.96),'darkened stone',label='Edge piers/outer side return')

def brick_row(f,left,right,bottom,height,depth,index,lod,label):
    width=.51 if lod else .263
    stride=width+.012;start=left-stride*(index%2)*.5;k=0
    while start<right-.015:
        lo=max(left,start);hi=min(right,start+width)
        if hi-lo>.02:
            mat=('red brick','brown brick','russet brick')[(k*7+index*17+k//5)%3]
            panel(f,lo,hi,bottom,bottom+height,depth+.025,depth,mat,label)
        start+=stride;k+=1

def side_pier(f,s,lod):
    tag='Right pier' if s>0 else 'Left pier'
    a,b=sorted([4.15*s,6.72*s]);x=s*5.60
    shape=box(a,.02,b,7.13)
    if s>0:
        small=Polygon([(4.97,0),(5.98,0),(5.98,2.46),(5.80,2.61),(5.34,2.61),(4.97,2.44)])
        shape=shape.difference(small)
        panel(f,4.99,5.97,.01,2.63,-.62,-.78,'dark panel',tag+'/opaque inset field')
    f.prism(shape,-.87,-.19,'honed buff stone',tag+'/field stone')
    for j in range(3):
        z=(j+1)*.46
        for left,right in ([(a,4.965),(5.985,b)] if s>0 else [(a,b)]):
            panel(f,left,right,z,z+.013,-.182,-.20,'darkened stone',tag+'/plinth joints')
    for k in range(6):
        x0=x+(k-2.5)*.087
        panel(f,x0-.011,x0+.011,3.27+.030*abs(k-2.5),6.80-.02*abs(k-2.5),-.166,-.20,'darkened stone',tag+'/linear relief')
    for k in range(5):
        z=4.48+k*.24
        shape=Polygon([(x-.139,z),(x-.06,z+.08),(x,z+.22),(x+.06,z+.08),(x+.139,z),(x+.048,z-.025),(x,z+.031),(x-.048,z-.025)])
        f.prism(shape,-.15,-.082,'relief bronze',tag+'/stepped geometric ornament')
    if s<0:
        panel(f,x-.28,x+.28,2.25,2.73,-.118,-.181,'pale marker',tag+'/small commemorative tablet')
    else:
        panel(f,7.32,7.83,2.63,6.25,.428,.33,'plaque porcelain','2015 vertical name tablet/ceramic face')
        for i,char in enumerate('上海市提篮桥监狱'):
            for _,outline in lettering_shapes(char,.388,.376,font=FONT):
                f.prism(translate(outline,xoff=7.575,yoff=6.00-i*.437),.427,.440,'plaque lettering','2015 vertical name tablet/inscription')

def brick_face(f,lod):
    # Successive rectangular red-brick returns follow the narrower stone centre frame.
    surround(f,4.20,2.59,7.08,5.00,-.43,-.97,'mortar','Brick surround/joints')
    count=27 if lod else 55;hz=6.89/count
    for i in range(count):
        z=.14+i*hz
        for left,right in ([(-4.18,-2.64),(2.64,4.18)] if z<5.15 else [(-4.18,4.18)]):
            brick_row(f,left,right,z,hz-.012,-.428,i,lod,'Brick surround/stretcher courses')
    for k in range(5):
        # Each U-shaped band steps forward toward the perimeter. Its corner joints turn through 90 degrees.
        x=2.63+k*.26;h=5.14+k*.285;depth=-.403+k*.026
        ring=box(-x-.071,1.48,x+.071,h+.093).difference(box(-x,1.47,x,h))
        f.prism(ring,-.457,depth,'brown brick','Brick surround/projecting nested brick frames')
        spans=round(2*x/(.28 if lod else .14))
        for j in range(spans):
            x0=-x+j*2*x/spans
            panel(f,x0+.008,x0+2*x/spans-.006,h+.009,h+.094,depth+.013,depth,'russet brick','Brick surround/radial header joints')
    # The red-brick fields stop on the broad stone plinth visible in both dates.
    for side in [-1,1]:
        left,right=sorted([2.61*side,4.21*side])
        for j in range(3):
            panel(f,left,right,.006+j*.491,(j+1)*.491-.006,-.28,-.92,'honed buff stone','Brick surround/stone base courses')
        panel(f,left,right,1.462,1.50,-.259,-.92,'weathered limestone','Brick surround/plinth sill')
    surround(f,2.65,2.12,5.16,4.59,-.461,-.91,'honed buff stone','Central recess/dressed stone liner')
    surround(f,2.19,2.12,4.67,4.59,-.448,-.47,'pale arris','Central recess/inner return')
    panel(f,-2.13,2.13,.01,4.61,-.864,-.98,'dark panel','Central recess/closed painted face')
    for x0,x1 in [(-2.10,-.018),(.018,2.10)]:
        for j in range(4):
            panel(f,x0+.027,x1-.027,.10+1.10*j,1.16+1.1*j,-.847,-.875,'dark panel','Central recess/subtle panel fields')
    panel(f,-.018,.018,.03,4.58,-.839,-.875,'panel edge','Central recess/vertical joint')

def add_front(b,lod):
    f=Facade(b,(-WIDTH/2,0),(WIDTH/2,0),'Street')
    panel(f,-8.77,8.77,.01,9.78,-1.16,-1.31,'section','Section/plain backing')
    for s in [-1,1]:
        fluted_edge(b,s,lod);side_pier(f,s,lod)
    brick_face(f,lod)
    # The sill of the monumental header projects in front of the recessed stone fields.
    for z0,z1,front,mat,label in [
        (7.05,7.23,.02,'darkened stone','shadowed soffit'),(7.19,7.40,.195,'honed buff stone','lower fillet'),
        (7.36,7.48,.285,'pale arris','projecting lower bead'),(7.45,7.58,.24,'darkened stone','recessed bed'),
        (7.57,8.71,.21,'weathered limestone','long weathered inscription bed'),
        (8.70,8.84,.265,'pale arris','stepped stone band'),(8.82,9.14,.178,'weathered limestone','upper stone band'),
        (9.13,9.32,.22,'honed buff stone','stone coping')]:
        panel(f,-6.76,6.76,z0,z1,front,-1.15,mat,'Header/'+label)
    panel(f,-6.77,6.77,9.31,9.71,.08,-1.155,'mortar','Header/frieze joint bed')
    n=83 if lod else 151
    for i in range(n):
        l=-6.76+i*13.52/n
        panel(f,l+.008,l+13.52/n-.008,9.33,9.705,.118,.079,'brown brick' if i%3 else 'russet brick','Header/upright brick frieze')
    for i in range(5):
        x0=-6.74+i*13.48/5;panel(f,x0+.01,x0+13.48/5-.012,9.713,9.785,.092,-1.16,'weathered limestone','Header/capping slabs')
    b.box((0,.59,9.84),(13.44,1.10,.12),'section',label='Section/top return')
