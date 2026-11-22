"""Upper two light bays of the former Hua Yi printing works, photographed at 308 Yulin Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
ID='yangpu-huayi-printing-works-fluted-parapet'
CEMENT='Grey streaked concrete';MORTAR='Recessed pale grey bedding';BRICK='Russet brick infill'
RED='Brown-red brick';SASH='Dark steel sash';GLASS='Cool grey glazing';LINING='Grey recessed window reveal'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(CEMENT,[1,1,1],.95),(MORTAR,[.58,.56,.51],.97),(BRICK,[.529,.253,.196],.93),(RED,[.444,.198,.150],.92),(SASH,[.193,.21,.207],.66),(GLASS,[.30,.35,.36],.41),(LINING,[.398,.407,.390],.90)]}
def texture():
 f=Path(__file__).with_name('cast-concrete.png')
 if not f.exists():
    yy,xx=np.indices((384,384));rng=np.random.default_rng(731)
    vertical=3*np.cos(xx*.033+np.sin(yy*.014))+2*np.sin(xx*.19+.4*np.sin(yy*.016))
    field=rng.normal(0,4.8,xx.shape)+vertical
    Image.fromarray((np.array([161,157,147])+field[:,:,None]).clip(0,255).astype('uint8')).quantize(100).save(f)
 PALETTE[CEMENT]['texture']=str(f)
BAYS=(-.50,.50)
def add_building(b,far=False):
 texture()
 def form(shape,back,front,m,label):b.prism(shape,back,front,lambda x,z,d:(x,-d,z),m,label)
 def rect(l,r,z,t,back,front,m,label):form(box(l,z,r,t),back,front,m,label)
 openings=[box(x-.403,.94,x+.403,2.14)for x in BAYS]
 panels=[box(x-.393,.058,x+.393,.82)for x in BAYS]
 form(box(-1.04,0,1.04,2.79).difference(unary_union(openings+panels)),-.17,0,CEMENT,'Concrete frame around windows and brick aprons')
 for x,hole in zip(BAYS,openings):
    inner=hole.buffer(-.037,join_style=2);pane=inner.buffer(-.021,join_style=2)
    form(hole.difference(inner),-.132,-.021,LINING,'Slender recessed jamb and head')
    form(inner.difference(pane),-.153,-.09,SASH,'Outer steel window frame')
    form(pane,-.166,-.143,GLASS,'Inset window glass')
    rect(x-.349,x+.349,1.86,1.889,-.146,-.09,SASH,'Thick horizontal bar under the transom')
    rect(x-.010,x+.010,.993,2.086,-.144,-.092,SASH,'Central vertical steel bar')
    rect(x-.349,x+.349,1.490,1.506,-.140,-.107,SASH,'Thin lower sash tie')
    left=x-.393
    rect(left,x+.393,.058,.82,-.146,-.051,MORTAR,'Pale mortar behind the red panels')
    for j in range(11):
        bottom=.061+j*.069
        cells=5
        for k in range(-1,cells+1):
            l=max(left,left+(.1572*k)+(.0786 if j%2 else 0))
            r=min(x+.393,left+(.1572*(k+1))+(.0786 if j%2 else 0))
            if r-l>.012:rect(l+.004,r-.004,bottom,bottom+.061,-.125,-.038,RED if (j+2*k)%5==0 else BRICK,'Thin brick course with staggered joints')
    rect(x-.039,x+.039,.05,.83,-.12,.018,CEMENT,'Narrow concrete rib dividing the apron')
    # Closely set vertical fins have unequal top heights and stepped lower ends.
    for i,u in enumerate((-.315,-.155,0,.155,.315)):
        cx=x+u;width=.035 if i%2 else .042;top=2.81+[.09,.035,.115,.055,.095][i]
        tip=2.17 if i in (0,4) else 2.22
        outline=Polygon([(cx-width,tip+.045),(cx,tip),(cx+width,tip+.045),(cx+width,top-.026),(cx+width*.60,top),(cx-width*.55,top),(cx-width,top-.027)])
        form(outline,-.035,.051 if i%2 else .065,CEMENT,'Chamfered concrete flute over the steel window')
        for z in (2.23,2.29):
            rect(cx-width-.001,cx+width+.001,z,z+.011,.049,.072,CEMENT,'Small transverse step at the base of a flute')
        if not far:
            for offset in (-width*.56,width*.56):
                rect(cx+offset-.004,cx+offset+.004,2.36,top-.035,.051,.067,CEMENT,'Short raised fillet on the weathered fluted face')
 for g in b.parts:
    if g['material']==CEMENT:g['texcoords']=[[(x+1.04)/2.08,z/2.95] for x,y,z in g['vertices']]
