"""Build three photo-referenced Bund buildings, without image textures.

Run from any directory:
  blender --background --threads 2 --python build_art_deco.py -- peace_north
  blender --background --threads 2 --python build_art_deco.py -- bank_china
  blender --background --threads 2 --python build_art_deco.py -- peace_south

The source coordinate frame is local east/north/up in metres. Blender's glTF
export converts this to east/up/south, preserving the WGS84 anchor in metadata.
Facade proportions and unobserved rear elevations are interpretive, not surveys.
"""
import bpy, math, json, sys, os
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from architecture import Builder,Facade,perimeter,roof,flag,make_materials
DATA=json.loads((HERE/'footprints.json').read_text())

def reset():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for m in list(bpy.data.materials):bpy.data.materials.remove(m)
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1

def walls(b,poly,z0,z1,nfloors,style='north',ground=False,inside=False,front_specific=False):
    for f in perimeter(b,poly):
        if inside:f.n=-f.n
        if f.length<.7:
            f.panel(0,f.length,z0,z1,0);continue
        is_front=f.n.x>.95 and (f.a.x>70 if style=='north' else True)
        n=9 if style=='north' and is_front and f.length>15 else max(1,round(f.length/(3.55 if style=='north' else 4.4)))
        pitch=f.length/n
        if ground:
            if style=='north' and not inside and f.length>12:
                arches=3 if is_front else max(1,round(f.length/6.2))
                for i in range(arches):
                    p=f.length/arches;f.arch((i+.5)*p,.25,z0+5.1,min(2.0,p*.34),z1,i*p,(i+1)*p,joints=True)
            elif style=='south' and not inside and f.length>3:
                arches=max(1,round(f.length/4.6));p=f.length/arches
                for i in range(arches):f.arch((i+.5)*p,.20,3.2,min(1.45,p*.34),z1,i*p,(i+1)*p,joints=True)
            else:
                for i in range(n):f.cell(i*pitch,(i+1)*pitch,z0,z1,pitch*.5,(z1-z0)*.60,m=0,center=(z0+z1)/2,joints=not inside)
            f.cornice(z1-.1);continue
        dz=(z1-z0)/nfloors
        if style=='north' and is_front and nfloors==1 and z0>45:
            gp=f.length/3
            for group in [0,2]:
                for i in range(3):
                    a=group*gp+i*gp/3;c=a+gp/3
                    f.cell(a,c,z0,z1,1.12,2.7,center=50.0,joints=True)
            for i in range(3):
                a=gp+i*gp/3;f.cell(a,a+gp/3,z0,50.8,1.12,2.5,center=48.7,joints=True)
            f.arch(f.length/2,50.8,52.1,1.35,z1,gp,2*gp,joints=True)
            f.cornice(z1-.10)
            continue
        if style=='north' and not inside and nfloors>2:
            # Sassoon House's defining continuous narrow window bands. Piers
            # run for the whole elevation; spandrels sit behind them, not on a
            # generic grid of projecting classical sills.
            if is_front and f.length>15:
                centers=[(g+.5)*f.length/3+offset for g in range(3) for offset in [-1.50,0,1.50]];ww=1.12
            else:
                centers=[(i+.5)*pitch for i in range(n)];ww=min(1.42,pitch*.59)
            prev=0
            for u in centers:
                f.panel(prev,u-ww/2,z0,z1,0,joints=True);prev=u+ww/2
            f.panel(prev,f.length,z0,z1,0,joints=True)
            for u in centers:
                for sign in [-1,1]:f.box(u+sign*(ww/2+.105),(z0+z1)/2,.135,z1-z0,.25,0,.15)
                for j in range(nfloors):
                    lo=z0+dz*j;hi=lo+dz;z=(lo+hi)/2;wh=dz*.64
                    for a,c in [(lo,z-wh/2),(z+wh/2,hi)]:
                        f.box(u,(a+c)/2,ww,c-a,.48,14,-.12)
                    f.window(u,z,ww,wh,stone=0,deep=.36,sill=False)
                    # Stepped slim Art-Deco panel border, visible in raking light.
                    h=dz*.26;zz=lo+h/2+.07
                    for sign in [-1,1]:f.flat(u+sign*(ww/2-.14),zz,.045,h,1,-.07)
                    f.flat(u,lo+.10,ww-.25,.045,1,-.07)
            f.cornice(z1-.45);f.box(f.length/2,z1+.35,f.length,.7,.5,0,.08)
            for i in range(max(1,int(f.length/1.25))):
                u=(i+.5)*f.length/max(1,int(f.length/1.25));f.box(u,z1+.38,.45,.42,.09,1,.16)
            continue
        for j in range(nfloors):
            lo=z0+dz*j;hi=lo+dz
            for i in range(n):
                width=min(1.38,pitch*.58) if style=='north' else min(2.3,pitch*.6)
                f.cell(i*pitch,(i+1)*pitch,lo,hi,width,dz*.60,m=0,joints=not inside,spandrel=0 if style=='north' and not inside else None)
                if style=='north' and not inside:
                    u=(i+.5)*pitch;bottom=lo+.12;hh=dz*.25
                    # Shallow recessed Art-Deco spandrel bordered by two ribs.
                    for sign in [-1,1]:f.flat(u+sign*(width/2-.14),bottom+hh/2,.055,hh,1,.08)
                    f.flat(u,bottom+.06,width-.27,.055,1,.08)
        if not inside:
            f.cornice(z1-.5)
            for i in range(n+1):
                if i%3==0:f.box(i*pitch,(z0+z1)/2,.38,z1-z0,.30,0,.20)
            # Parapet blocks and circular shallow reliefs.
            f.box(f.length/2,z1+.35,f.length,.7,.5,0,.08)
            for i in range(max(1,int(f.length/1.25))):
                u=(i+.5)*f.length/max(1,int(f.length/1.25));f.box(u,z1+.38,.45,.42,.09,1,.16)

