"""The photographed cast piers, two-plane arch and street ironwork of Lane 212."""
from pathlib import Path
import json
import sys
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"hongkou-general-post-office/source/common"))
from sign_lettering import lettering_shapes

SOURCE=Path(__file__).resolve().parent
MEASURE=SOURCE.parent/'measurements'
def reading(name):
    return json.loads((MEASURE/name).read_bytes())
ANCHORS=reading('212-window-cameras.json')['gate_controls']['globes_metres']
ARCH=reading('arch-curves.json')
FABRIC=reading('pier-reliefs-and-address.json')
balls=np.array(ANCHORS);origin=balls.mean(axis=0);origin[2]=0.
U=np.r_[balls[1,:2]-balls[0,:2],0.];U/=np.linalg.norm(U)
V=np.array([-U[1],U[0],0.]);Z=np.array([0.,0.,1.])
HALF=np.linalg.norm(balls[1,:2]-balls[0,:2])/2
def at(u,v,z):return origin+u*U+v*V+z*Z

def finish(rgb,roughness,metallic=0.):
    x=np.array(rgb)/255.;linear=np.where(x<.04045,x/12.92,((x+.055)/1.055)**2.4)
    return dict(color=linear.tolist(),roughness=roughness,metallic=metallic)
CREAM='212 pier | warm painted render';BLUE='212 pier | grey blue painted moulding';STONE='212 pier | worn carved stone';BASE='212 pier | basalt grey foot';DEEP='212 pier | worn relief recess';PALE='212 pier | relief highlights'
IRON='212 gate | charcoal iron';EDGE='212 gate | weathered iron edge';GREEN='212 pier | green enamel';IVORY='212 pier | ivory numbers';SIGN='212 pier | off-white civic plaque';INK='212 pier | faded red lettering'
RED='212 lantern | deep red pleated silk';RIB='212 lantern | faded gold thread';GOLD='212 lantern | golden tassels'
PALETTE={CREAM:finish((187,180,159),.89),BLUE:finish((119,128,125),.80),STONE:finish((143,144,134),.85),BASE:finish((96,103,100),.91),
 DEEP:finish((106,106,95),.93),PALE:finish((153,150,136),.86),IRON:finish((47,45,41),.59,.56),EDGE:finish((60,57,52),.54,.50),
 GREEN:finish((38,70,61),.48,.16),IVORY:finish((202,207,185),.55),SIGN:finish((186,177,159),.76),INK:finish((124,86,80),.77),
 RED:finish((145,48,41),.76),RIB:finish((170,103,55),.65),GOLD:finish((185,146,55),.79)}
def block(b,ua,ub,va,vb,za,zb,mat,label):
    b.box(at((ua+ub)/2,(va+vb)/2,(za+zb)/2),[ub-ua,vb-va,zb-za],mat,[U,V,Z],label)
def section(b,polygon,depth,thickness,face,material,label):
    if face=='front': b.prism(polygon,-depth,-depth+thickness,lambda s,z,d:at(s,-d,z),material,label)
    elif face=='east': b.prism(polygon,depth,depth+thickness,lambda s,z,d:at(d,s,z),material,label)
    else: b.prism(polygon,-depth,-depth+thickness,lambda s,z,d:at(-d,-s,z),material,label)
def polygons(data,lod):
    for c in data:
        p=Polygon(c['outline'],c['holes'])
        clean=p.simplify(.0021 if lod else .0007,preserve_topology=True)
        # Touching camera pixels can leave a zero-width meeting of two relief
        # contours. A sub-millimetre opening gives each extrusion a closed edge.
        clean=clean.buffer(-.00052,quad_segs=1).buffer(.00052,quad_segs=1)
        if not clean.is_empty:yield clean
