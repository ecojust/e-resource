"""The numbered frontage at 46 Xinle Road. Brick courses wrap around its eastern corner."""
from pathlib import Path
import numpy as np
from PIL import Image

ID = "xuhui-xinle-46-two-tone-tilework"
RED="Burgundy ceramic facings"; IVORY="Pale buff ceramic facings"; UMBER="Soot-brown facing tiles"
MORTAR="Recessed grey lime joints"; STONE="Light cement window surround"
CAP="Terracotta string course"; DRIP="Grey coping"; GREEN="Green street number enamel"
INK="Ivory enamel numerals"; DARK="Shop joinery"; SLAT="Shadowed grey shutter"
FACINGS=(RED,IVORY,UMBER,STONE,CAP)
PALETTE={m:dict(color=[1.,1.,1.],roughness=.88) for m in FACINGS}
PALETTE.update({m:dict(color=c,roughness=r) for m,c,r in [(MORTAR,[.55,.50,.45],.96),(DRIP,[.36,.35,.32],.87),(GREEN,[.086,.39,.37],.44),(INK,[.91,.94,.87],.65),(DARK,[.15,.18,.17],.75),(SLAT,[.405,.46,.45],.84)]})
EDGE=2.32; REVEAL=1.53; STEP=.124; WIDTH=.305; ROWS=22
def texture():
    path=Path(__file__).with_name("xinle-fired-facings.png")
    if not path.exists():
        rng=np.random.default_rng(839);n=192
        def cloud(w,h):
            return np.asarray(Image.fromarray(rng.integers(0,255,(h,w),dtype="uint8")).resize((n,n),Image.Resampling.BICUBIC),float)-128
        grains=[]
        for colour in ([123,69,61],[223,200,162],[117,104,91],[194,189,173],[175,117,91]):
            variation=cloud(14,11)*.10+cloud(62,17)*.044+rng.normal(0,2.3,(n,n))
            grains.append(np.array(colour)+variation[:,:,None])
        Image.fromarray(np.clip(np.concatenate(grains,axis=1),0,255).astype("uint8")).quantize(240).save(path)
    for mat in FACINGS: PALETTE[mat]["texture"]=str(path)
def segments(row,left,right):
    first=-3.1+.5*WIDTH*(row%2)
    for col in range(22):
        lo=first+col*WIDTH;hi=lo+WIDTH
        u,v=max(lo,left),min(hi,right)
        if v-u>.018: yield col,u,v
def material(row,col):
    if row>=19: return UMBER
    return RED if (row+col)%2 else IVORY
def add_building(b,far=False):
    texture()
    def block(x0,x1,y0,y1,z0,z1,m,n):
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=n)
    # Local face coordinates follow the street first, then the side turning into the lane.
    def facing(lo,hi,z0,z1,mat,side=False):
        g=.0045;u,v=lo+g,hi-g;l,h=z0+g,z1-g
        def vertex(s,depth,z):return (EDGE-depth,s,z) if side else (s,depth,z)
        recess=-.010;back=.014;bevel=.004
        ends=[(u,l),(v,l),(v,h),(u,h)]
        if far:
            levels=[(recess,ends),(back,ends)]
        else:
            levels=[(recess,[(u+bevel,l+bevel),(v-bevel,l+bevel),(v-bevel,h-bevel),(u+bevel,h-bevel)]),(recess+bevel,ends),(back,ends)]
        vertices=[vertex(s,d,z) for d,outline in levels for s,z in outline]
        faces=[(0,1,2,3)]
        for k in range(len(levels)-1):
            a=4*k
            for j in range(4):faces.append((a+j,a+j+4,a+(j+1)%4+4,a+(j+1)%4))
        last=(len(levels)-1)*4;faces.append(tuple(last+i for i in (3,2,1,0)))
        b.add(vertices,faces,mat,'Lane return facing' if side else 'Street facing')
    block(-EDGE,-REVEAL,.004,.27,0,2.75,MORTAR,'Left wall bed')
    block(REVEAL,EDGE,.004,.27,0,2.75,MORTAR,'Right wall bed')
    block(-REVEAL,REVEAL,.004,.27,1.51,2.75,MORTAR,'Masonry above opening')
    block(EDGE-.24,EDGE-.004,0,.98,0,2.75,MORTAR,'Return to lane')
    for r in range(ROWS):
        intervals=[(-EDGE,-REVEAL),(REVEAL,EDGE)] if r<14 else [(-EDGE,EDGE)]
        for left,right in intervals:
            for col,u,v in segments(r,left,right):
                facing(u,v,r*STEP,(r+1)*STEP,material(r,col))
        for col,u,v in segments(r,0,.98):
            facing(u,v,r*STEP,(r+1)*STEP,material(r,col+1),True)
    # A single row of soldier tiles above the continuous cement head runs jamb to jamb.
    for i in range(31):
        u=-REVEAL+i*2*REVEAL/31
        facing(u,u+2*REVEAL/31,1.51,14*STEP,IVORY if i%2 else RED)
    block(-REVEAL,REVEAL,-.040,.15,1.22,1.508,STONE,'Cement head')
    for sign in (-1,1):
        x=sign*(REVEAL-.093)
        block(x-.093,x+.093,-.034,.20,.01,1.224,STONE,'Cement jamb')
    block(-1.341,1.341,.095,.25,.005,1.221,DARK,'Dark shop window frame')
    block(-1.285,1.285,.084,.102,.015,1.15,SLAT,'Recessed top portion of shutter')
    for z in np.arange(.08,1.13,.074 if not far else .15):
        block(-1.28,1.28,.078,.089,z-.004,z+.004,DARK,'Horizontal shutter joints')
    for a,h,mat,pro in [(2.727,2.764,DRIP,.037),(2.764,2.966,CAP,.049),(2.966,2.995,CAP,.07),(2.995,3.07,DRIP,.093)]:
        block(-EDGE-pro,EDGE+pro,-pro,.29,a,h,mat,'Street string course and drip')
        block(EDGE-.22,EDGE+pro,.29,.98,a,h,mat,'Returning string course')
    block(-.146,.146,-.062,-.039,1.258,1.479,GREEN,'Green number plate')
    def glyph(coords):
        b.tube([(x,-.068,z) for x,z in coords],.0058,INK,5 if far else 8,'Number 46 on green enamel')
    glyph([(-.029,1.437),(-.082,1.348),(-.011,1.348)])
    glyph([(-.033,1.436),(-.033,1.322)])
    glyph([(.071,1.439),(.045,1.434),(.023,1.412),(.012,1.364),(.019,1.334),(.038,1.325),(.063,1.328),(.08,1.345),(.077,1.368),(.061,1.384),(.04,1.387),(.017,1.374)])
    for part in b.parts:
        m=part['material']
        if m in FACINGS:
            slot=FACINGS.index(m)
            part['texcoords']=[((slot+.025+.95*((x*.14+y*.21+.523)%1))/len(FACINGS),.975-.95*((z*.29+y*.05+.021)%1))for x,y,z in part['vertices']]
