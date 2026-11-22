"""Grey cap tiles, plaster face and stepped end of the curved party wall at 120 Hongxi Street."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
ID='pudong-ye-cotton-shop-saddle-gable'
PLASTER='Whitewashed mortar';SHADOW='Shaded grey under-course';CAP='Rounded dark top tiles';NOSE='Weathered edges of individual caps';BRICK='Grey stepped end pieces';FLASH='Dark tile noses below cap';STONE='White plaster end moulding'
PALETTE={n:dict(color=c,roughness=r) for n,c,r in ((PLASTER,[1,1,1],.93),(SHADOW,[.315,.302,.277],.91),(CAP,[1,1,1],.91),(NOSE,[.325,.318,.294],.91),(BRICK,[.408,.392,.359],.94),(FLASH,[.365,.347,.309],.94),(STONE,[.718,.708,.643],.91))}
def texture():
    f=Path(__file__).with_name('lime-and-smoked-tiles.png')
    if not f.exists():
        g=np.random.default_rng(855);y,x=np.indices((220,256));noise=np.asarray(Image.fromarray(g.integers(0,255,(19,16),dtype='uint8')).resize((256,220),Image.Resampling.BILINEAR)).astype(float)
        pale=np.array([216,210,190])+(.09*(noise-127)+g.normal(0,3.2,y.shape))[:,:,None]
        dark=np.array([98,90,75])+(.19*(noise-127)+g.normal(0,4.7,y.shape))[:,:,None]
        Image.fromarray(np.concatenate((pale,dark),axis=1).clip(0,255).astype('uint8')).quantize(128).save(f)
    for m in (CAP,PLASTER):PALETTE[m]['texture']=str(f)
# Measured silhouette; both tips turn above the low saddle between them.
KNOTS=[(-1.16,1.22,.71),(-.93,1.57,1.60),(-.70,1.91,.53),(-.60,1.91,-.71),(-.42,1.54,-2.81),(-.21,.88,-2.39),(.03,.62,-.28),(.25,.65,.77),(.46,.93,1.70),(.67,1.34,1.78),(.80,1.53,1.38),(.86,1.64,.96)]
def top(x):
    for (x0,z0,m0),(x1,z1,m1) in zip(KNOTS,KNOTS[1:]):
        if x<=x1+1e-8:
            dx=x1-x0;t=(x-x0)/dx
            return (2*t**3-3*t**2+1)*z0+(t**3-2*t**2+t)*dx*m0+(-2*t**3+3*t**2)*z1+(t**3-t**2)*dx*m1
    return KNOTS[-1][1]
def add_building(b,far=False):
    texture()
    xs=np.linspace(-1.16,.86,70 if far else 182)
    def face(poly,lo,hi,mat,n):b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),mat,n)
    def shaped(lo,hi,f0,f1,m,label):
        face(Polygon([(x,top(x)+f1) for x in xs]+[(x,top(x)+f0) for x in xs[::-1]]),lo,hi,m,label)
    face(Polygon([(x,top(x)-.088)for x in xs]+[(.86,.04),(-1.16,.04)]),-.13,.13,PLASTER,'Whitewashed saddle gable cut by its measured skyline')
    shaped(-.145,.145,-.093,-.057,SHADOW,'Inset grey bed below the cap')
    # Equal arc-length spacing keeps individual cap ends and lower projections distinct on the steep slopes.
    dense=np.linspace(-1.16,.86,1001);samples=np.column_stack((dense,[top(x)for x in dense]));dist=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(samples,axis=0),axis=1))]
    boundaries=np.interp(np.linspace(0,dist[-1],36),dist,dense)
    for i,(x0,x1) in enumerate(zip(boundaries,boundaries[1:])):
        x1=min(.86,x1+.010);seg=5 if far else 13;pts=[];faces=[];uv=[]
        for x in (x0,(x0+x1)/2,x1):
            for j in range(seg+1):
                a=math.pi*j/seg;pts.append((x,.182*math.cos(a),top(x)-.042+.083*math.sin(a)))
                uv.append((.51+.475*j/seg,.02+.96*(x-x0)/(x1-x0)))
        for k in range(2):
            for j in range(seg):
                a=k*(seg+1)+j;faces.append((a,a+1,a+seg+2,a+seg+1))
        faces.extend([tuple(range(seg,-1,-1)),tuple(range(2*(seg+1),3*(seg+1)))])
        # u advances along the ridge and the outer normal faces up at the crown.
        b.add(pts,faces,CAP,'Individual rounded dark cap');b.parts[-1]['texcoords']=uv
        if i%2==0:
            # The projection visible end-on in the photograph is a transverse dark tile embedded in the step below.
            x=(x0+x1)/2;z=top(x)-.115
            b.box((x,0,z),(max(.035,x1-x0)*.83,.343,.071),FLASH,label='Alternating exposed transverse tile nose')
        leg= min(.014,(x1-x0)*.27);pts=[];quads=[]
        for x in (x0,x0+leg):
            for j in range(seg+1):
                a=math.pi*j/seg;pts.append((x,.185*math.cos(a),top(x)-.039+.088*math.sin(a)))
        for j in range(seg):quads.append((j,j+1,j+seg+2,j+seg+1))
        quads.extend([tuple(range(seg,-1,-1)),tuple(range(seg+1,2*(seg+1)))])
        b.add(pts,quads,NOSE,'Dark rim on each successive cap tile')
    # At the courtward terminal a smaller triangular hood and a stack of pale courses project out from the wall end.
    for y in (-.12,.12):
        b.box((.80,y,.52),(.21,.047,.96),PLASTER,label='Narrow ends of the courtward pier')
    for top_z,wide,deep,mat in ((1.014,.27,.31,STONE),(1.059,.31,.34,SHADOW),(1.104,.34,.37,STONE),(1.150,.38,.40,STONE)):
        b.box((.80,0,top_z-.021),(wide,deep,.043),mat,label='Stepped bands below the end hood')
    gable=Polygon([(-.209,1.147),(.209,1.147),(.209,1.194),(0,1.284),(-.209,1.194)])
    b.prism(gable,.720,.979,lambda y,z,x:(x,y,z),STONE,'Small triangular end moulding')
    p=Polygon([(-.229,1.190),(0,1.289),(.229,1.190),(.229,1.230),(0,1.327),(-.229,1.230)])
    b.prism(p,.714,.987,lambda y,z,x:(x,y,z),BRICK,'Dark sloping trim over the end moulding')
    for part in b.parts:
        if part['material']==PLASTER:part['texcoords']=[(.013+.47*min(1,max(0,(x+1.17)/2.16)),.98-.96*min(1,max(0,z/1.96)))for x,y,z in part['vertices']]