def tap(b,u,v,levels,mat,label):
    """Four-sided moulding with a real sloping arris and level end faces."""
    vertices=[];faces=[(0,3,2,1)]
    for z,hw,hd in levels:
        vertices.extend(at(u+sx*hw,v+sy*hd,z)for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)])
    for j in range(0,len(vertices)-4,4):
        faces.extend((j+k,j+(k+1)%4,j+(k+1)%4+4,j+k+4)for k in range(4))
    h=len(vertices)-4;faces.append(tuple(range(h,h+4)));b.add(vertices,faces,mat,label)
def carving(b,u,role,face,lod):
    # Side relief supplies the silhouette. The repeated cast occurs on both
    # original piers; the inner side on the east is only partially visible.
    for key,base,t,mat in [('silhouette_vz',0.,.015,DEEP),('raised_vz',.014,.012,STONE),('highest_vz',.025,.007,PALE)]:
        for j,p in enumerate(polygons(FABRIC['capital'][key],lod)):
            if face=='front':
                p=affinity.translate(p,xoff=u-.040)
                section(b,p,-.316-base,t,face,mat,f'{role} capital street foliate {key} {j+1}')
            elif face=='east':
                section(b,p,u+.320+base,t,face,mat,f'{role} capital return foliate {key} {j+1}')
            else:
                p=affinity.translate(affinity.scale(p,xfact=-1.,yfact=1.,origin=(0,0)),xoff=.08)
                section(b,p,u-.320-base,t,face,mat,f'{role} capital inner foliate {key} {j+1}')
def pier(b,u,role,lod):
    west=role=='West'; foot=.37 if west else .25; plinth=.935 if west else .825
    block(b,u-.313,u+.313,-.294,.398,foot-.03,plinth,BASE,role+' dark masonry plinth')
    block(b,u-.313,u+.313,-.294,.398,plinth-.003,2.601,CREAM,role+' warm rendered square shaft')
    # Moulded blue-grey surrounds and their inboard return enclose an exposed
    # strip of the original shaft, including the slightly darker upper reveal.
    outside=box(u-.220,.938,u+.214,2.411)
    for idx,(outer,inner,d,mat) in enumerate([(outside,outside.buffer(-.026,join_style=2),.018,BLUE),(outside.buffer(-.025,join_style=2),outside.buffer(-.053,join_style=2),.032,BLUE),(outside.buffer(-.052,join_style=2),outside.buffer(-.068,join_style=2),.022,STONE)]):
        section(b,outer.difference(inner),-.294,d,'front',mat,f'{role} raised shaft frame step {idx+1}')
    if west:
        notice=Polygon([(u-.110,1.794),(u+.118,1.803),(u+.112,1.940),(u-.117,1.936)])
        section(b,notice,-.294,.0025,'front',SIGN,'West upper shaft pale paper notice')
    tap(b,u,.051,[(2.535,.323,.354),(2.558,.345,.371),(2.588,.349,.381),(2.605,.327,.363)],BLUE,role+' lower frieze shelf')
    block(b,u-.320,u+.320,-.316,.412,2.599,2.939,CREAM,role+' square frieze field')
    carving(b,u,role,'front',lod);carving(b,u,role,'east' if west else 'west',lod)
    tap(b,u,.049,[(2.918,.322,.366),(2.951,.338,.378),(2.970,.373,.406),(2.996,.375,.408),(3.021,.403,.433),(3.054,.402,.433)],STONE,role+' stepped top cornice')
    dz=ANCHORS[0 if west else 1][2]-3.50
    b.lathe(at(u,0,0)[:2],[(z+dz,r) for z,r in [(3.041,.152),(3.074,.172),(3.110,.179),(3.138,.148),(3.170,.12),(3.204,.104),(3.232,.079),(3.252,.083),(3.275,.113),(3.301,.096),(3.310,.070),(3.345,.067)]],STONE,14 if lod else 28,role+' turned globe pedestal')
    r=.163
    orb=[(3.50+dz+r*np.sin(a),max(.0002,r*np.cos(a)))for a in np.linspace(-np.pi/2,np.pi/2,11 if lod else 23)]
    b.lathe(at(u,0,0)[:2],orb,STONE,18 if lod else 34,role+' grey round finial')

