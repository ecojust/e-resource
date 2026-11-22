"""Pierced A-shaped steeple of the Sacred Heart Church on Zhongxiatang Street."""
from pathlib import Path
import json,math,numpy as np
from PIL import Image
from shapely.affinity import scale,translate
from shapely.geometry import Polygon,box,shape
ID='jiading-gongbaoqiao-perforated-triangular-steeple'
PALE='Pale stucco';OCHRE='Shaded ochre return';STONE='Light tower coping';DARK='Three raised inscription characters';METAL='Aged cross and rods';BAR='Dark inner cross braces'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(PALE,[1,1,1],.94),(OCHRE,[1,1,1],.93),(STONE,[.70,.68,.59],.84),(DARK,[.15,.17,.16],.70),(METAL,[.40,.39,.33],.58),(BAR,[.31,.25,.18],.90)]}
def texture():
    out=Path(__file__).with_name('pale-render-and-aperture-return.png')
    if not out.exists():
        g=np.random.default_rng(903);h,w=400,215
        long=np.asarray(Image.fromarray(g.integers(0,255,(15,90),dtype='uint8')).resize((w,h),Image.Resampling.BICUBIC),float)-128
        cloudy=np.asarray(Image.fromarray(g.integers(0,255,(8,11),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-128
        y,x=np.indices((h,w));a=.080*long+.075*cloudy+g.normal(0,2.6,(h,w))
        paint=np.array([182,177,162])+a[:,:,None];returns=np.array([139,120,93])+(a+.08*cloudy)[:,:,None]
        Image.fromarray(np.concatenate((paint,returns),axis=1).clip(0,255).astype('uint8')).quantize(196).save(out)
    for m in (PALE,OCHRE):PALETTE[m]['texture']=str(out)
def glyphs():
    name=json.loads(Path(__file__).with_name('church-inscription.json').read_bytes())
    for i,ch in enumerate('天主堂'):
        p=shape(name[ch]);a,b,c,d=p.bounds;p=scale(p,.228/(c-a),.173/(d-b),origin=(0,0));a,b,c,d=p.bounds
        yield translate(p,-(a+c)/2,2.53-i*.235-(b+d)/2)
def add_building(b,far=False):
    texture()
    def prism(p,front,back,mat,label):
        n=len(b.parts);b.prism(p,-back,-front,lambda x,z,d:(x,-d,z),mat,label)
        if mat in (PALE,OCHRE):
            k=0 if mat==PALE else 1
            for r in b.parts[n:]:r['texcoords']=[((k+.012+.976*(x+1.32)/2.64)/2,.99-.98*z/4.25)for x,y,z in r['vertices']]
    def triangle(base,top,z0):return Polygon([(-base,z0),(base,z0),(0,top)])
    outer=triangle(1.19,4.13,.14)
    front=outer.difference(triangle(.845,1.58,.136))
    rear=outer.difference(triangle(.57,1.10,.136))
    prism(front,-.055,.16,PALE,'Pale front plate with its wide three-sided aperture')
    prism(rear,.31,.58,OCHRE,'Shaded rear reveal with smaller triangular opening')
    for side in (-1,1):
        a,z=side*.843,.14;c,t=0.,1.58;e,v=side*.57,.14;f,u=0.,1.10
        coords=[(a,.159,z),(c,.159,t),(f,.313,u),(e,.313,v)]
        if side>0:coords.reverse()
        b.add(coords,[(0,1,2,3)],OCHRE,'Splayed inside face of the open diagonal jamb')
    for s in (-1,1):
        a,z=s*.29,1.11;c,t=-s*.22,1.40;dx,dz=c-a,t-z;mag=math.hypot(dx,dz);nx,nz=-dz/mag*.022,dx/mag*.022
        prism(Polygon([(a+nx,z+nz),(c+nx,t+nz),(c-nx,t-nz),(a-nx,z-nz)]),.190,.255,BAR,'Cross brace above the clear lower aperture')
    for p in glyphs():prism(p.simplify(.00175) if far else p,-.086,-.052,DARK,'Raised dark inscription')
    for z,h,d,m in ((.018,.036,.82,STONE),(.074,.067,.76,STONE),(.126,.033,.69,PALE)):
        b.box((0,.21,z),(2.49,d,h),m,label='Light overlapping tower ledges')
    b.box((0,.090,4.575),(.018,.022,.945),METAL,label='Narrow upright above apex')
    b.box((0,.09,4.808),(.704,.026,.021),METAL,label='Single horizontal cross-arm')
    def knob(x,y,z,r,label):
        bands=5 if far else 10;slices=8 if far else 18;pts=[(x,y,z-r)]
        for i in range(1,bands):
            phi=-math.pi/2+math.pi*i/bands
            for j in range(slices):
                a=2*math.pi*j/slices;pts.append((x+r*math.cos(phi)*math.cos(a),y+r*math.cos(phi)*math.sin(a),z+r*math.sin(phi)))
        top=len(pts);pts.append((x,y,z+r));faces=[(0,1+(j+1)%slices,1+j)for j in range(slices)]
        for k in range(bands-2):
            n=1+k*slices;faces.extend([(n+j,n+(j+1)%slices,n+slices+(j+1)%slices,n+slices+j)for j in range(slices)])
        n=1+(bands-2)*slices;faces.extend((n+j,n+(j+1)%slices,top)for j in range(slices));b.add(pts,faces,METAL,label)
    for x,z,r in ((0,4.13,.065),(0,5.045,.031),(-.35,4.808,.027),(.35,4.808,.027)):knob(x,.09,z,r,'Apex junction or terminal boss')
    for part in b.parts:
        if part['material'] in (PALE,OCHRE) and not part.get('texcoords'):
            strip=(PALE,OCHRE).index(part['material'])
            part['texcoords']=[((strip+.014+.97*(x+1.32)/2.64)/2,.985-.96*max(0,min(1,(z+.15*y)/4.25)))for x,y,z in part['vertices']]
