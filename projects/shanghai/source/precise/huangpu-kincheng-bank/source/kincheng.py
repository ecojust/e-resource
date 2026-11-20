"""Jiangxi Middle Road street block. Viewer right is south along the street; Y goes into the building."""
from math import cos, pi, sin
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering


FONT = Path(__file__).with_name('fonts') / 'JiangxiBankPlaque.otf'
PALETTE = {
    'Jinshan granite': {'color':[.44,.43,.40],'roughness':.82},
    'dressed granite': {'color':[.52,.50,.46],'roughness':.74},
    'granite joint': {'color':[.33,.32,.29],'roughness':.89},
    'bronze sash': {'color':[.15,.15,.13],'metallic':.33,'roughness':.44},
    'bank glazing': {'color':[.13,.17,.19],'roughness':.32,'metallic':.15},
    'dark plaque': {'color':[.19,.19,.17],'roughness':.69},
    'roof': {'color':[.33,.32,.28],'roughness':.94},
    'unverified wall': {'color':[.41,.40,.37],'roughness':.88},
}
STONE='Jinshan granite'
TRIM='dressed granite'
HALF=17.72
DEPTH=19.96
MAIN=22.45
ROOF=29.48


def panel(f,u,z,width,height,material,projection=.09,name='panel'):
    f.box(u,z,width,height,projection+.03,projection/2-.015,material,name)


def glazing(f,hole,lod,cols,rows,name):
    xmin,zmin,xmax,zmax=hole.bounds
    pane=hole.buffer(-.073,join_style='mitre')
    f.prism(hole.buffer(.011,join_style='mitre'),-.37,-.35,'bank glazing',name+' glazing')
    grid=[]
    for idx in range(1,cols if not lod else min(2,cols)):
        u=xmin+(xmax-xmin)*idx/(cols if not lod else min(2,cols))
        grid.append(box(u-.029,zmin,u+.029,zmax))
    for idx in range(1,rows if not lod else min(2,rows)):
        z=zmin+(zmax-zmin)*idx/(rows if not lod else min(2,rows))
        grid.append(box(xmin,z-.028,xmax,z+.028))
    panes=pane.difference(unary_union(grid)) if grid else pane
    f.prism(hole.buffer(-.021,join_style='mitre').difference(panes),-.30,-.21,
            'bronze sash',name+' frame')
    panel(f,(xmin+xmax)/2,zmin-.055,xmax-xmin+.13,.11,TRIM,.13,name+' sill')


def belt(f,z,height,projection,mat=TRIM,label='belt course'):
    f.box(0,z,f.length,height,projection+.20,(projection-.20)/2,mat,label)


def rustication(f,wallshape,bottom,top,lod):
    # Low-relief blocks leave real narrow mortar joints, including at the windows.
    rows=max(1,round((top-bottom)/.72))
    count=max(1,round(f.length/1.8))
    dx=f.length/count
    for k in range(rows):
        z=bottom+(top-bottom)*k/rows
        ztop=bottom+(top-bottom)*(k+1)/rows
        for j in range(-1,count+1):
            left=-f.length/2+j*dx+(k%2)*dx/2
            rect=box(left+.019,z+.022,left+dx-.019,ztop-.020)
            piece=wallshape.intersection(rect)
            if piece.area>.015:
                f.prism(piece,.003,.043 if lod else .055,STONE,'ashlar courses')


def opening_with_head(f,u,bottom,w,h,lod,label):
    # The short segmental head is a blind stone tympanum above the glass.
    shape=opening(u,bottom,w,h,.73,12 if lod else 26)
    glazing(f,shape,lod,3,4,label)
    _,_,_,top=shape.bounds
    cap=shape.intersection(box(u-w/2,top-.73,u+w/2,top))
    f.prism(cap,-.16,-.12,TRIM,label+' blind head')
    key=Polygon([(u-.16,top-.03),(u+.16,top-.03),(u+.29,top+.69),(u-.29,top+.69)])
    f.prism(key,-.01,.14,TRIM,label+' keystone')
    return shape


