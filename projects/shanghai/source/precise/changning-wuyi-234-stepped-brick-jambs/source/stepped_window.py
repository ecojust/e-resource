"""Saw-toothed brick edging and combed stucco, based on the 2018 view of 234 Wuyi Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box
ID='changning-wuyi-234-stepped-brick-jambs'
PLASTER='Combed cream stucco'; BRICK='Burnished brown-red brick'; DEEP='Dark red brick'
JOINT='Recessed brown mortar'; FRAME='Painted grey-white window frame'; SEAL='Dark glazing gasket'
GLASS='Blue-grey single pane'; STONE='Pale projecting sill'; TOP='Shadow under the eave'
PALETTE={key:dict(color=c,roughness=r) for key,c,r in [(PLASTER,[1,1,1],.97),(BRICK,[.321,.139,.111],.94),(DEEP,[.255,.100,.086],.95),(JOINT,[.172,.104,.089],.97),(FRAME,[.694,.689,.668],.70),(SEAL,[.099,.101,.104],.86),(GLASS,[.123,.176,.217],.33),(STONE,[.650,.617,.527],.94),(TOP,[.176,.151,.135],.93)]}
def texture():
    f=Path(__file__).with_name('combed-stucco.png')
    if not f.exists():
        rng=np.random.default_rng(699);y,x=np.indices((384,384))
        phase=x*.337+1.10*np.sin(y*.019)+.45*np.sin(y*.071+x*.036)
        grooves=np.maximum(0,np.cos(phase))**7
        field=15*grooves+2.6*np.cos(phase+.98)+rng.normal(0,5.8,x.shape)+3.4*np.sin(y*.08+x*.031)
        image=np.array([199,194,183])[None,None,:]-field[...,None]
        Image.fromarray(image.clip(0,255).astype('uint8')).quantize(120).save(f)
    PALETTE[PLASTER]['texture']=str(f)
BOTTOM=.65; TOPLINE=2.022; N=18; RISE=(TOPLINE-BOTTOM)/N; CORE=.39
def reach(course,side):
    widths=(.60,.50,.40,.30) if side<0 else (.65,.55,.44,.32)
    return widths[course%4]*2*CORE
def add_building(b,far=False):
    texture()
    def sheet(p,back,front,m,name):b.prism(p,back,front,lambda x,z,y:(x,-y,z),m,name)
    def rect(l,r,z,t,back,front,m,name):sheet(box(l,z,r,t),back,front,m,name)
    wall=box(-1.20,0,1.2,2.48).difference(box(-CORE,BOTTOM,CORE,TOPLINE))
    sheet(wall,-.26,0,PLASTER,'Combed rendering around the opening')
    for j in range(N):
        z=BOTTOM+j*RISE
        for side in (-1,1):
            extent=reach(j,side)
            l,r=sorted((CORE*side,(CORE+extent)*side))
            rect(l,r,z,z+RISE,-.008,.006,JOINT,'Brown mortar bed at a stepped jamb')
            split=l+.48*(r-l) if j%2==0 else l+.74*(r-l)
            for k,(a,c) in enumerate([(l+.003,split-.003),(split+.003,r-.003)]):
                rect(a,c,z+.004,z+RISE-.004,-.005,.014,DEEP if (j+2*k)%7==0 else BRICK,'Stretcher at stepped window jamb')
    a=box(-CORE,BOTTOM,CORE,TOPLINE); inner=box(-.31,BOTTOM+.084,.31,TOPLINE-.084)
    sheet(a.difference(inner),-.126,-.034,FRAME,'Pale flat frame of the single window')
    aperture=box(-.295,BOTTOM+.099,.295,TOPLINE-.099)
    sheet(inner.difference(aperture),-.129,-.098,SEAL,'Narrow dark line at the edge of glass')
    sheet(aperture,-.146,-.123,GLASS,'Single blue-grey glazed pane')
    rect(-.47,.47,BOTTOM-.081,BOTTOM,-.118,.115,STONE,'Projecting window sill')
    rect(-1.20,1.20,2.39,2.48,-.25,.092,TOP,'Dark thin edge of the eave')
    if not far:
        # Comb marks continue across the sill line in the photographed plaster.
        for i in range(37):
            x=-1.17+i*.064
            if abs(x)<.83:continue
            for z in (.20,.72,1.30,1.85):
                rect(x,x+.006,z,z+.28,-.006,.003,PLASTER,'Raised edge of a plaster comb stroke')
    for group in b.parts:
        if group['material']==PLASTER:group['texcoords']=[[(x+1.2)/2.4,z/2.48]for x,y,z in group['vertices']]