def north():
    d=DATA['bund20'];builders=[]
    b=Builder('01 Ground arches, sandstone piers and bronze doors');builders.append(b)
    walls(b,d['exterior'],0,8.4,1,ground=True)
    b=Builder('02 Hotel masonry, genuine window reveals and Art-Deco vertical ribs');builders.append(b)
    walls(b,d['exterior'],8.4,46.8,8)
    # Courtyard holes remain open; their elevations are simpler and explicitly inferred.
    b=Builder('03 Three open courtyards, rear windows, floor and roof slabs');builders.append(b)
    for p in d['holes']:
        rev=list(reversed(p));walls(b,rev,.3,46.8,9,inside=True)
    roof(b,d['roof_triangles'],46.8)
    roof(b,d['roof_triangles'],.05,8)
    # Eastern pavilion follows the clipped true footprint and stands above wings.
    e=d['eastern_upper'];b=Builder('04 Stepped eastern pavilion and projecting central balcony');builders.append(b)
    walls(b,e['exterior'],46.8,53.6,1)
    roof(b,e['roof_triangles'],53.6)
    front=next(f for f in perimeter(b,e['exterior']) if f.n.x>.95 and f.length>15)
    mid=front.length/2
    front.box(mid,50.1,7.0,.50,2.1,1,1.5)
    front.box(mid,51.0,7.0,1.3,.4,0,1.5)
    for u in [mid-3.25,mid-2.2,mid-1.1,mid,mid+1.1,mid+2.2,mid+3.25]:front.box(u,51,.35,1.3,.18,1,1.62)
    for sign in [-1,1]:
        # Stepped stone corbels below the real projecting balcony.
        for k in range(4):front.box(mid+sign*2.7,49.7-k*.32,.60,.30,1.8-k*.35,1,1.3-k*.20)
    front.crest(mid,8.0,1.5,1.6)
    # Penthouse tower: independent inset volume, wrapped elevations, guarded terrace.
    b=Builder('05 Penthouse, sculpted frieze and terrace balustrades');builders.append(b)
    poly=[(54,-10.8),(77,-10.8),(77,11.2),(54,11.2)]
    for f in perimeter(b,poly):
        n=max(3,round(f.length/3.1));p=f.length/n
        for i in range(n):f.cell(i*p,(i+1)*p,53.6,59.4,p*.56,2.35,center=56.3,joints=True)
        f.cornice(59.6);f.box(f.length/2,60.5,f.length,1.5,.50,0,.06)
        for i in range(int(f.length/1.6)):
            u=(i+.5)*1.6;f.box(u,59.15,.45,.48,.65,1,.35)
        f.railing(61.25)
        if f.n.x>.9:f.crest(f.length/2,61.15,2.8,2.8)
    # Sloping copper roof has real seams/ribs and terracotta hip flashing.
    b=Builder('06 Patinated copper pyramid, raised seams, lantern and flagpole');builders.append(b)
    cx,cy=65.5,.2;lo=(23.0,22.0);up=(3.8,3.6);z0,z1=61.2,73.2
    b.frustum((cx,cy),z0,z1,lo,up,6)
    for axis in [0,1]:
        width=lo[axis];upper=up[axis];fixed=lo[1-axis]/2;topfix=up[1-axis]/2
        for sign in [-1,1]:
            for i in range(int(width/.45)+1):
                t=-.5+i/int(width/.45)
                a=[cx,cy,z0];q=[cx,cy,z1];a[axis]+=t*width;q[axis]+=t*upper;a[1-axis]+=sign*fixed;q[1-axis]+=sign*topfix
                b.rod(a,q,.035,6,6)
    for a,c in zip([(cx-11.5,cy-11),(cx+11.5,cy-11),(cx+11.5,cy+11),(cx-11.5,cy+11)],[(cx-1.9,cy-1.8),(cx+1.9,cy-1.8),(cx+1.9,cy+1.8),(cx-1.9,cy+1.8)]):b.rod((*a,z0),(*c,z1),.13,7,8)
    b.box((cx,cy,73.45),(4.2,4,.50),7)
    b.box((cx,cy,75.15),(3.6,3.4,3.1),3)
    for x in [cx-1.65,cx+1.65]:
        for y in [cy-1.55,cy+1.55]:b.box((x,y,75.1),(.38,.38,3.2),7)
    for z in [73.8,76.5,76.9]:b.box((cx,cy,z),(4.0,3.8,.26),7)
    for f in perimeter(b,[(cx-1.8,cy-1.7),(cx+1.8,cy-1.7),(cx+1.8,cy+1.7),(cx-1.8,cy+1.7)]):f.railing(77.05)
    flag(b,(cx,cy,77),6)
    # Roof equipment is hidden behind modest screened enclosures, not placed atop the copper roof.
    b=Builder('07 Screened rear roof plant');builders.append(b)
    for x,y in [(-45,-23),(-10,-24),(30,-10)]:
        b.box((x,y,48),(5,4,2.4),8)
        for f in perimeter(b,[(x-3,y-2.5),(x+3,y-2.5),(x+3,y+2.5),(x-3,y+2.5)]):
            f.box(f.length/2,48.3,f.length,2.9,.20,0)
            for z in [47.3,47.7,48.1,48.5,48.9]:f.box(f.length/2,z,f.length-.4,.10,.13,4,.04)
    return builders,d,{'architectural_height_m':77,'spire_height_m':83,'description':'Sassoon House: three arched riverfront openings, nine narrow windows in three groups, recessed bronze glazing, setbacks, central balcony, copper pyramid and terracotta lantern; mapped courtyard holes remain open.','limits':['Window proportions and sculpted motifs interpreted from photographs, not measured surveys.','Rear and courtyard elevations reconstructed conservatively; modern plant enclosures are schematic.']}