def main_segment(b,x1,x2,y,section,lod):
    f=Facade(b,(x1,y),(x2,y),section)
    holes=[]
    if section=='Central entrance':
        door=opening(0,.09,3.97,4.31)
        holes.append(door)
        f.prism(door,-1.64,-1.61,'dark plaque','doorway backstop')
        frame=door.buffer(.11,join_style='mitre').difference(door).intersection(box(-2.3,0,2.3,4.7))
        f.prism(frame,-1.62,-.32,TRIM,'door reveal')
        for u in [-1.57,1.57]:
            c=f.point(u,0,.18)
            section_profile=[(.08,.28),(.16,.33),(.32,.30),(.42,.248),(4.00,.225),
                             (4.13,.25),(4.20,.32),(4.30,.34),(4.39,.34)]
            b.lathe(c[:2],section_profile,TRIM,16 if lod else 36,'Central entrance/Doric shafts')
            if not lod:
                for j in range(16):
                    a=2*pi*j/16
                    b.tube([(c[0]+.242*cos(a),c[1]+.242*sin(a),.46),
                            (c[0]+.225*cos(a),c[1]+.225*sin(a),3.99)],
                           .014,'granite joint',5,'Central entrance/fluting')
        h=opening(0,5.62,3.88,5.0)
        holes.append(h);glazing(f,h,lod,4,4,'upper door light')
        h=opening(0,13.05,4.14,4.3,1.84,12 if lod else 30)
        holes.append(h);glazing(f,h,lod,4,3,'central roundhead')
        for u in [-1.73,0,1.73]:
            h=opening(u,18.3,1.28,2.85);holes.append(h);glazing(f,h,lod,2,3,'top gallery')
        panel(f,0,12.25,4.25,.94,TRIM,.10,'stone sign')
        add_facade_lettering(f,'交通银行',0,12.24,3.22,.63,.115,.159,
                            'bronze sash',label='current user name',font=FONT)
        hood=Polygon([(-2.05,10.68),(2.05,10.68),(0,11.57)])
        f.prism(hood,-.008,.17,'bronze sash','pediment above upper sash')
        f.prism(LineString([(-2.07,10.67),(0,11.60),(2.07,10.67)]).buffer(.08,cap_style='flat',join_style='mitre'),
                .17,.25,'dark plaque','pediment raking edges')
        # Two scroll shoulders rise to a central crest. The motif is indistinct.
        top=[(-2.10,5.32),(-1.53,5.39),(-1.02,5.58),(-.57,5.98),(-.34,6.10),
             (0,6.05),(.34,6.10),(.57,5.98),(1.02,5.58),(1.53,5.39),(2.10,5.32)]
        crest=Polygon([(-2.1,4.54),(2.1,4.54),*reversed(top)])
        f.prism(crest,0,.23,TRIM,'entrance crest wall')
        f.prism(LineString(top).buffer(.085,cap_style='flat',join_style='mitre'),
                .21,.32,STONE,'scroll shoulders')
        ring=Point(0,5.32).buffer(.53,quad_segs=8 if lod else 18)
        f.prism(ring.difference(ring.buffer(-.071)),.24,.31,TRIM,'round relief border')
        # Figure-ground of the emblem only; no invented dragon or axe carving.
        f.prism(ring.buffer(-.115),.235,.268,STONE,'round relief field')
        # Shallow bowed balcony, at the level above the half-round central window.
        balcony=[(u, y-.29-.41*(1-(u/1.86)**2)) for u in [-1.86,-1.39,-.93,-.46,0,.46,.93,1.39,1.86]]
        footprint=Polygon([*balcony,(1.86,y+.17),(-1.86,y+.17)])
        b.plan_prism(footprint,17.50,17.73,TRIM,'Central entrance/curved balcony slab')
        lip=LineString(balcony).buffer(.095,cap_style='flat')
        b.plan_prism(lip,17.71,18.29,STONE,'Central entrance/curved balcony front')
        b.plan_prism(lip.buffer(.05,join_style='mitre'),18.29,18.42,TRIM,'Central entrance/balcony coping')
    elif 'Recess' in section:
        step=f.length/3
        for j,u in enumerate([-step,0,step]):
            for z,w,h,n in [(.68,1.35,2.92,'base grille'),(13.12,1.54,3.35,'third storey'),(18.29,1.55,2.82,'upper sash')]:
                hole=opening(u,z,w,h);holes.append(hole);glazing(f,hole,lod,2,4,n)
            holes.append(opening_with_head(f,u,5.08,1.69,5.66,lod,'monumental sash'))
            panel(f,u,12.46,1.42,.49,STONE,.12,'relief cartouche')
            if not lod:
                for idx in (-1,0,1):
                    w=.25
                    med=Polygon([(u+idx*.35-w,12.44),(u+idx*.35,12.61),
                                 (u+idx*.35+w,12.44),(u+idx*.35,12.29)])
                    f.prism(med,.125,.17,TRIM,'cartouche raised leaves')
    else:
        end_arch=opening(0,5.04,3.10,6.28,1.48,12 if lod else 32)
        holes.append(end_arch);glazing(f,end_arch,lod,4,5,'fully glazed end arch')
        arch_band=end_arch.buffer(.18,join_style='mitre').difference(end_arch)
        f.prism(arch_band.intersection(box(-2,8.40,2,11.65)),-.02,.115,TRIM,'dressed archivolt')
        panel(f,0,11.52,.57,.61,TRIM,.20,'end arch keystone')
        hole=opening(0,.7,2.09,2.88);holes.append(hole);glazing(f,hole,lod,4,4,'base grille')
        for u in (-.92,.92):
            hole=opening(u,13.0,1.45,3.78);holes.append(hole);glazing(f,hole,lod,2,4,'paired tall lights')
        for u in (-1.32,0,1.32):
            hole=opening(u,18.43,1.05,2.69);holes.append(hole);glazing(f,hole,lod,2,3,'triplet')
        stone_disc=Point(0,17.72).buffer(.44,quad_segs=8 if lod else 15)
        f.prism(stone_disc.difference(stone_disc.buffer(-.047)),.01,.055,TRIM,'spandrel medallion')
    wall=f.wall(0,MAIN,holes,.38,STONE)
    rustication(f,wall,.0,4.41,lod)
    if 'Recess' not in section and not lod:
        for u in (-f.length/2+.24,f.length/2-.24):
            stone=wall.intersection(box(u-.225,4.49,u+.225,21.40))
            for j in range(25):
                h=4.49+j*.68
                f.prism(stone.intersection(box(u-.26,h+.017,u+.26,h+.66)),
                        .008,.062,STONE,'coursed pilaster')
    for z,h,off in [(4.49,.19,.25),(21.65,.17,.22),(22.04,.40,.42),(22.39,.16,.49)]:
        belt(f,z,h,off)
    for j in range(max(3,round(f.length/.54))):
        count=max(3,round(f.length/.54));u=(j+.5)*f.length/count-f.length/2
        panel(f,u,21.86,.20,.25,TRIM,.33,'cornice modillion')