def plates(b,lod):
    face=-HALF+.313;plate=FABRIC['plaque'];civic=FABRIC['civic_plaque']
    for role,data,mat in [('Lane address',plate,GREEN),('Civic',civic,SIGN)]:
        section(b,Polygon(data['face_vz']),face,.009,'east',mat,role+' enamel face')
    for i,p in enumerate(polygons(plate['glyph_shapes'],lod)):
        x,z=p.centroid.coords[0]
        if z<2.43 or .03<x<.095 or x>.248:continue
        section(b,p,face+.0085,.0022,'east',IVORY,f'Address traced numeral or dash {i+1}')
    font=SOURCE/'fonts/NanchangLaneCharacters.otf'
    # Top-row large numbers preserve their actual source silhouettes. The five
    # small ideographs have a documented type substitute inside measured bounds.
    chars=[('弄',.062,2.479,.070,.081),('号',.278,2.491,.039,.044),
           ('南',-.061,2.393,.049,.044),('昌',.071,2.400,.047,.044),('路',.202,2.407,.047,.044)]
    for ch,x,z,width,h in chars:
        for _,p in lettering_shapes(ch,width,h,font=font):
            p=affinity.translate(p,xoff=x,yoff=z).simplify(.0012 if lod else .0005,preserve_topology=True)
            section(b,p,face+.0085,.0022,'east',IVORY,'Address lettering '+ch)
    for i,p in enumerate(polygons(civic['paint'],lod)):
        section(b,p,face+.0085,.002,'east',INK,f'Civic plaque traced red paint {i+1}')

def curve(key,u):
    record=ARCH[key];t=u/record['halfspan_m'];a,b,c,d=record['height_polynomial']
    return a+b*t+c*t*t+d*t**4
def bezier(points,n):
    p=np.array(points);t=np.linspace(0.,1.,n)[:,None]
    return (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]
def ironbar(b,path,r,lod,label,material=IRON):
    b.tube(path,r,material,6 if lod else 10,label)
def flat_arc(b,key,depth,lod,label):
    span=ARCH[key]['halfspan_m']; samples=np.linspace(-span,span,27 if lod else 69)
    hw=.016 if key=='outer' else .019
    p=Polygon([(x,curve(key,x)-hw)for x in samples]+[(x,curve(key,x)+hw)for x in samples[::-1]])
    section(b,p,depth+.018,.036,'front',IRON,label)
def curl(b,cx,cz,rx,rz,hand,depth,lod,label,angle=.14,mat=IRON):
    # A flat strip rolled inward, leaving the centre of every scroll open.
    t=np.linspace(0.,1.,10 if lod else 26);phi=angle+hand*t*5.58;r=1.-.83*t
    ironbar(b,[at(cx+rj*rx*np.cos(a),depth,cz+rj*rz*np.sin(a))for rj,a in zip(r,phi)],.0068,lod,label,mat)
