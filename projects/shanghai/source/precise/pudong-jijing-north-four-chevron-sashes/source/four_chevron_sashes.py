"""Four dark sashes with paired chevrons on Jijing North Road, Gaoqiao."""
from pathlib import Path
import math,numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,LineString
ID='pudong-jijing-north-four-chevron-sashes'
WALL='Ochre scored street wall';JOINT='Narrow mortar joint';FRAME='Dark brown perimeter and stiles';BAR='Black brown diagonals and rails';GLASS='Dusky pale glass behind diagonal bars';EDGE='Dark outer shutter rim'
PALETTE={m:dict(color=c,roughness=r) for m,c,r in ((WALL,[1,1,1],.92),(JOINT,[.37,.30,.20],.92),(FRAME,[1,1,1],.86),(BAR,[1,1,1],.86),(GLASS,[1,1,1],.31),(EDGE,[.205,.16,.132],.8))}
P=.46
LOW=.31
HIGH=1.92
def texture():
    p=Path(__file__).with_name('ochre-wall-dark-bars-and-glass.png')
    if not p.exists():
        g=np.random.default_rng(895);h,w=220,256;y,x=np.indices((h,w))
        field=lambda hh,ww:np.asarray(Image.fromarray(g.integers(0,255,(hh,ww),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        n=field(20,23)*.11+g.normal(0,3.5,(h,w));brown=np.array([171,141,92])+(n+field(7,8)*.12)[:,:,None]
        timber=np.array([64,51,45])+(n*.75+field(7,w)*.12)[:,:,None]
        glass=np.array([133,125,125])+(4*np.sin(x*.006+y*.032)+field(6,8)*.13+n*.22)[:,:,None]
        Image.fromarray(np.concatenate((brown,timber,glass),axis=1).clip(0,255).astype('uint8')).quantize(160).save(p)
    for m in (WALL,FRAME,BAR,GLASS):PALETTE[m]['texture']=str(p)
def add_building(b,far=False):
    texture()
    def face(p,lo,hi,mat,label):b.prism(p,lo,hi,lambda x,z,d:(x,-d,z),mat,label)
    def board(x,z,w,h,d0,d1,m,n):b.box((x,-(d0+d1)/2,z),(w,d1-d0,h),m,label=n)
    opening=box(-.975,LOW-.09,.975,HIGH+.09)
    # Incised horizontal courses and alternating vertical joints appear in the brown facade.
    frame=box(-1.27,.02,1.27,2.25)
    face(frame.difference(opening),-.24,-.072,JOINT,'Mortar showing only through narrow joints')
    heights=[.0,.36,.78,1.20,1.63,2.04,2.26]
    for j,(a,z) in enumerate(zip(heights,heights[1:])):
        xs=[-1.27,-.62,.48,1.27] if j%2 else [-1.27,-1.03,-.02,1.04,1.27]
        for left,right in zip(xs,xs[1:]):
            geom=box(left+.003,a+.003,right-.003,z-.003).intersection(frame).difference(opening)
            for reg in (list(geom.geoms)if geom.geom_type=='MultiPolygon'else [geom]):
                if not reg.is_empty and reg.area>1e-6:face(reg,-.070,-.046,WALL,'Scored ochre wall around the opening')
    face(opening.difference(box(-.92,LOW,.92,HIGH)),-.145,-.003,FRAME,'Continuous dark outer case')
    heights=np.linspace(LOW+.047,HIGH-.046,5)
    for i in range(4):
        c=(i-1.5)*P
        board(c,(LOW+HIGH)/2,P-.047,HIGH-LOW-.080,-.124,-.111,GLASS,'One glass plane behind the measured lattice')
        for x in (c-P/2+.014,c+P/2-.014):
            board(x,(LOW+HIGH)/2,.028,HIGH-LOW,-.105,.014,FRAME,'Wide dark side stile of each shutter')
        for z in (LOW+.020,HIGH-.020):board(c,z,P-.044,.039,-.104,.011,FRAME,'Top or bottom shutter rail')
        board(c,(LOW+HIGH)/2,.020,HIGH-LOW-.075,-.095,-.033,BAR,'Central upright across the four cells')
        for z in heights[1:-1]:board(c,z,P-.051,.024,-.097,-.022,BAR,'Narrow straight horizontal rail')
        for row,(base,top) in enumerate(zip(heights,heights[1:])):
            shoulder=top if row%2==0 else base;tip=base if row%2==0 else top
            for sign in (-1,1):
                line=LineString([(c+sign*(P/2-.026),shoulder),(c,tip)])
                p=line.buffer(.0105,cap_style=2,join_style=2)
                face(p,-.091,-.040,BAR,'Diagonal between the centre and a corner in one glazed cell')
        # Narrow beading is rounded on the oblique inner edge and remains visible from the side.
        for x in (c-.208,c+.208):
            radius=.007;seg=5 if far else 12;pts=[]
            for z in (LOW+.042,HIGH-.041):
                for k in range(seg):
                    a=2*math.pi*k/seg;pts.append((x+radius*math.cos(a),.033+radius*math.sin(a),z))
            faces=[(k,(k+1)%seg,seg+(k+1)%seg,seg+k) for k in range(seg)]
            faces+= [tuple(range(seg-1,-1,-1)),tuple(range(seg,2*seg))]
            b.add(pts,faces,EDGE,'Slender glazing bead')
    for p in b.parts:
        m=p['material']
        if m not in (WALL,FRAME,BAR,GLASS):continue
        strip=0 if m==WALL else 2 if m==GLASS else 1
        p['texcoords']=[((strip+.018+.963*min(1,max(0,(x+1.28)/2.56)))/3,.989-.96*min(1,max(0,z/2.26))) for x,y,z in p['vertices']]