def chinese_roof(b,c,width,depth,z):
    # Low Chinese roof with curved sweep and visibly raised eave corners.
    cx,cy=c;nx=20;ny=32
    verts=[]
    for i in range(nx+1):
        x=-depth/2+depth*i/nx
        for j in range(ny+1):
            y=-width/2+width*j/ny
            a=abs(x)/(depth/2);q=abs(y)/(width/2)
            zz=z+1.45*(1-a)**1.5+.70*q**7+.45*a**7*q**5
            verts.append((cx+x,cy+y,zz))
    faces=[]
    for i in range(nx):
        for j in range(ny):
            k=i*(ny+1)+j;faces.append((k,k+1,k+ny+2,k+ny+1))
    b.geom(verts,faces,6)
    for sign in [-1,1]:
        for j in range(ny):
            a=verts[(0 if sign<0 else nx)*(ny+1)+j];c=verts[(0 if sign<0 else nx)*(ny+1)+j+1];b.rod(a,c,.12,6,8)
    # Actual raised tile ridges, no flat pattern texture.
    for j in range(0,ny+1,2):
        for i in range(nx):b.rod(verts[i*(ny+1)+j],verts[(i+1)*(ny+1)+j],.045,6,6)

def bank():
    d=DATA['bund23'];builders=[]
    # Model axes are rotated after construction to match the mapped east tower.
    b=Builder('01 Granite podium, deep bank entrance and carved pilasters');builders.append(b)
    poly=[(-10,-14),(10,-14),(10,14),(-10,14)]
    front=Facade(b,(10,-14),(10,14),(1,0,0))
    # Three recessed entry portals, two monumental piers, side door openings.
    for a,c in [(0,3),(3,9),(19,25),(25,28)]:
        if c-a>4:front.cell(a,c,0,10.4,1.5,3.0,window_m=3,center=7,joints=True)
        else:front.panel(a,c,0,10.4,0,joints=True)
    for a,c in [(9,12),(12,16),(16,19)]:
        front.panel(a,c,8.3,10.4,0,joints=True)
        front.box((a+c)/2,4.6,c-a-.25,7.0,.09,3,-1.1)
        front.window((a+c)/2,5.0,c-a-.4,6.3,frame=4,glass=3,deep=1.05)
        for k in range(max(1,int((c-a-.4)/.23))):
            u=a+.2+k*.23;b.rod(front.p(u,1,-.60),front.p(u,3.6,-.60),.028,4,6)
        for zz in [1.0,1.4,2.5,3.6]:front.box((a+c)/2,zz,c-a-.2,.065,.09,4,-.55)
        for k in range(3):
            u=a+.45+(c-a-.9)*k/2
            for i in range(16):
                t=math.tau*i/16;v=math.tau*(i+1)/16
                b.rod(front.p(u+.2*math.cos(t),2.95+.28*math.sin(t),-.51),front.p(u+.2*math.cos(v),2.95+.28*math.sin(v),-.51),.025,4,6)
    for u in [11.75,16.25]:
        front.box(u,4.5,.55,8.8,1.2,1,.6)
        for k in range(9):front.crest(u,1.1+k*.8,.25,.48)
        front.box(u,.4,.85,.5,1.4,1,.7);front.box(u,8.8,.85,.5,1.4,1,.7)
    for u in [4.9,23.1]:
        front.window(u,7,1.5,3.0,glass=3,deep=.5)
        for k in range(7):
            front.box(u+(-.35 if k%2 else .35),5.8+k*.36,.16,.44,.18,1,.13)
            front.box(u,5.8+k*.36,1.2,.12,.18,1,.13)
    front.cornice(10.5)
    # Entry step treads descend to exact ground zero.
    for i in range(6):b.box((10.4+i*.27,0,.72-i*.11),(.32,11.2,.22),1)
    # Two seated entrance guardians, geometrically interpreted from the CC0 photo.
    # These are sculptural approximations, not scans of the original carving.
    for sign in [-1,1]:
        y=sign*9.0;b.box((12.5,y,.53),(1.7,1.5,.7),1);b.box((12.5,y,.93),(1.85,1.62,.17),1)
        b.ellipsoid((12.35,y,1.50),(.53,.43,.58),1)
        b.ellipsoid((12.68,y,1.95),(.42,.34,.63),1)
        b.ellipsoid((12.94,y,2.60),(.39,.40,.42),1)
        b.ellipsoid((13.24,y,2.48),(.25,.27,.18),1)
        for side in [-1,1]:
            b.ellipsoid((12.95,y+side*.25,1.55),(.17,.16,.53),1)
            b.ellipsoid((13.10,y+side*.25,1.10),(.28,.19,.14),1)
            b.ellipsoid((12.91,y+side*.32,2.94),(.14,.15,.20),1)
            b.ellipsoid((13.25,y+side*.19,2.68),(.045,.048,.05),3,n=12,rings=6)
        for k in range(12):
            a=math.tau*k/12;b.ellipsoid((12.76,y+.39*math.cos(a),2.55+.39*math.sin(a)),(.18,.15,.15),1,n=12,rings=6)
        b.ellipsoid((13.40,y,2.47),(.028,.20,.042),3,n=12,rings=6)
        b.ellipsoid((13.31,y+.27,1.17),(.23,.23,.23),1)
    for f in perimeter(b,poly):
        if f.n.x>.9:continue
        n=max(2,round(f.length/4));p=f.length/n
        for i in range(n):f.cell(i*p,(i+1)*p,0,10.4,p*.48,4.5,center=5.0,joints=True)
    b=Builder('02 Tower ashlar, staggered shoulders and fifteen-storey opening pattern');builders.append(b)
    # Front composition: three bronze vertical strips, two flanking window rows,
    # ornamental pierced grilles and two shoulder rows; these are not uniform bays.
    front=Facade(b,(10,-14),(10,14),(1,0,0))
    rows=12;lo=10.8;pitch=4.10
    cols=[(0,4,2.0,'side'),(4,6.7,.75,'grille'),(6.7,10,1.55,'plain'),(10,12.7,1.7,'strip'),(12.7,15.3,1.7,'strip'),(15.3,18,1.7,'strip'),(18,21.3,1.55,'plain'),(21.3,24,.75,'grille'),(24,28,2.0,'side')]
    for row in range(rows):
        z0=lo+row*pitch;z1=z0+pitch
        for a,c,w,typ in cols:
            # Side shoulders stop below central tower, exactly visible in reference.
            if typ=='side' and row>=10:continue
            if typ=='grille':
                u=(a+c)/2;front.cell(a,c,z0,z1,.8,1.9,window_m=3,joints=True)
                # Perforated Chinese geometric grille: frame plus alternating teeth.
                for sign in [-1,1]:front.box(u+sign*.34,(z0+z1)/2,.13,1.8,.22,1,.04)
                for k in range(4):
                    zz=(z0+z1)/2-.7+k*.46;front.box(u+(-.13 if k%2 else .13),zz,.48,.13,.22,1,.04)
            else:
                front.cell(a,c,z0,z1,w,2.85,joints=True,spandrel=12 if typ=='strip' else None)
                if typ=='strip':
                    for u in [(a+c)/2-w*.32,(a+c)/2,(a+c)/2+w*.32]:front.box(u,z0+.53,.055,.85,.10,4,.08)
    # Two upper floors are set back at both ends; opaque massing never covers windows.
    front.panel(0,28,10.4,10.8,0,joints=True)
    upper=[(-10,-10),(10,-10),(10,10),(-10,10)]
    for f in perimeter(b,poly):
        if f.n.x>.9:continue
        n=max(2,round(f.length/3.5));p=f.length/n
        for j in range(10):
            for i in range(n):f.cell(i*p,(i+1)*p,10.8+j*pitch,10.8+(j+1)*pitch,min(1.65,p*.57),2.85,joints=True,spandrel=12 if i%3==1 else None)
        f.cornice(51.7)
    # Shoulder roof and high centre mass, with side-wall returns.
    for y in [-12,12]:b.box((0,y,51.8),(20,4,.40),0)
    for f in perimeter(b,upper):
        if f.n.x>.9:continue
        n=max(2,round(f.length/3.5));p=f.length/n
        for j in range(2):
            for i in range(n):f.cell(i*p,(i+1)*p,51.8+j*pitch,51.8+(j+1)*pitch,min(1.65,p*.57),2.85,joints=True)
    # Final two-storey penthouse holds the real bank-name band and small windows.
    top=[(-8,-8.8),(10,-8.8),(10,8.8),(-8,8.8)]
    b=Builder('03 Upper setback, bank-name band and Chinese swept-eave crown');builders.append(b)
    for f in perimeter(b,top):
        n=5 if f.n.x>.9 else max(3,round(f.length/3.4));p=f.length/n
        for j in range(2):
            for i in range(n):f.cell(i*p,(i+1)*p,60+j*4.2,64.2+j*4.2,p*.52,2.1,joints=True)
        f.panel(0,f.length,68.4,70.9,0,joints=True);f.cornice(71.0)
        for i in range(max(1,int(f.length/.70))):f.box((i+.5)*.70,70.85,.32,.5,.5,1,.34)
        # Linked raised rings under the traditional eaves.
        for i in range(max(1,int(f.length/1.1))):
            u=(i+.5)*1.1
            for k in range(12):
                a=math.tau*k/12;c=math.tau*(k+1)/12
                b.rod(f.p(u+.38*math.cos(a),69.4+.13*math.sin(a),.07),f.p(u+.38*math.cos(c),69.4+.13*math.sin(c),.07),.045,1,6)
    chinese_roof(b,(1,0),19.8,20.2,71.35)
    b.box((0,0,60.1),(20,20,.25),8)
    flag(b,(-1,9.3,61.2),5)
    logo=Facade(b,(10,-8.8),(10,8.8),(1,0,0));lu=3.1;lz=64.2
    for i in range(32):
        a=math.tau*i/32;c=math.tau*(i+1)/32
        b.rod(logo.p(lu+.62*math.cos(a),lz+.62*math.sin(a),.16),logo.p(lu+.62*math.cos(c),lz+.62*math.sin(c),.16),.095,10,8)
    logo.box(lu,lz,.14,1.25,.16,10,.22)
    for zz in [lz-.26,lz+.26]:logo.box(lu,zz,.60,.14,.16,10,.22)
    for u in [lu-.30,lu+.30]:logo.box(u,lz,.14,.52,.16,10,.22)
    # The documented four-storey west building is a distinct mapped footprint.
    # Its current OSM nine-floor tag conflicts with architectural descriptions;
    # this lower rear reconstruction is explicitly flagged as lower confidence.
    wing=d.get('western_wing')
    if wing:
        a=-math.radians(d['tower_rotation_degrees'])
        def to_model(p):return (p[0]*math.cos(a)-p[1]*math.sin(a),p[0]*math.sin(a)+p[1]*math.cos(a))
        wp=[to_model(p) for p in wing['exterior']]
        b=Builder('04 Documented four-storey western wing — inferred elevation');builders.append(b)
        for f in perimeter(b,wp):
            if f.length<1.5:f.panel(0,f.length,0,20,0);continue
            n=max(1,round(f.length/3.9));p=f.length/n
            for j in range(4):
                for i in range(n):f.cell(i*p,(i+1)*p,j*4.8,(j+1)*4.8,min(1.9,p*.56),2.9,joints=True)
            f.cornice(19.4);f.box(f.length/2,20.0,f.length,.9,.45,0,.05)
        roof(b,[[to_model(p) for p in t] for t in wing['roof_triangles']],19.5)
    # Name and logo are constructed from curves converted into solid meshes.
    return builders,d,{'architectural_height_m':73.5,'description':'Bank of China east tower: carved podium, three recessed entrances, central bronze spandrels, alternating pierced grilles, two-stage setbacks, small upper windows and swept Chinese eaves.','limits':['Height 73.5m is an architectural-reference approximation pending surveyed datum.','Carved reliefs and unobserved rear elevations are simplified geometric interpretations.']}

