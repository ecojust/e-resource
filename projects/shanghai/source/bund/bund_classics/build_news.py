"""North China Daily News / AIA building: photographic facade on mapped OSM footprint.

blender --background --python build_news.py
Uses build_classics.py, mesh_utils.py and news-footprint.json in this directory.
Height and sculptural detail are interpreted, not a conservation survey.
"""
import bpy, json, math, os, sys
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from build_classics import *
RED=8
PALETTE.append(('AIA red lettering',(.62,.022,.035),.48,0))

def facade_band(f,z0,z1,windows,start=None,end=None):
    left=-f.L/2 if start is None else start;right=f.L/2 if end is None else end
    cursor=left
    for u,w,lo,hi,arched in sorted(windows):
        a=u-w/2;z=u+w/2
        if a>cursor:f.box((cursor+a)/2,(z0+z1)/2,a-cursor,z1-z0)
        f.cell(u,w,z0,z1,w,lo,hi,arched)
        cursor=z
    if right>cursor:f.box((cursor+right)/2,(z0+z1)/2,right-cursor,z1-z0)

def flute_column(b,xy,z0,z1,r,segments=96):
    x,y=xy;profiles=[(z0,r*1.25),(z0+.15,r*1.25),(z0+.30,r),(z1-.30,r*.88),(z1-.18,r*1.14),(z1,r*1.22)]
    verts=[]
    for z,rad in profiles:
        for j in range(segments):
            a=math.tau*j/segments;rr=rad*(1-.055*(1+math.cos(a*16)))
            verts.append((x+rr*math.cos(a),y+rr*math.sin(a),z))
    faces=[]
    for k in range(len(profiles)-1):
        for j in range(segments):faces.append((k*segments+j,k*segments+(j+1)%segments,(k+1)*segments+(j+1)%segments,(k+1)*segments+j))
    b.geom(verts,faces,TRIM,True)
    b.box((x,y,z0+.10),(r*2.8,r*2.8,.20),TRIM)
    b.box((x,y,z1-.05),(r*2.8,r*2.8,.16),TRIM)

def atlas(b,f,u):
    # Simplified load-bearing human silhouette, retaining arm/torso/scroll relief.
    q=f.p(u,0,.35)
    lathe(b,q.xy,[(24.5,.13),(24.8,.20),(25.3,.29),(25.8,.24),(26.2,.35),(26.6,.32)],TRIM,18)
    lathe(b,q.xy,[(26.63,.12),(26.7,.23),(26.92,.25),(27.13,.18),(27.2,.02)],TRIM,20)
    for s in [-1,1]:
        a=f.p(u+s*.28,26.4,.36);el=f.p(u+s*.52,26.74,.32);hand=f.p(u+s*.65,27.35,.23)
        b.segment(a,el,.20,.23,f.n,TRIM);b.segment(el,hand,.18,.20,f.n,TRIM)
    f.box(u,24.4,.68,.24,.38,.3,TRIM)

def news_tower(b,f,u):
    q=f.p(u,0,-1.15);w=3.0
    b.box((q.x,q.y,34.30),(w,w,.46),TRIM,[f.t,f.n,Vector((0,0,1))])
    for su in [-1,1]:
        for sd in [-1,1]:
            for delta in [-.17,.17]:
                p=q+f.t*(su*1.1+delta)+f.n*(sd*1.1)
                flute_column(b,p.xy,34.52,37.2,.15,48)
    b.box((q.x,q.y,37.35),(3.30,3.30,.32),TRIM,[f.t,f.n,Vector((0,0,1))])
    b.box((q.x,q.y,37.64),(3.05,3.05,.20),STONE,[f.t,f.n,Vector((0,0,1))])
    lathe(b,q.xy,[(37.74,1.4),(37.98,1.35),(38.28,1.18),(38.48,.85),(38.64,.3),(38.67,0)],TRIM,36)
    # Small corner acroteria observed around the shallow dome.
    for su in [-1,1]:
        for sd in [-1,1]:
            p=q+f.t*su*1.35+f.n*sd*1.35;b.box((p.x,p.y,38.0),(.18,.18,.55),TRIM)
    b.cylinder((q.x,q.y,39.42),.025,1.16,METAL,10)
    # Reference photograph has simple red flags; flags are geometric cloth, not textures.
    pts=[]
    for j in range(6):
        for z in [39.8,39.15]:
            pt=q+f.t*(j*.15)+f.n*(math.sin(j*.9)*.05)+Vector((0,0,z));pts.append(pt)
    b.geom(pts,[(2*j,2*j+2,2*j+3,2*j+1) for j in range(5)],RED)

