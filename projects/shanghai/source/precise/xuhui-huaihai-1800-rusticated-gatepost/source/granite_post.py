"""Upper granite pier and gabled coping over the address plate, 1800 Middle Huaihai Road."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,Point,shape
from shapely.affinity import scale,translate
ID='xuhui-huaihai-1800-rusticated-gatepost'
GRANITE='Speckled grey granite';MARGIN='Dressed margin of block';MORTAR='Narrow recessed joint';CAP='Granite gabled coping';GOLD='Warm bronze address plate';TYPE='Black painted number or character';PIN='Dark bronze pins';LUG='Square projecting stone'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(GRANITE,[1,1,1],.94),(MARGIN,[.572,.578,.568],.91),(MORTAR,[.336,.343,.340],.95),(CAP,[.642,.646,.618],.91),(GOLD,[.653,.478,.263],.67),(TYPE,[.115,.106,.091],.88),(PIN,[.324,.276,.196],.71),(LUG,[.433,.438,.419],.90)]}
def texture():
    f=Path(__file__).with_name('grey-flecked-granite.png')
    if not f.exists():
        rng=np.random.default_rng(807);values=rng.normal(0,10,(704,512,1))+np.array([148,147,143])
        p=rng.uniform(size=(704,512));values[p<.113]-=rng.uniform(18,47,(int((p<.113).sum()),1));values[p>.892]+=rng.uniform(13,37,(int((p>.892).sum()),1))
        Image.fromarray(values.clip(0,255).astype('uint8')).quantize(132).save(f)
    PALETTE[GRANITE]['texture']=str(f)
def letters():
    data=json.loads(Path(__file__).with_name('plate-type.json').read_bytes())
    for word,level,step,high in [('1800',1.137,.112,.144),('淮海中路',1.017,.068,.071)]:
        for j,ch in enumerate(word):
            q=shape(data[ch]);x,z,r,t=q.bounds;q=scale(q,xfact=step*.88/(r-x),yfact=high/(t-z),origin=(0,0));x,z,r,t=q.bounds
            yield ch,translate(q,(j-(len(word)-1)/2)*step-(x+r)/2,level-(z+t)/2)
COURSES=[(0,.281),(.291,.649),(.659,.978),(.987,1.276),(1.289,1.419)]
def relief(u,v,idx):
    # Bounded, deterministic chipped face; the rectangular dressed margins stay flat.
    rip=np.sin(11*u+4*v+idx*3)+.51*np.sin(7*v-5*u+idx)+.39*np.cos(18*u-7*v-idx)
    return .010+.018*max(0,1-abs(2*u-1)**3)*max(0,1-abs(2*v-1)**3)+.005*rip
def add_building(b,far=False):
    texture()
    def face(poly,lo,hi,m,label):b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),m,label)
    b.box((0,.199,.708),(.768,.441,1.416),MORTAR,label='Recessed beds seen between granite courses')
    for idx,(z,t) in enumerate(COURSES):
        half=.393-(.008 if idx==4 else 0)
        b.box((0,.192,(z+t)/2),(2*half,.458,t-z),MARGIN,label='Dressed edges of granite course')
        for side in ['front','left','right']:
            n,m=(8,5)if far else (19,11)
            vertices=[];faces=[]
            for iy in range(m+1):
                v=iy/m;zz=z+.014+(t-z-.029)*v
                for ix in range(n+1):
                    u=ix/n;dd=relief(u,v,idx+(1 if side!='front' else 0))
                    if side=='front':xyz=(-half+.015+(2*half-.030)*u,-.038-dd,zz)
                    else:
                        sign=1 if side=='right' else -1;xyz=(sign*(half+dd),-.022+.429*u,zz)
                    vertices.append(xyz)
            for iy in range(m):
                for ix in range(n):
                    a=iy*(n+1)+ix
                    f=(a,a+1,a+n+2,a+n+1)
                    faces.append(tuple(reversed(f)) if side=='left' else f)
            b.add(vertices,faces,GRANITE,'Split granite face on the '+side+' of course '+str(idx+1))
            b.parts[-1]['texcoords']=[[(ix/n)*.985+.006,(iy/m)*.982+.008]for iy in range(m+1)for ix in range(n+1)]
    # Two sloping coping stones shelter an open triangular recess behind the raised lug.
    wedge=Polygon([(-.442,1.423),(0,1.736),(.442,1.423),(.414,1.379),(0,1.652),(-.414,1.379)])
    face(wedge,-.441,.078,CAP,'Two sloping long stones of the open gabled coping')
    triangle=Polygon([(-.376,1.407),(0,1.647),(.376,1.407)])
    face(triangle,-.396,-.102,MARGIN,'Set-back gable field')
    lug=Polygon([(-.065,1.494),(-.048,1.577),(.057,1.566),(.064,1.499),(.017,1.473)])
    face(lug,-.104,.012,LUG,'Small faceted central projecting lug below ridge')
    plate=box(-.319,.963,.319,1.277)
    for x in [-.319,.319]:
        for z in [.963,1.277]:plate=plate.difference(Point(x,z).buffer(.043,resolution=6 if far else 15))
    face(plate,.060,.082,GOLD,'Address plaque with clipped concave corners')
    for x in [-.297,.297]:
        face(Point(x,1.099).buffer(.0095,resolution=6 if far else 13),.082,.095,PIN,'Visible side pin of the address plaque')
    for ch,p in letters():
        face(p.simplify(.0004 if far else .00010,preserve_topology=True),.082,.087,TYPE,'Black lettering '+ch)
