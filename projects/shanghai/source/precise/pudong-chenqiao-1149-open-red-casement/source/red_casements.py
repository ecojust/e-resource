"""Old red casements, protected opening and aggregate reveals at 1149 Chenqiao Village."""
from pathlib import Path
import math,numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
ID='pudong-chenqiao-1149-open-red-casement'
PAINT='Peeling red timber';IRON='Dark weathered slender rods';STONE='Green grey aggregate reveal';WALL='Tan scored wall';MOULD='Grey pale mouldings';GLASS='Cloudy grey glazing';DARK='Shaded interior window plane'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in ((PAINT,[1,1,1],.89),(IRON,[.348,.253,.178],.71),(STONE,[1,1,1],.94),(WALL,[1,1,1],.91),(MOULD,[.65,.60,.49],.90),(GLASS,[1,1,1],.33),(DARK,[.137,.121,.101],.93))}
HINGES=[(-.548,-1,math.radians(70)),(.548,1,0.)]
ZB=.315;ZT=1.86
def texture():
    f=Path(__file__).with_name('old-red-paint-grit-and-frosted-glass.png')
    if not f.exists():
        r=np.random.default_rng(891);h,w=320,218;yy,xx=np.indices((h,w))
        field=lambda a,b:np.asarray(Image.fromarray(r.integers(0,255,(a,b),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        grain=field(9,105);broad=field(23,38);peeled=np.clip((broad+.25*grain-13)/43,0,1)
        red=np.array([139,69,61])+(np.array([193,170,143])-np.array([139,69,61]))*peeled[:,:,None]+(.12*grain+r.normal(0,3,(h,w)))[:,:,None]
        pebble=r.normal(0,19,(h,w));stone=np.array([158,158,133])+(pebble+.15*field(43,72))[:,:,None]
        wall=np.array([185,164,133])+(.20*field(14,13)+r.normal(0,3.8,(h,w)))[:,:,None]
        glass=np.array([157,159,143])+(.09*field(8,9)+2.75*np.cos(xx*.019+yy*.006))[:,:,None]
        Image.fromarray(np.concatenate((red,stone,wall,glass),axis=1).clip(0,255).astype('uint8')).quantize(192).save(f)
    for m in (PAINT,STONE,WALL,GLASS):PALETTE[m]['texture']=str(f)
def leaf_point(leaf,s,depth,z):
    hx,side,ang=HINGES[leaf]
    # Positive s measured from the outside hinge toward the centre of a closed sash.
    direction=-side
    return hx+direction*s*math.cos(ang)+direction*depth*math.sin(ang),-.053-s*math.sin(ang)+depth*math.cos(ang),z
def add_building(b,far=False):
    texture()
    def plate(x,y,z,w,d,h,m,n):b.box((x,y,z),(w,d,h),m,label=n)
    hole=box(-.681,.224,.681,1.955)
    surround=box(-.908,.025,.908,2.257).difference(hole)
    b.prism(surround,-.138,.061,lambda x,z,d:(x,-d,z),WALL,'Ochre street wall and broad cut-out')
    for j,z in enumerate((.16,.52,.89,1.26,1.63,2.01)):
        for side in (-1,1):
            plate(side*.793,-.0615,z,.217,.003,.005,MOULD,'Scored horizontal course on street face')
    for side in (-1,1):
        poly=Polygon([(side*.682,.222),(side*.549,.280),(side*.549,ZT+.037),(side*.682,1.955)])
        b.prism(poly,-.142,.063,lambda x,z,d:(x,-d,z),STONE,'Exposed aggregate side of the reveal')
    plate(0,.040,1.906,1.13,.197,.093,STONE,'Recessed aggregate overhead return')
    plate(0,.022,.258,1.40,.337,.082,MOULD,'Projecting pale stone sill')
    for z,d,w,h in ((2.009,.142,1.37,.052),(2.073,.216,1.45,.069),(2.13,.253,1.49,.042),(2.19,.30,1.55,.070)):
        plate(0,-.034,z,w,d,h,MOULD,'Projecting layers above the window hood')
    width=.539
    for leaf in (0,1):
        def frame(s1,s2,z1,z2,d1,d2,material,label):
            pts=[leaf_point(leaf,s,d,z)for z in (z1,z2) for d in (d1,d2)for s in (s1,s2)]
            faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
            if leaf==1:faces=[tuple(reversed(face))for face in faces]
            b.add(pts,faces,material,label)
        frame(.043,width-.044,ZB+.062,ZT-.064,.036,.048,GLASS,'Pane in the opened left or seated right sash')
        for lo,hi in ((0,.046),(width-.047,width)):
            frame(lo,hi,ZB,ZT,-.018,.059,PAINT,'Red vertical stile with worn paint')
        for a,z in ((ZB,ZB+.068),(ZT-.069,ZT)):
            frame(.04,width-.04,a,z,-.018,.058,PAINT,'Wide red end rail')
        for k in (1,2):
            z=ZB+.066+(ZT-ZB-.136)*k/3
            frame(.042,width-.042,z-.012,z+.012,-.006,.042,PAINT,'Single narrow red horizontal glazing bar')
    for x in (-.398,-.242,-.086,.077,.238,.404):
        seg=6 if far else 17;r=.009;pts=[]
        for z in (ZB-.021,ZT+.02):
            for k in range(seg):
                a=k*2*math.pi/seg;pts.append((x+r*math.cos(a),.108+r*math.sin(a),z))
        faces=[(k,(k+1)%seg,seg+(k+1)%seg,seg+k)for k in range(seg)];faces+=[tuple(range(seg-1,-1,-1)),tuple(range(seg,2*seg))]
        b.add(pts,faces,IRON,'Fixed slender rod behind the two window leaves')
    plate(0,.123,1.055,1.10,.035,.035,IRON,'Horizontal tie crossing the fixed rods')
    # A shallow dark plane records the shaded interior visible in the source, behind the unobstructed rods.
    plate(0,.239,1.08,1.12,.022,1.61,DARK,'Shaded plane inside the open window')
    for p in b.parts:
        m=p['material']
        if m not in (PAINT,STONE,WALL,GLASS):continue
        strip=(PAINT,STONE,WALL,GLASS).index(m)
        p['texcoords']=[((strip+.024+.949*min(1,max(0,(x+1.05)/2.1+y*.055)))/4,.983-.948*min(1,max(0,z/2.28))) for x,y,z in p['vertices']]