def south():
    d=DATA['bund19'];builders=[]
    b=Builder('01 Rusticated ground-floor stone and deep arched entrances');builders.append(b)
    walls(b,d['exterior'],0,5.1,1,style='south',ground=True)
    b=Builder('02 Red brick pilasters, pale infill and recessed timber windows');builders.append(b)
    for f in perimeter(b,d['exterior']):
        if f.length<1.2:
            f.panel(0,f.length,5.1,29.0,7);continue
        n=2 if f.n.x>.95 and f.length>9 else max(1,round(f.length/4.2));p=f.length/n
        for j in range(5):
            z0=5.1+j*4.5;z1=z0+4.5
            for i in range(n):
                u=(i+.5)*p;w=min(2.0,p*.58)
                f.cell(i*p,(i+1)*p,z0,z1,w,2.7,m=9,joints=False)
                # Terra-cotta surround projects beyond the cream infill, not a painted stripe.
                for sign in [-1,1]:f.box(u+sign*(w/2+.12),(z0+z1)/2,.23,3.1,.22,7,.19)
                f.box(u,z1-.7,w+.6,.28,.30,7,.24)
                if j in [0,3]:
                    if i%2:f.pediment(u,z1-.51,w+.75,.72,7)
                    else:
                        for k in range(20):
                            a=math.pi*k/20;c=math.pi*(k+1)/20
                            b.rod(f.p(u+(w/2+.25)*math.cos(a),z1-.45+.65*math.sin(a),.27),f.p(u+(w/2+.25)*math.cos(c),z1-.45+.65*math.sin(c),.27),.10,7,8)
                for sign in [-1,1]:f.box(u+sign*(p/2-.18),(z0+z1)/2,.36,4.5,.28,7,.22)
            for dz,h,dep in [(0,.13,.14),(.2,.18,.25)]:f.box(f.length/2,z0+dz,f.length,h,.5,7,dep)
            # Thin brick courses, only across infill spandrel strips.
            for z in [z0+.43,z0+.63,z0+.83]:f.box(f.length/2,z,f.length,.008,.006,11,.01)
        f.cornice(28.15,m=7);f.box(f.length/2,28.8,f.length,1.1,.50,7,.15)
        for i in range(int(f.length/.45)):f.box((i+.5)*.45,27.95,.2,.32,.45,7,.4)
        f.railing(29.4)
    roof(b,d['roof_triangles'],28.6)
    # Distinctive octagonal rooftop turret at the northeast corner, as in both photos.
    b=Builder('03 Octagonal corner lanterns and copper caps');builders.append(b)
    corners=[(41.0,17.0,3.2),(-33.7,1.2,2.9)]
    for x,y,r in corners:
        poly=[(x+r*math.cos(math.tau*i/8+math.pi/8),y+r*math.sin(math.tau*i/8+math.pi/8)) for i in range(8)]
        for f in perimeter(b,poly):
            f.cell(0,f.length,29,33.4,f.length*.48,2.25,m=9)
            f.cornice(33.4)
            for sign in [0,1]:f.box(sign*f.length,31.2,.28,4.4,.40,7,.2)
        verts=[]
        for rad,z in [(r+.38,33.9),(r*.75,35.05),(r*.3,35.55)]:verts.extend([(x+rad*math.cos(math.tau*i/8+math.pi/8),y+rad*math.sin(math.tau*i/8+math.pi/8),z) for i in range(8)])
        faces=[tuple(range(16,24))]+[(row*8+i,row*8+(i+1)%8,(row+1)*8+(i+1)%8,(row+1)*8+i) for row in range(2) for i in range(8)]
        b.geom(verts,faces,6);b.rod((x,y,35.5),(x,y,38),.035,4,10)
    # Stepped central gable above the long Nanjing Road elevation.
    b=Builder('04 Main pediment, roof terrace and screened equipment');builders.append(b)
    long=max(perimeter(b,d['exterior']),key=lambda f:f.length if f.n.y>0 else 0)
    u=long.length*.45
    long.box(u,30.5,8.5,3.8,.8,7,.18);long.pediment(u,32.2,9.5,2.8,7)
    long.window(u,30.4,2.4,2.6,stone=7);long.crest(u,33.1,1.3,1.2)
    riverfront=max(perimeter(b,d['exterior']),key=lambda f:f.length if f.n.x>.95 else 0)
    center=riverfront.length/2
    riverfront.pediment(center,5.35,4.0,1.4,1)
    for sign in [-1,1]:
        riverfront.box(center+sign*1.6,2.6,.36,4.8,.75,1,.4)
        riverfront.box(center+sign*1.6,4.8,.66,.38,.8,1,.45)
    for x,y in [(-18,-4),(12,5)]:b.box((x,y,29.5),(4,3,1.5),8)
    # Riverfront roof pavilion: paired round windows, central pediment and
    # a smaller cupola distinct from the octagonal corner turret.
    b=Builder('05 Riverfront mansard pavilion, oculi and small lantern');builders.append(b)
    pavilion=[(36.5,-1),(43,-1),(43,9),(36.5,9)]
    for f in perimeter(b,pavilion):
        if f.n.x>.9:
            f.oculus(1.8,31.5,.72,0,3.6,29.6,33.3)
            f.cell(3.6,6.4,29.6,33.3,1.5,2.1,m=7)
            f.oculus(8.2,31.5,.72,6.4,10,29.6,33.3)
            f.pediment(5,33.0,3.4,1.1,1)
        else:
            f.panel(0,f.length,29.6,33.3,9);f.cornice(33.3)
    b.frustum((39.75,4),33.25,34.2,(7.8,11.1),(5.0,8.2),6)
    cupola=[(38.8,3.05),(40.7,3.05),(40.7,4.95),(38.8,4.95)]
    for f in perimeter(b,cupola):
        f.cell(0,f.length,34.2,36.6,.85,1.6,m=9);f.cornice(36.65)
    b.frustum((39.75,4),36.85,37.35,(2.5,2.5),(.7,.7),6)
    b.rod((39.75,4,37.25),(39.75,4,38.1),.055,6,10)
    return builders,d,{'architectural_height_m':35.6,'spire_height_m':38,'description':'Palace Hotel south building: cream infill, red brick pilasters, alternated curved and triangular window pediments, ground arches, projecting cornices and octagonal copper-capped corner lanterns.','limits':['Six-storey main block is based on photographs and published 30m description; turret heights are inferred.','Small sculptural ornament is interpreted geometrically; side/rear details are lower confidence.']}