def arch(b,lod):
    for face,depth in [('Street',-.304),('Lane',.394)]:
        for key in ['outer','inner']:flat_arc(b,key,depth,lod,face+' arched iron '+key+' member')
        for sign in [-1,1]:
            for name,x in [('outer',sign*ARCH['outer']['halfspan_m']),('inner',sign*ARCH['inner']['halfspan_m'])]:
                bottom=3.04;top=curve(name,x)
                block(b,x-.017,x+.017,depth-.020,depth+.020,bottom,top,IRON,face+f' {sign:+d} {name} square upstand')
            low=sign*1.64;high=sign*2.26
            block(b,min(low,high),max(low,high),depth-.017,depth+.017,3.045,3.076,IRON,face+f' {sign:+d} bearing strap')
            # The side infill wraps around the ball and shares its bearing strap.
            curl(b,sign*2.125,3.311,.104,.181,sign,depth,lod,face+f' {sign:+d} lower side roll')
            curl(b,sign*2.11,3.544,.086,.112,-sign,depth,lod,face+f' {sign:+d} upper side roll')
        # Paired S scrolls span the band between the continuous load-bearing
        # straps. The source shows large open turns with tight inward curls
        # and small punched flower ends, especially on the sunlit west half.
        for j,cx in enumerate([-1.57,-1.14,-.70,-.26,.18,.62,1.06,1.50]):
            width=.425
            for hand in [-1,1]:
                def pos(p):
                    x=cx+hand*width*p[0]
                    bottom=curve('inner',x);h=curve('outer',x)-bottom
                    return at(x,depth,bottom+p[1]*h)
                # Lower turn rolls upward and inward. The second stem rises
                # to the outer strap and turns back on itself just below it.
                scrolls=[
                    [[(-.02,.005),(.32,.025),(.52,.195),(.44,.355)],
                     [(.44,.355),(.39,.480),(.14,.475),(.14,.342)],
                     [(.14,.342),(.14,.263),(.27,.278),(.26,.340)]],
                    [[(-.02,.005),(-.065,.245),(.017,.621),(.252,.822)],
                     [(.252,.822),(.372,.923),(.207,1.003),(.055,.990)]],
                    [[(.252,.822),(.105,.733),(-.005,.625),(.066,.571)],
                     [(.066,.571),(.174,.493),(.277,.636),(.153,.646)]]]
                for k,chain in enumerate(scrolls):
                    points=[]
                    for curve_points in chain:
                        segment=bezier(curve_points,6 if lod else 13)
                        points.extend(segment if not points else segment[1:])
                    ironbar(b,[pos(q)for q in points],.0042 if k==2 else .0050,lod,f'{face} bay {j+1} {hand:+d} scroll {k+1}')
                if (j+(hand>0))%2==0:
                    end=pos((.26,.340)); relative=end-origin
                    x=float(relative@U);z=float(end[2]);rad=.021
                    flower=[(x+(rad if k%2==0 else rad*.43)*np.cos(k*np.pi/5),z+(rad if k%2==0 else rad*.43)*np.sin(k*np.pi/5))for k in range(10)]
                    section(b,Polygon(flower),depth+.003,.009,'front',EDGE,f'{face} openwork flower {j+1} {hand:+d}')
    for sign in [-1,1]:
        for key in ['outer','inner']:
            x=sign*ARCH[key]['halfspan_m'];h=curve(key,x)
            for kind,z in [('base',3.061),('spring',h)]:ironbar(b,[at(x,-.304,z),at(x,.394,z)],.016,lod,f'{key} {sign:+d} {kind} cross tie')
    # Three visible small ties carry the narrow depth of the upper frame.
    for i,x in enumerate([-1.12,.02,1.13]):
        z=curve('outer',x);ironbar(b,[at(x,-.304,z),at(x,.394,z)],.011,lod,f'Overhead cross tie {i+1}')
    for i,(x,dep) in enumerate([(-.149,-.304),(.042,.394)]):
        h=curve('outer',x)
        # Two large lower C scrolls support a smaller pair forming a heart
        # immediately beneath the floral finial in the 2015 original.
        for hand in [-1,1]:
            for k,chain in enumerate([
                [[(-.003,0.),(.137,.006),(.143,.186),(.063,.192)],[(.063,.192),(-.003,.195),(.002,.101),(.046,.127)]],
                [[(0.,0.),(-.015,.105),(.145,.217),(.080,.279)],[(.080,.279),(.005,.354),(-.013,.228),(.045,.252)]]]):
                pts=[]
                for seg in chain:
                    t=bezier(seg,7 if lod else 16);pts.extend(t if not pts else t[1:])
                ironbar(b,[at(x+hand*s,dep,h+z)for s,z in pts],.0056,lod,f'Crest {i+1} {hand:+d} curled tier {k+1}')
        ironbar(b,[at(x,dep,h+.18),at(x-.020,dep,h+.364)],.006,lod,f'Crest stem {i+1}')
        p=[(x-.020+(.033 if k%2==0 else .013)*np.cos(k*np.pi/6),h+.365+(.033 if k%2==0 else .013)*np.sin(k*np.pi/6)) for k in range(12)]
        section(b,Polygon(p),dep+.005,.011,'front',EDGE,f'Crest six-petal flower {i+1}')