def make_news(c):
    b=Builder();p=c['polygon_local_east_north'];b.outline([(x*.90,y*.90) for x,y in p],0,33.7,DARK);b.outline(p,0,.35,STONE);fs=edge_facades(b,p);f=fs[2];L=f.L
    wing=3.55;wc=L/2-wing/2;central=L-2*wing
    # Side and back are secondary, kept consistent with mapped slender/deep building.
    for idx,g in enumerate(fs):
        if idx==2:continue
        n=max(3,round(g.L/3.85));bw=g.L/n
        for j in range(n):
            u=-g.L/2+(j+.5)*bw
            for k,(lo,hi) in enumerate([(0,4.5),(4.5,9.0)]+[(9+i*3.6,12.6+i*3.6) for i in range(5)]+[(27,33.7)]):
                g.cell(u,bw,lo,hi,min(1.65,bw*.6),lo+.8,hi-.6,False)
        for z in [9,27,33.7]:g.beam(z,.32,.35)
    # Two double-height giant arched wings, with inset doors/sign panels below.
    for s in [-1,1]:
        u=s*wc
        facade_band(f,0,9,[(u,2.25,.15,8.5,True)],u-wing/2,u+wing/2)
        f.box(u,4.6,2.12,2.35,.24,-.02,TRIM)
        # Projecting coarse rusticated blocks: eleven true stone courses.
        for j in range(13):
            z=.35+j*.65
            for side in [-1,1]:
                f.box(u+side*(wing/2-.34),z,.65,.48,.40,.12,STONE)
        f.rail(u,9.15,3.05,.77,True)
        f.box(u,8.95,3.65,.35,1.05,.22,TRIM)
    recessed=Facade(b,(f.a-f.n*.60).xy,(f.c-f.n*.60).xy)
    facade_band(recessed,0,4.7,[(-3.5,1.2,.5,4.4,False),(0,3.15,.5,4.4,False),(3.5,1.2,.5,4.4,False)],-central/2,central/2)
    facade_band(recessed,4.7,9.0,[(-3.5,1.2,6.35,8.65,False),(0,3.15,6.35,8.65,False),(3.5,1.2,6.35,8.65,False)],-central/2,central/2)
    for u in [-2.4,2.4]:
        q=f.p(u,0,.17);flute_column(b,q.xy,.38,8.8,.42)
    f.beam(9.15,.34,.6)
    f.rail(0,.47,7.8,.80,True)
    # Three low-relief narrative panels are present in the real central entrance band.
    for u in [-3.55,0,3.55]:
        f.box(u,5.50,2.6,1.20,.15,-.04,TRIM)
        for j in range(5):
            uu=u+(j-2)*.40;q=f.p(uu,5.9,.06)
            b.cylinder(q,.08,.08,STONE,12,f.n)
            f.line(uu,5.80,uu-.08,5.20,.10,.12,.07,STONE)
            f.line(uu,5.65,uu+.19,5.40,.07,.09,.07,STONE)
    # Five middle floors; wing axes are wider and the central triplet is NOT uniform.
    layout=[(-wc,1.95),(-3.55,1.12),(-1.23,.50),(0,1.42),(1.23,.50),(3.55,1.12),(wc,1.95)]
    for k in range(5):
        z0=9.4+k*3.51;z1=z0+3.51
        facade_band(f,z0,z1,[(u,w,z0+.68,z1-.62,False) for u,w in layout])
        for u in [-wc,wc]:
            f.box(u,z0+.53,2.3,.14,.30,.07,TRIM)
        f.box(0,z0+.53,3.60,.13,.30,.07,TRIM)
    for s in [-1,1]:
        for u in [s*(wc-wing/2+.10),s*(L/2-.13)]:f.box(u,18.1,.20,17.5,.25,.04,TRIM)
    # A prominent sculptural cornice terminates the seven-storey main facade.
    f.beam(27.10,.24,.35);f.beam(27.70,.50,.95);f.beam(28.10,.24,1.08);f.dentils(27.37,.42)
    for u in [-L/2+.35,-central/2+.05,central/2-.05,L/2-.35]:atlas(b,f,u)
    # Recessed top loggia and two end pavilions, with real openings and columns.
    top=Facade(b,(f.a-f.n*.55).xy,(f.c-f.n*.55).xy)
    for s in [-1,1]:
        u=s*wc
        top.cell(u,wing,28.22,33.72,1.8,29.15,32.6,True)
        top.rail(u,29.2,2.1,.65,False);top.pediment(u,33.52,3.65)
        for e in [-1,1]:top.box(u+e*(wing/2-.18),30.95,.22,4.75,.17,.08,TRIM)
        news_tower(b,f,u)
    # Actual open balcony: dark rear wall is 1.8 m behind the columns.
    back=Facade(b,(f.a-f.n*1.8).xy,(f.c-f.n*1.8).xy)
    facade_band(back,28.22,33.72,[(-3.15,1.8,29.25,32.9,False),(0,1.8,29.25,32.9,False),(3.15,1.8,29.25,32.9,False)],-central/2,central/2)
    top.rail(0,28.45,central,.84,False)
    for u in [-4.7,-1.56,1.56,4.7]:
        q=f.p(u,0,-.42);flute_column(b,q.xy,28.62,33.56,.20)
    top.beam(33.73,.27,.38);top.beam(34.04,.18,.45);top.dentils(33.5,.34)
    # Red AIA letters in the current photograph, built as original mesh strokes.
    for center,letter in [(-1.75,'A'),(0,'I'),(1.75,'A')]:
        if letter=='A':
            f.line(center-.68,28.15,center,29.85,.23,.20,.58,RED);f.line(center,29.85,center+.68,28.15,.23,.20,.58,RED)
            f.line(center-.42,28.75,center+.42,28.75,.19,.20,.58,RED)
        else:f.line(center,28.15,center,29.85,.24,.20,.58,RED)
    b.outline(p,33.73,33.9,ROOF)
    return b,{'observedMainFacadeLevels':'2 rusticated lower floors + 5 middle rows + recessed attic loggia + twin small roof pavilions',
      'osmLevels':10,'publishedAlternativeLevels':9,'modelHeightM':40.0,
      'heightStatus':'40 m is a photo-proportioned working estimate, not a verified or surveyed height. Public search snippets with more precise numbers were not accepted as primary evidence.',
      'facadeStructure':'Narrow riverfront 17.415 m; two wider wing axes flank narrow central openings and a triplet. Fluted two-storey entrance columns, coarse stone blocks, relief frieze, cornice atlantes, recessed colonnaded loggia, twin shallow-domed pavilions.',
      'estimatedGeometry':['All vertical elevations','Relief figures simplified','Sculptural atlantes simplified','Side/rear window spacing','Top loggia column spacing','Flag length'],
      'references':['https://en.wikipedia.org/wiki/North_China_Daily_News_Building','https://zh.wikipedia.org/wiki/字林大楼','https://commons.wikimedia.org/wiki/File:North_China_Daily_News_Building_20250501.jpg']}

if __name__=='__main__':
    c=json.loads((HERE/'news-footprint.json').read_text());b,d=make_news(c)
    out=Path(os.environ.get('BUND_CLASSICS_OUTPUT',str(HERE/'output')));out.mkdir(parents=True,exist_ok=True)
    export(c,b,d,out)