def text_label(text,name,loc,size,rotation,material):
    cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.align_x='CENTER';cu.size=size;cu.extrude=.022;cu.bevel_depth=.006;cu.bevel_resolution=1
    font=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc')
    if font.exists():
        try:cu.font=bpy.data.fonts.load(str(font))
        except Exception:pass
    obj=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=rotation;cu.materials.append(material)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.convert(target='MESH');obj.select_set(False);return obj

def setup_render(scene,objects,slug,out,detail=False):
    coords=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)]);center=(lo+hi)/2
    if slug=='peace_north':target=Vector((15,0,38));location=Vector((220,-230,135));lens=50
    elif slug=='bank_china':target=Vector((0,0,35));location=Vector((118,-92,62));lens=58
    else:target=Vector((6,0,16));location=Vector((128,123,74));lens=55
    if detail:
        if slug=='peace_north':target=Vector((77,0,17));location=Vector((126,-35,24));lens=62
        elif slug=='bank_china':target=Vector((11,-1,17));location=Vector((68,-35,25));lens=62
        else:target=Vector((42,12,15));location=Vector((95,71,30));lens=62
    bpy.ops.object.camera_add(location=location);cam=bpy.context.object;cam.name='Architectural comparison camera';cam.rotation_euler=(target-location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_end=2000;scene.camera=cam
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.12;scene.render.resolution_x=1600;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out/('detail.png' if detail else 'overview.png'))
    scene.view_settings.view_transform='AgX';scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.66,.76,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    if not any(o.type=='LIGHT' for o in scene.objects):
        light=bpy.data.lights.new('Soft afternoon sun','SUN');light.energy=2.4;light.angle=.10;obj=bpy.data.objects.new('Soft afternoon sun',light);scene.collection.objects.link(obj);obj.rotation_euler=(.62,-.55,-.4)
        # The studio ground is deliberately excluded from the exported model.
        bpy.ops.mesh.primitive_plane_add(size=800,location=(0,0,-.035));ground=bpy.context.object;ground.name='Preview ground — not exported';mat=bpy.data.materials.new('Preview warm neutral');mat.diffuse_color=(.38,.40,.40,1);ground.data.materials.append(mat)