PAVING='212 paving | warm grey aggregate';JOINT='212 paving | dark threshold edge'
PALETTE.update({PAVING:finish((127,123,116),.95),JOINT:finish((103,101,96),.94)})
def lanterns(b,lod):
    for n,row in enumerate(reading('lane212-iron-street-fabric.json')['lanterns']):
        x,depth,z0=row['local_uvz'];c=at(x,depth,0.)[:2]
        p=[(-.149,.048),(-.145,.088),(-.119,.143),(-.067,.188),(0.,.202),(.076,.184),(.119,.132),(.140,.063)]
        b.lathe(c,[(z0+z,r)for z,r in p],RED,20 if lod else 36,f'Lantern {n+1} pleated red shell')
        # A small bridge between the two arch faces supports each seasonal lamp.
        support=curve('inner',x)
        ironbar(b,[at(x,-.304,support),at(x,.394,support)],.009,lod,f'Lantern {n+1} transverse hanger')
        ironbar(b,[at(x,depth,z0+.139),at(x,depth,support)],.006,lod,f'Lantern {n+1} suspension')
        for j,a in enumerate(np.linspace(0.,2*np.pi,10 if lod else 16,endpoint=False)):
            pts=[at(x+(r+.001)*np.cos(a),depth+(r+.001)*np.sin(a),z0+z)for z,r in p]
            ironbar(b,pts,.0026,lod,f'Lantern {n+1} silk rib {j+1}',RIB)
        b.lathe(c,[(z0-.165,.044),(z0-.148,.081),(z0-.131,.074)],RIB,12 if lod else 22,f'Lantern {n+1} lower cap')
        b.lathe(c,[(z0-.29,.081),(z0-.274,.083),(z0-.183,.065),(z0-.163,.043)],GOLD,16 if lod else 28,f'Lantern {n+1} short tassel skirt')
        if n==1:
            low=z0-.74
            ironbar(b,[at(x,depth,low+.012),at(x,depth,z0-.275)],.003,lod,'East lantern long cord',RIB)
            center=z0-.432;sz=.052
            b.add([at(x,depth,center+sz),at(x+sz,depth,center),at(x,depth,center-sz),at(x-sz,depth,center),at(x,depth-.025,center),at(x,depth+.025,center)],[(0,4,1),(1,4,2),(2,4,3),(3,4,0),(0,1,5),(1,2,5),(2,3,5),(3,0,5)],IVORY,'East lantern hanging pale lozenge')
            b.lathe(c,[(low-.153,.038),(low-.130,.037),(low-.043,.021),(low+.014,.011)],GOLD,10 if lod else 20,'East lantern lower tassel')

