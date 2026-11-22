"""Three engaged columns and two bow-fronted window bays, No. 525 South Xiangyang Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Point
from shapely.affinity import scale,translate
ID='xuhui-xiangyang-525-fluted-round-bay'
CREAM='Warm cream window reveals';FRAME='Grey painted steel';GLASS='Cool grey window glass';STONE='Pale stone columns';GREY='Grey fascia and bases';RED='Deep red oval panels';SOFFIT='Ochre cornice blocks'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(CREAM,[1.,1.,1.],.92),(FRAME,[.27,.30,.29],.64),(GLASS,[.51,.57,.57],.37),(STONE,[.77,.74,.66],.91),(GREY,[.46,.454,.446],.86),(RED,[.51,.23,.215],.78),(SOFFIT,[.62,.54,.41],.91)]}
R=2.;LIMIT=1.86;COL=[-1.5,0,1.5]
def pos(u,z,d):return ((R+d)*np.sin(u/R),R-(R+d)*np.cos(u/R),z)
def texture():
    f=Path(__file__).with_name('warm-mineral-render.png')
    if not f.exists():
        rng=np.random.default_rng(767);a=np.array([201,190,155])+rng.normal(0,3.7,(256,256,1));Image.fromarray(a.clip(0,255).astype('uint8')).quantize(91).save(f)
    PALETTE[CREAM]['texture']=str(f)
def add_building(b,far=False):
    texture();n=26 if far else 48
    def skin(poly,back,front,mat,name):
        for l,r in zip(np.linspace(-LIMIT,LIMIT,n+1)[:-1],np.linspace(-LIMIT,LIMIT,n+1)[1:]):
            sub=poly.intersection(box(l,-.3,r,3.95))
            if sub.area>1e-9:b.prism(sub,back,front,pos,mat,name)
    def layer(a,c,lo,hi,back,front,mat,name):skin(box(a,lo,c,hi),back,front,mat,name)
    wall=box(-LIMIT,.07,LIMIT,3.09)
    for center in [-.75,.75]:
        aperture=box(center-.551,.79,center+.551,2.48);wall=wall.difference(aperture)
        pane=box(center-.519,.823,center+.519,2.437);skin(aperture.difference(pane),-.108,-.029,FRAME,'Steel window perimeter')
        skin(pane,-.146,-.12,GLASS,'Recessed glazing')
        for u in [center-.179,center+.179]:
            layer(u-.014,u+.014,.82,2.44,-.128,-.041,FRAME,'Two upright mullions')
        for h in [1.31,1.91]:
            layer(center-.52,center+.52,h-.011,h+.011,-.126,-.062,FRAME,'Thin horizontal sash bar')
    skin(wall,-.189,0,CREAM,'Curved wall framing the windows')
    for lo,hi,d,mat in [(0,.104,.24,RED),(.098,.18,.272,GREY),(.18,.26,.198,GREY),(.705,.773,.072,GREY),(2.565,2.60,.095,GREY),(2.593,2.66,.118,STONE),(2.66,2.716,.146,GREY),(2.712,2.819,.08,CREAM),(2.815,2.884,.097,SOFFIT),(2.999,3.064,.233,RED),(3.058,3.119,.249,GREY)]:
        layer(-LIMIT,LIMIT,lo,hi,-.04,d,mat,'Continuous projecting bow-front moulding')
    for u in np.linspace(-1.68,1.68,9):layer(u-.095,u+.095,2.864,3.013,-.035,.231,SOFFIT,'Projecting cornice bracket')
    for u in COL:
        c=np.array(pos(u,.0,.042));xy=c[:2]
        levels=[(.695,.159,0),(.725,.171,0),(.752,.166,0),(.782,.146,.011),(.895,.14,.012),(1.17,.136,.011),(1.249,.134,0),(1.95,.12,0),(2.27,.12,.011),(2.413,.12,.011),(2.455,.136,0),(2.505,.155,0)]
        k=40 if far else 96;angles=np.linspace(0,2*np.pi,k,endpoint=False)
        vs=[]
        for h,r,dip in levels:
            radius=r-dip*.5*(1+np.cos(12*angles))
            vs.extend([[xy[0]+v*np.sin(a),xy[1]-v*np.cos(a),h]for a,v in zip(angles,radius)])
        faces=[]
        for j in range(len(levels)-1):
            for i in range(k):
                l=j*k+i;m=j*k+(i+1)%k;faces.extend([(l,m,l+k),(m,m+k,l+k)])
        b.add(vs,faces,STONE,'Shallow-fluted pale column with partly smooth shaft')
        layer(u-.192,u+.192,.229,.709,-.015,.173,GREY,'Square column plinth')
        oval=translate(scale(Point(0,0).buffer(1,resolution=8 if far else 20),.088,.144),u,.472)
        skin(oval,.17,.185,RED,'Oval red panel on the square plinth')
        for z0,z1,d,mat in [(2.462,2.505,.187,GREY),(2.505,2.556,.203,RED),(2.555,2.597,.218,GREY)]:
            layer(u-.203,u+.203,z0,z1,-.015,d,mat,'Layered capital beneath the curved fascia')
    for part in b.parts:
        if part['material']==CREAM:part['texcoords']=[[(np.arctan2(x,R-y)*R+LIMIT)/1.25,z/1.35]for x,y,z in part['vertices']]