def roof_storeys(b,x1,x2,y,label,lod):
    f=Facade(b,(x1,y),(x2,y),label)
    pitch=f.length/3
    holes=[]
    end=label.startswith(('North end','South end'))
    if end:
        arch=opening(0,22.71,3.27,2.39,1.48,12 if lod else 30)
        holes.append(arch);glazing(f,arch,lod,4,2,'attic arch')
        arch_ring=arch.buffer(.15,join_style='mitre').difference(arch)
        f.prism(arch_ring.intersection(box(-2,23,2,25.4)),-.01,.12,TRIM,'attic archivolt')
    for u in (-pitch,0,pitch):
        for z,h in ([(26.09,2.32)] if end else [(23.15,1.45),(26.09,2.32)]):
            w=min(pitch*.66,1.53)
            hole=opening(u,z,w,h);holes.append(hole);glazing(f,hole,lod,2,2,'addition sash')
    f.wall(MAIN,ROOF,holes,.33,STONE)
    for z,h,p in [(25.25,.22,.19),(28.95,.29,.25),(29.48,.22,.25)]:
        belt(f,z,h,p)


def add_bank(b,lod):
    spans=[(-HALF,-13.02,.12,'North end'),(-13.02,-3.72,.55,'Recess north'),
           (-3.72,3.72,.08,'Central entrance'),(3.72,13.02,.55,'Recess south'),
           (13.02,HALF,.12,'South end')]
    for x1,x2,y,label in spans:
        main_segment(b,x1,x2,y,label,lod)
        roof_storeys(b,x1,x2,y+.26,label+' roof storeys',lod)
    for x in (-13.02,-3.72,3.72,13.02):
        b.box((x,.34,MAIN/2),(.13,.48,MAIN),STONE,label='Street wall/projected return')
        b.box((x,.62,(MAIN+ROOF)/2),(.12,.52,ROOF-MAIN),STONE,label='Addition/return')
    full_plan=box(-HALF,.55,HALF,DEPTH)
    b.plan_prism(full_plan,0,.12,'granite joint','Street block/base')
    b.plan_prism(box(-HALF,.13,HALF,DEPTH),MAIN-.17,MAIN,TRIM,'Street block/addition sill')
    b.plan_prism(box(-HALF,.42,HALF,DEPTH),ROOF-.23,ROOF,'roof','Street block/roof')
    for x in (-HALF,HALF):
        b.box((x,(DEPTH+.51)/2,MAIN/2),(.23,DEPTH-.51,MAIN),
              'unverified wall',label='Street block/end closures')
        b.box((x,(DEPTH+.74)/2,(MAIN+ROOF)/2),(.22,DEPTH-.74,ROOF-MAIN),
              'unverified wall',label='Addition/end walls')
        b.box((x,(DEPTH+.74)/2,ROOF+.13),(.26,DEPTH-.74,.28),STONE,label='Addition/side roof edge')
    b.box((0,DEPTH-.13,ROOF/2),(HALF*2,.26,ROOF),'unverified wall',label='Street block/rear cut')
    b.box((0,DEPTH-.13,ROOF+.13),(HALF*2,.26,.28),STONE,label='Addition/rear roof edge')