def open_leaf(b,lod):
    # The complete western moving leaf can be traced in the 2015 courtyard-side
    # photograph. The eastern return is largely concealed by shop fittings.
    hinge_u=-1.620; hinge_d=.42651;span=1.61;ang=np.radians(83.20406)
    along=np.cos(ang)*U+np.sin(ang)*V; outward=np.cross(along,Z)
    def pt(s,z,t=0.):return at(hinge_u,hinge_d,0)+s*along+z*Z+t*outward
    def polyline(coords,r,label,offset=0.,mat=IRON):
        ironbar(b,[pt(s,z,offset)for s,z in coords],r,lod,'West leaf '+label,mat)
    def rail(s,z,w,h,dep,name):
        b.box(pt(s,z),[w,dep,h],IRON,[along,-outward,Z],'West leaf '+name)
    def top(s):
        ratio=np.clip(s/span,0.,1.);return 2.54092+.63665*ratio*ratio*(3.-2.*ratio)
    base=.59
    for name,s in [('hinge stile',0.),('meeting stile',span)]:
        h=top(s);rail(s,(base+h)/2,.037,h-base,.048,name)
    for j,dz in enumerate([0.,.09]):rail(span/2,base+dz,span,.042 if j==0 else .022,.039,f'base rail {j+1}')
    for j,dz in enumerate([0.,-.268]):
        polyline([(s,top(s)+dz)for s in np.linspace(0,span,15 if lod else 35)],.023 if j==0 else .015,'curved head '+str(j+1))
    for i,s in enumerate([.135,.298,.470,.653,.827,1.003,1.174,1.352,1.49]):
        low=base+.075;high=top(s)-.006
        rail(s,(low+high)/2,.016,high-low,.020,f'upright {i+1}')
    for i,s in enumerate([.165,.476,.777,1.060,1.375]):
        cz=top(s)-.125;t=np.linspace(0.,1.,11 if lod else 23);a=(1 if i%2==0 else -1)*t*5.5+.12
        r=1.-.76*t;polyline([(s+rr*.108*np.cos(aa),cz+rr*.087*np.sin(aa))for aa,rr in zip(a,r)],.007,'head rolled strap '+str(i+1))
    # Two pairs of crossing, gently arched lower straps occur beneath the
    # vertical bars and can be read against the pale return wall.
    for i,p in enumerate([[(0,1.98),(.54,1.77),(1.26,.96),(1.49,base+.02)],[(0,1.84),(.55,1.65),(1.34,.81),(1.60,base+.02)],
                          [(.09,base+.02),(.25,1.29),(.92,2.24),(1.60,2.58)],[(.28,base+.02),(.43,1.32),(1.11,2.23),(1.60,2.44)]]):
        polyline(bezier(p,10 if lod else 22),.010,'fan sweep '+str(i+1),.009 if i<2 else -.009)
    for j,s in enumerate([.13,.40,.70,.95,1.22,1.49]):
        hi=top(s);polyline([(s,hi-.01),(s,hi+.059)],.006,'spear stem '+str(j+1))
        verts=[pt(s,hi+.032),pt(s-.017,hi+.059),pt(s,hi+.116),pt(s+.017,hi+.059),pt(s,hi+.060,.009),pt(s,hi+.060,-.009)]
        b.add(verts,[(4,1,0),(4,2,1),(4,3,2),(4,0,3),(5,0,1),(5,1,2),(5,2,3),(5,3,0)],IRON,f'West leaf spearhead {j+1}')
    for n,z in enumerate([.86,2.27]):
        ironbar(b,[pt(0,z),at(-HALF+.312,.34,z)],.017,lod,f'West post hinge link {n+1}',EDGE)
        b.lathe(pt(0,z)[:2],[(z-.065,.026),(z+.066,.026)],EDGE,8 if lod else 14,f'West post hinge barrel {n+1}')

def pavement(b):
    # Road level is the ground datum of the two upstairs-window cameras. The
    # raised threshold and sloping footway are visible in the December views.
    corners=[(-2.50,-.96),(2.50,-.96),(2.50,.80),(-2.50,.80)]
    h=[.275,.185,.284,.371];vertices=[at(x,y,.06)for x,y in corners]+[at(x,y,z)for (x,y),z in zip(corners,h)]
    b.add(vertices,[(0,3,2,1),(4,5,6),(4,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],PAVING,'Lane 212 gently graded threshold paving')
    for i,(x,zt) in enumerate([(-HALF,.368),(HALF,.268)]):
        block(b,x-.315,x+.315,-.300,.399,.08,zt+.015,BASE,f'Pier {i+1} embedded plinth foot')

def add_gate(b,lod=False):
    b.palette.update(PALETTE)
    pavement(b);pier(b,-HALF,'West',lod);pier(b,HALF,'East',lod)
    plates(b,lod);arch(b,lod);lanterns(b,lod);open_leaf(b,lod)
