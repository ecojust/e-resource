"""Embankment House as recorded in the 2022 repair views and the 2025 river photograph."""
from pathlib import Path
import math,sys
from shapely.geometry import box,Polygon,LineString
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder,Facade
from river_geometry import HEIGHT,GROUND,FLOOR,segments,footprint,frontage,pavilion

SAND='warm exposed aggregate';BUFF='light buff bands';DARK='brown face brick';BROWN='brick joint';SASH='dark steel casement'
GLASS='smoky blue-grey glass';DOOR='oxidised bronze leaf';IRON='black balcony guard';ROOF='grey roof';BACK='cut backing';BASE='grey granite plinth';GLASS2='infilled balcony glazing'
def sw(rgb,rough=.79,metal=0):return {'color':list(rgb),'roughness':rough,'metallic':metal}
PALETTE={SAND:sw((.58,.45,.281)),BUFF:sw((.69,.55,.366)),DARK:sw((.273,.112,.075)),BROWN:sw((.19,.115,.091)),
         SASH:sw((.065,.076,.066),.53,.3),GLASS:sw((.114,.169,.18),.34,.25),GLASS2:sw((.155,.204,.202),.40,.19),
         DOOR:sw((.192,.12,.093),.6,.17),IRON:sw((.12,.122,.099),.57,.38),ROOF:sw((.277,.270,.243)),BACK:sw((.412,.38,.32)),BASE:sw((.42,.40,.33))}

def window(f,u,z,w,h,cells,lod,door=False,back=.22,infilled=False):
    glass=DOOR if door else GLASS2 if infilled else GLASS
    f.box(u,z+h/2,w,h,.039,-back,glass,'recessed glazing')
    def bar(cx,cz,width,height):
        if lod:
            # Distant steel bars retain their visible front faces without hidden backs.
            verts=[f.point(cx+dx*width/2,cz+dz*height/2,-back+.08) for dx,dz in [(-1,-1),(1,-1),(1,1),(-1,1)]]
            f.builder.add(verts,[(0,1,2,3)],SASH,f.label+'/steel glazing bars')
        else:
            f.box(cx,cz,width,height,.06,-back+.05,SASH,'steel glazing bars')
    count=max(2,round(cells*.52))if lod else cells
    for k in range(count+1):
        bar(u-w/2+k*w/count,z+h/2,.048 if k in (0,count) else .035,h)
    for hfrac in ((0,.66,1) if lod or not door else(0,.34,.68,1)):
        bar(u,z+h*hfrac,w,.050)
    return box(u-w/2,z,u+w/2,z+h)

def balcony(f,u,bottom,w,lod,open_guard):
    f.box(u,bottom+.12,w+.27,.22,.81,.26,BUFF,'cantilever balcony sill')
    for sign in (-1,1):f.box(u+sign*(w/2-.04),bottom+.57,.11,.94,.69,.26,BUFF,'balcony cheeks')
    if open_guard:
        f.box(u,bottom+1.02,w,.058,.047,.645,IRON,'top guard rail')
        f.box(u,bottom+.41,w,.044,.044,.645,IRON,'lower guard rail')
        n=max(2,round(w/(.53 if lod else .28)))
        for k in range(n+1):f.box(u-w/2+k*w/n,bottom+.71,.034,.64,.041,.645,IRON,'vertical balusters')
    else:f.box(u,bottom+.62,w,.81,.12,.615,SAND,'solid balcony apron')

def brown_bands(f,lod):
    # The before-repair aerial and opposite-bank photograph both show four vertical bays.
    edges=[-46.15,-24.13,8.65,36.18]
    center=(f.a[0]+f.b[0])*.5
    for x in edges:
        u=x-center
        for side in (-1,1):
            f.box(u+side*.87,(HEIGHT+GROUND)/2,.50,HEIGHT-GROUND,.10,.054,DARK,'face brick stair bay')
            f.box(u+side*1.18,(HEIGHT+GROUND)/2,.14,HEIGHT-GROUND+.43,.19,.082,BUFF,'raised ends of pilaster')
        f.box(u,HEIGHT+.31,2.53,.59,.29,.06,BUFF,'brick bay parapet cap')
    return edges