def main(slug,render=True):
    reset();mats=make_materials()
    if slug=='peace_north':
        for i,color in [(0,(.45,.335,.205)),(1,(.59,.47,.30)),(2,(.30,.235,.16)),(5,(.085,.145,.155))]:
            mats[i].diffuse_color=(*color,1);mats[i].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
    elif slug=='bank_china':
        for i,color in [(0,(.61,.565,.46)),(1,(.70,.65,.54)),(2,(.40,.37,.31))]:
            mats[i].diffuse_color=(*color,1);mats[i].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
    elif slug=='peace_south':
        for i,color in [(0,(.46,.435,.38)),(4,(.12,.10,.08))]:
            mats[i].diffuse_color=(*color,1);mats[i].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
    builders,d,meta={'peace_north':north,'bank_china':bank,'peace_south':south}[slug]()
    objects=[b.finish(mats) for b in builders]
    if slug=='peace_north':
        face=next(f for f in perimeter(Builder('position'),d['exterior']) if f.n.x>.95 and f.length>15)
        p=face.p(face.length/2,7.40,.12)
        objects.append(text_label('和平饭店','Raised gold Peace Hotel name',p,.55,(math.pi/2,0,math.atan2(face.u.y,face.u.x)),mats[13]))
    if slug=='bank_china':
        # Main inscription on upper tower; text plane points toward +east.
        objects.append(text_label('中国银行','Raised upper Bank of China inscription',(10.12,0,63.65),1.25,(math.pi/2,0,math.pi/2),mats[4]))
        # Rotate to true north, matching the OSM tower footprint orientation.
        a=math.radians(d['tower_rotation_degrees'])
        for obj in objects:
            if obj.type=='MESH':
                # Text retains its local object transform before common rotation.
                from mathutils import Matrix
                obj.matrix_world=Matrix.Rotation(a,4,'Z')@obj.matrix_world
    out=HERE/slug;out.mkdir(exist_ok=True)
    bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    for o in objects:o['reference_reconstruction']='Photographic architectural reconstruction; not survey measured'
    bpy.ops.export_scene.gltf(filepath=str(out/(slug+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True)
    triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects if o.type=='MESH')
    coords=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    meta.update({'id':slug,'name':d['source']['name_zh'],'units':'metres','coordinate_system':'glTF X east, Y up, Z south','origin_longitude':d['source']['origin_longitude'],'origin_latitude':d['source']['origin_latitude'],'geographic_bbox':d['source']['geographic_bbox'],'replacement':d['source']['replacement'],'geometry_source':d['source']['osm']['url'],'geometry_license':'ODbL-1.0; © OpenStreetMap contributors','triangles':triangles,'meshes':len(objects),'glb_bytes':(out/(slug+'.glb')).stat().st_size,'bounds_enu':{'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]},'source_files':['../build_art_deco.py','../architecture.py','../footprints.json']})
    if slug=='bank_china' and d.get('western_wing'):
        west=d['source']['related_geometries']['western_wing']
        meta['replacement']['building_ids'].append(west['overture_id'])
        meta['western_wing']={'included':True,'source':west['source_url'],'modeled_storeys':4,'model_roof_m':20.45,'confidence':'lower than the photographed east tower','floor_conflict':west['floor_conflict']}
        coords_geo=d['source']['geometry']['coordinates'][0]+west['geometry']['coordinates'][0]
        meta['geographic_bbox']=[min(p[0] for p in coords_geo),min(p[1] for p in coords_geo),max(p[0] for p in coords_geo),max(p[1] for p in coords_geo)]
    meta['landmark_source_id']=d['source']['id'];meta['reference_metadata']='../references.json'
    meta['previews']={'overview':'overview.png','riverfront':'front.png','entrance_detail':'detail.png'}
    assert triangles<300000,(slug,triangles)
    assert meta['glb_bytes']<100_000_000
    (out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    scene=bpy.context.scene;setup_render(scene,objects,slug,out)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(slug+'.blend')),compress=True)
    if render:
        bpy.ops.render.render(write_still=True)
        setup_render(scene,objects,slug,out,detail=True);bpy.ops.render.render(write_still=True)
    print('ART_DECO_COMPLETE',slug,triangles,meta['glb_bytes'])

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['peace_north']
    main(args[0],render='--no-render' not in args)
