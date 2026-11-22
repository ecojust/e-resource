"""Paired stepped lozenges and the three registers of blind arches."""
from pathlib import Path
import math,numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
ID='qingpu-zhujiajiao-belfry-brick-lozenges'
GREY='Weathered grey brick';RED='Burnt orange brick';ASH='Light radial voussoirs';CORN='Shadowed dark-red cornice';MORTAR='Recessed buff pointing'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in ((GREY,[1,1,1],.95),(RED,[1,1,1],.92),(ASH,[.65,.62,.54],.91),(CORN,[.44,.26,.19],.93),(MORTAR,[.56,.54,.47],.99))}
BAYS=[-.62,.62];BANDS=[(BAYS,1.07,.52,.49,.129), (BAYS,1.83,.53,.38,.104), ([-.888,-.296,.296,.888],2.56,.218,.202,.087)]
def texture():
    f=Path(__file__).with_name('grey-and-russet-fired-brick.png')
    if not f.exists():
        g=np.random.default_rng(907);h,w=450,350;y,x=np.indices((h,w));row=y//13;col=(x+17*(row%2))//35;grain=g.normal(0,4.3,(h,w));chars=g.uniform(-16,15,(37,13))[row,col];joints=(y%13<1)|((x+17*(row%2))%35<1)
        def brick(base,mortar):
            surf=np.array(base)+(grain+chars)[:,:,None];surf[joints]=np.array(mortar)+grain[joints,None];return surf
        Image.fromarray(np.concatenate((brick([148,148,139],[160,157,143]),brick([155,90,59],[135,126,107])),axis=1).clip(0,255).astype('uint8')).quantize(196).save(f)
    for m in (GREY,RED):PALETTE[m]['texture']=str(f)
def arch(cx,z,r,h):return [(cx+r*math.cos(t),z+h*math.sin(t))for t in np.linspace(0,math.pi,37)]
def add_building(b,far=False):
    texture()
    def panel(p,f,k,m,n):b.prism(p,-k,-f,lambda x,z,d:(x,-d,z),m,n)
    def piece(a,z,c,t,f,k,m,n):panel(box(a,z,c,t),f,k,m,n)
    piece(-1.62,.10,1.62,3.16,.14,.29,GREY,'Original grey backing in the shallow arches')
    for i in range(2):
        a=-1.63 if i==0 else 1.20;c=a+.43;piece(a,.13,c,3.17,-.055,.15,GREY,'Outer banded pier')
        for j in range(7):
            z=.34+j*.401;piece(a-.005,z,c+.006,z+.077,-.063,-.050,RED,'Horizontal red band across outer pier')
    for cx in BAYS:
        for j,offset in enumerate((0,1,2,3,4,3,2,1,0)):
            z=.46+.078*j
            for dx in ([-offset,offset]if offset else [0]):
                x=cx+dx*.087;piece(x-.058,z,x+.058,z+.067,.125,.145,RED,'Stepped lozenge built one brick course at a time')
        piece(cx-.093,.776,cx+.093,.844,.124,.146,RED,'Short central red brick')
    for level,(xs,spring,rise_width,rise_height,thick) in enumerate(BANDS):
        for cx in xs:
            r,h=rise_width,rise_height
            above=box(cx-r-thick,spring,cx+r+thick,spring+h+thick+.055)
            opening=Polygon([(cx-r,spring-.01),(cx+r,spring-.01),*arch(cx,spring,r,h)])
            panel(above.difference(opening),.001,.15,GREY,'Raised spandrel around a recessed round-headed blind arch')
            pieces=11 if level<2 else 7
            for j in range(pieces):
                start=math.pi*j/pieces;end=math.pi*(j+1)/pieces
                angles=np.linspace(start+.002,end-.002,6 if not far else 3)
                pts=[(cx+(r+thick)*math.cos(a),spring+(h+thick)*math.sin(a))for a in angles]+[(cx+r*math.cos(a),spring+h*math.sin(a))for a in reversed(angles)]
                panel(Polygon(pts),-.032,.018,RED if j%2==0 else ASH,'Alternating radial brick and pale voussoir')
            for side in (-1,1):
                x=cx+side*(r+thick*.5)
                piece(x-thick*.581,spring-.066,x+thick*.581,spring+.009,-.049,.135,RED,'Short projecting impost under the archivolt')
    piece(-.122,.12,.122,1.047,-.012,.153,GREY,'Shared short pier between the two lower recesses')
    for z in (.235,.67,.993):piece(-.126,z,.126,z+.072,-.034,.02,RED,'Red cross band on short pier')
    for z,ext,depth,ht,m in ((.012,.045,.128,.065,CORN),(.074,.001,.090,.056,RED),(3.133,.003,.090,.113,RED),(3.244,.053,.135,.093,CORN),(3.337,.103,.202,.072,RED),(3.408,.135,.264,.088,CORN)):
        piece(-1.62-ext,z,1.62+ext,z+ht,-depth,.27,m,'Stepped red top or bottom cornice')
    for p in b.parts:
        m=p['material']
        if m not in (GREY,RED):continue
        strip=int(m==RED);p['texcoords']=[((strip+.011+.976*(x+1.79)/3.58)/2,.989-.975*z/3.52)for x,y,z in p['vertices']]