def flat_face(f,lod,kind):
    L=f.length
    long=kind=='long';head=kind=='court head'
    if long:
        center=(f.a[0]+f.b[0])/2
        absolute=brown_bands(f,lod)
        cores=[x-center for x in absolute]
        divided=[-L/2,*cores,L/2];layout=[]
        for i,(a,b)in enumerate(zip(divided,divided[1:])):
            left=a+(1.44 if i else .40);right=b-(1.44 if i<len(divided)-2 else .42)
            width=right-left
            if width<1.1:continue
            if width<5:layout.append(((left+right)/2,width*.73,3,'plain'));continue
            slots=max(1,round(width/8.5))
            for k in range(slots):
                start=left+k*width/slots;span=width/slots
                layout.append((start+span*.305,span*.54,max(3,round(span*.80)),'wide'))
                layout.append((start+span*.806,span*.176,2,'single'))
    else:
        count=max(1,round(L/(5.10 if head else 4.67)));span=L/count
        layout=[(-L/2+(j+.5)*span,span*(.64 if j%3 else .72),4 if j%3 else 5,'wide' if j%3==1 else 'plain') for j in range(count)]
        cores=[]
    for level in range(10):
        floor=0 if level==0 else GROUND+(level-1)*FLOOR
        hi=GROUND if level==0 else floor+FLOOR
        holes=[]
        for u in cores:
            if level:
                holes.append(window(f,u,floor+.52,1.18,1.98,2,lod))
                f.box(u,floor+.25,2.15,.53,.105,.048,DARK,'brick spandrels')
                f.box(u,hi-.29,2.15,.60,.105,.048,DARK,'brick spandrels')
        for j,(u,width,cells,typ)in enumerate(layout):
            if level==0:
                entrance=head and j==len(layout)//2
                lower=.10 if entrance else .57
                w=min(width,2.62 if entrance else 2.90)
                holes.append(window(f,u,lower,w,2.46-lower,cells if cells<5 else 4,lod,entrance))
                if entrance:
                    f.box(u,2.83,w+.80,.21,.74,.37,BUFF,'court entrance canopy')
                continue
            w=width; z=floor+.60;h=2.02
            rails_here=typ=='wide' and (j%3==1 or ((level+j)%4)==1)
            if rails_here:
                balcony(f,u,floor+.08,w,lod,open_guard=(level+j)%3!=0)
                holes.append(window(f,u,floor+.28,w,2.39,cells,lod,back=.48,infilled=(level+j)%3==0))
            else:
                holes.append(window(f,u,z,w,h,cells,lod))
                if typ=='wide':
                    f.box(u,z-.071,w+.25,.12,.23,.065,BUFF,'washed stone window sill')
        f.wall(floor,hi,holes,thickness=.15,material=BASE if level==0 else SAND)
    f.box(0,GROUND-.045,L,.17,.28,.065,BUFF,'plinth string')
    f.box(0,HEIGHT-.19,L,.35,.34,.091,BUFF,'continuous top cornice')

def curved_face(f,lod):
    # Each short chord is one piece of the continuously turning bank of windows.
    L=f.length
    for level in range(10):
        floor=0 if level==0 else GROUND+(level-1)*FLOOR;hi=GROUND if level==0 else floor+FLOOR
        if level==0:
            width=max(.50,L*.63);holes=[window(f,0,.54,width,1.86,max(2,round(width/.68)),lod)]
        else:
            width=L-.13;holes=[window(f,0,floor+.58,width,2.08,max(2,round(width/.57)),lod)]
            f.box(0,floor+.32,L+.012,.50,.29,.08,BUFF,'curved concrete spandrel')
            f.box(0,hi-.16,L+.012,.16,.25,.079,BUFF,'thin continuous drip')
        f.wall(floor,hi,holes,thickness=.15,material=BASE if level==0 else SAND)
    f.box(0,HEIGHT-.18,L+.035,.34,.35,.096,BUFF,'ribbon parapet cap')

def slab(b,path,bottom,top,mat,key):
    b.plan_prism(path,bottom,top,mat,key)

def corner_pavilion(b,lod):
    p=pavilion();wall=p.exterior.coords;z=HEIGHT
    slab(b,p.buffer(.19,join_style='mitre'),z-.23,z+.23,BUFF,'roof belvedere/base cornice')
    for i,(a,c) in enumerate(zip(wall,list(wall)[1:])):
        f=Facade(b,a,c,'roof belvedere drum')
        f.wall(z+.17,z+1.22,[window(f,0,z+.51,f.length*.57,.41,2,lod)],thickness=.15,material=SAND)
    slab(b,p.buffer(.22,join_style='mitre'),z+1.18,z+1.43,BUFF,'roof belvedere/drum sill')
    # The level above the drum is open between substantial edge posts.
    for j,(x,y)in enumerate(list(wall)[:-1]):
        if j%2:continue
        b.box((x,y,z+2.90),(.36,.36,2.97),SAND,label='roof belvedere/open pavilion posts')
    slab(b,p.buffer(.19,join_style='mitre'),z+4.36,z+4.60,BUFF,'roof belvedere/pavilion upper lip')
    slab(b,p.buffer(.08,join_style='mitre'),z+4.60,z+5.34,SAND,'roof belvedere/polygonal crown')
    slab(b,p.buffer(.19,join_style='mitre'),z+5.32,z+5.51,BUFF,'roof belvedere/stepped coping')

def build_apartments(b,lod):
    for name,line,kind in segments():
        for a,c in zip(line,line[1:]):
            f=Facade(b,a,c,name)
            if kind=='ribbon':curved_face(f,lod)
            else:flat_face(f,lod,kind)
    base=footprint().union(pavilion().buffer(.26,join_style='mitre'))
    slab(b,base,0,.14,BASE,'river wall/ground base')
    slab(b,base,HEIGHT-.19,HEIGHT,ROOF,'river wall/flat roof')
    # Close each exposed section behind the measured facade. Leave the old
    # courtyard and street wings visible beyond the four-metre front strip.
    rest=base.boundary.difference(frontage().buffer(.025))
    for line in getattr(rest,'geoms',[rest]):
        for a,c in zip(line.coords,list(line.coords)[1:]):
            if math.dist(a,c)>.012:
                Facade(b,c,a,'unexposed rear cut').wall(0,HEIGHT,material=BACK,thickness=.072)
    corner_pavilion(b,lod)
