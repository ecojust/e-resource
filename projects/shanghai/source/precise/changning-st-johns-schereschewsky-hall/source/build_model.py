"""Reconstruct Schereschewsky Hall's southern teaching wing from street and court views."""
from pathlib import Path
import argparse
import json
import math
import sys
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').exists())
sys.path.insert(0, str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder, Facade
ID = 'changning-st-johns-schereschewsky-hall'
META = dict(id=ID, heritage_id='sh-historic-b2-060', name='圣约翰大学怀施堂（韬奋楼）南翼与钟楼', address='万航渡路1575号41号楼', viewer_page='st-johns-schereschewsky-hall.html', geometry_license='MIT', photos_embedded=False)
BRICK='blue-grey facing brick'; RED='warm red brick dressings'; STONE='weathered granite'; RAIL='painted red-brown timber'; DARK='dark iron and timber'; GLASS='smoke grey glazing'; TILE='grey butterfly tile'; WHITE='warm cream stucco'; DIAL='clock enamel'
PALETTE={role:dict(color=color,roughness=rough) for role,color,rough in [
    (BRICK,[.29,.288,.297],.86),(RED,[.52,.254,.177],.84),(STONE,[.46,.421,.355],.85),
    (RAIL,[.33,.126,.097],.68),(DARK,[.064,.06,.054],.56),(GLASS,[.16,.18,.185],.31),
    (TILE,[.20,.205,.206],.79),(WHITE,[.82,.78,.66],.87),(DIAL,[.875,.864,.817],.44)]}
WIDTH=40.533; DEPTH=12.5; COURT=20.75; TOWER=4.8515
COURT_EAVE=8.342; FLOOR=4.8207; LOW_EAVE=8.342; RIDGE=11.961
def curve(c,bottom,spring,peak,width,n,flat=.0):
    """Rounded opening between vertical reveals, optionally with a flat central crown."""
    rad=(width-flat)/2; rise=peak-spring; c0=c-flat/2;c1=c+flat/2
    left=[(c0+rad*math.cos(t),spring+rise*math.sin(t)) for t in np.linspace(math.pi,math.pi/2,n+1)]
    right=[(c1+rad*math.cos(t),spring+rise*math.sin(t)) for t in np.linspace(math.pi/2,0,n+1)]
    if not flat:right=right[1:]
    return Polygon([(c-width/2,bottom),*left,*right,(c+width/2,bottom)])
def hood(f,q,base,material,label,thickness=.16,front=.055):
    ring=q.buffer(thickness,join_style=2).difference(q)
    f.prism(ring.intersection(box(q.bounds[0]-1,base,q.bounds[2]+1,q.bounds[3]+1)),.004,front,material,label)
def projecting_bands(f,wall,heights,label='brick string course'):
    for h,w in heights:
        cut=wall.intersection(box(-50,h-w/2,50,h+w/2))
        if not cut.is_empty:f.prism(cut,.004,.025,RED,label)
def lattice(f,c,z,width,height,lod,label):
    border=.038
    pieces=[box(c-width/2,z,c+width/2,z+border),box(c-width/2,z+height-border,c+width/2,z+height)]
    for col in range(max(2, round(width/.29))+1):
        u=c-width/2+width*col/max(2,round(width/.29));pieces.append(box(u-border/2,z,u+border/2,z+height))
    for t in ([.50] if lod else [.43,.73]):
        pieces.append(box(c-width/2,z+height*t-.013,c+width/2,z+height*t+.013))
    f.prism(unary_union(pieces),-.108,-.048,RAIL,label)
def wing(b,side,street,lod):
    a,c=sorted([side*TOWER/2,side*(WIDTH if street else COURT)/2]);length=c-a
    y=0 if street else DEPTH
    f=Facade(b,(a,y),(c,y),'Street upper and lower loggias' if street else 'Courtyard south wall') if street else Facade(b,(c,y),(a,y),'Courtyard south wall')
    n=8 if lod else 15
    if street:
        # School's aerial resolves 10 upper apertures per side. Bays are enumerated from the tower out.
        weights=np.array([.84,1.36,.84,.84,1.36,.84,.91,.91,.91,.91])
        edges=np.r_[0,np.cumsum(weights)]/sum(weights)*length
        intervals=[(side*((edges[i]+edges[i+1])/2-length/2),edges[i+1]-edges[i]) for i in range(10)]
    else:
        intervals=[(-length/3,length/3),(0,length/3),(length/3,length/3)]
    # The occupied corridor is open at its outer piers and terminates at a real backing wall.
    holes=[]
    for i,(u,span) in enumerate(intervals):
        w=span-.30 if street else span-.35
        q=curve(u,.32,3.04,4.12,w,n,.14*w if street else 0.)
        holes.append(q);hood(f,q,3.04,RED,'ground arcade brick head',.165)
        if not(street and i==0):lattice(f,u,.35,w,.80,lod,'gallery ground railing')
        if street:
            p=curve(u,FLOOR,7.68,7.98,w,n,.30*w)
            hood(f,p,7.68,RED,'upper flat-shouldered brick head',.12)
            lattice(f,u,FLOOR+.02,w,.89,lod,'upper gallery timber balusters')
        else:
            p=box(u-.432,5.91,u+.432,7.36)
            f.window(p,2,2,DARK,False,GLASS,'courtyard recessed upper sash')
            arch=curve(u,7.33,7.41,7.60,1.32,n,.09)
            hood(f,arch,7.42,RED,'upper sash indented segmental head',.12)
        holes.append(p)
    wall=box(-length/2,0,length/2,LOW_EAVE).difference(unary_union(holes))
    f.prism(wall,-.29,0,BRICK,'pier and spandrel masonry')
    projecting_bands(f,wall,[(1.65,.09),(3.04,.08),(FLOOR-.06,.12),(5.91,.10),(7.12,.09),(8.22,.075)])
    f.box(0,FLOOR-.16,length,.10,.39,.03,STONE,'floor belt')
    if street:
        # Arcaded passage stays open. Its interior backing wall is pierced separately.
        r=Facade(b,(a,2.35),(c,2.35),'Street loggia inner face')
    else:r=Facade(b,(c,DEPTH-2.04),(a,DEPTH-2.04),'Court loggia inner face')
    win=[box(u-.36,.36,u+.36,2.83) for u,span in intervals]
    r.wall(0,LOW_EAVE,win,material=BRICK)
    for j,q in enumerate(win):
        r.prism(q,-.25,-.19,RAIL,'recessed corridor door')
    for h in [.14,FLOOR-.09]:
        b.box(((a+c)/2,(1.18 if street else DEPTH-1.03),h),(length,2.37 if street else 2.06,.16),STONE,label='loggia/slab')
def rotated_shape(coords,angle,x,z):
    co=math.cos(angle);si=math.sin(angle)
    return Polygon([(x+a*co-b*si,z+a*si+b*co) for a,b in coords])
def clock_face(f,lod):
    c=13.134;w=2.58;h=2.69
    plate=box(-w/2,c-h/2,w/2,c+h/2)
    f.prism(plate,.018,.077,DIAL,'square enamel dial')
    rim=plate.buffer(.063,join_style=2).difference(plate)
    f.prism(rim,.015,.125,DARK,'clock outer rim')
    # Court clock shows bold numerals only at the four cardinal hours. Other hours are batons.
    for hour in (1,2,4,5,7,8,10,11):
        a=math.tau*hour/12;r=.94
        p=rotated_shape([(-.065,-.19),(.065,-.19),(.065,.19),(-.065,.19)],-a,r*math.sin(a),c+r*math.cos(a))
        f.prism(p,.081,.107,DARK,'clock/hour index')
    glyphs=json.loads((HERE/'clock-numerals.json').read_bytes())
    for num,dx,dz in [('12',0,.98),('3',.96,0),('6',0,-.97),('9',-.96,0)]:
        for paths in glyphs[num]:
            rings=[[(dx+x,c+dz+z)for x,z in ring]for ring in paths]
            f.prism(Polygon(rings[0],rings[1:]),.083,.111,DARK,'clock/numeral '+num)
    # Retain the positions recorded on the court face, independent of the street exposure.
    hour,minute=(.05,4.02) if 'Court' in f.label else (10.1,7.1)
    for hr,reach,width,d in [(hour,.57,.080,.146),(minute,.98,.047,.177)]:
        a=math.tau*hr/12
        p=rotated_shape([(-width,-.14),(-width,.14),(-width*.52,reach*.73),(0,reach),(width*.52,reach*.73),(width,.14),(width,-.14)],-a,0,c)
        f.prism(p,d,d+.020,DARK,'clock/hand')
    from shapely.geometry import Point
    f.prism(Point(0,c).buffer(.098,quad_segs=8),.186,.223,DARK,'clock/axle')
def tower_face(b,court,lod):
    half=TOWER/2;y=DEPTH if court else 0
    f=Facade(b,(half,y),(-half,y),'Court clock') if court else Facade(b,(-half,y),(half,y),'Street clock')
    n=9 if lod else 18
    portal=curve(0,-.12,3.04,4.35,2.58,n)
    lights=[curve(u,5.85,7.76 if i==1 else 7.62,8.33 if i==1 else 8.08,w,n) for i,(u,w)in enumerate([(-1.10,.53),(0,.86),(1.10,.53)])]
    clerestory=[box(u-w/2,9.564,u+w/2,11.06)for u,w in [(-1.04,.53),(0,.72),(1.04,.53)]]
    wall=box(-half,0,half,14.98).difference(unary_union([portal,*lights,*clerestory]))
    f.prism(wall,-.36,0,BRICK,'tower perforated masonry')
    hood(f,portal,.04 if not court else 3.03,RED,'portal shaped brick surround',.205, .117)
    for q in lights:
        hood(f,q,7.62,RED,'arch over tower sash',.15)
        f.window(q,2 if q==lights[1] else 1,3,DARK,False,GLASS,'arched light')
    for q in clerestory:f.window(q,2 if q==clerestory[1] else 1,4,DARK,False,GLASS,'rectangular light')
    projecting_bands(f,wall,[(1.73,.10),(3.04,.08),(4.821,.15),(5.93,.096),(7.15,.096),(7.80,.08),(9.125,.12),(11.555,.14),(14.937,.15)])
    f.prism(box(-half+.04,14.982,half-.04,16.95),-.32,.002,WHITE,'cream upper belfry panel')
    for z in [11.555,14.937,16.94]:f.box(0,z,TOWER+.10,.105,.40,.016,RED,'cap moulding')
    for u in np.linspace(-1.53,1.53,6):f.box(u,16.66,.047,.225,.08,.045,DARK,'belfry vent')
    clock_face(f,lod)
    if not court:
        for z,w,h in [(5.36,3.30,.55),(15.44,2.61,.43)]:
            f.prism(box(-w/2,z-h/2,w/2,z+h/2),.009,.071,RED,'tablet frame')
            f.prism(box(-w/2+.064,z-h/2+.045,w/2-.064,z+h/2-.045),.074,.100,WHITE,'inscribed tablet field')
        lattice(f,0,3.17,2.55,1.28,lod,'iron transom grille')
def clock_roof(b):
    # The Chinese roof corners sweep above the eaves. Nested polygonal rings give the
    # top a concave profile; the hips join the ridge before the four corner tips rise.
    xc=0;yc=DEPTH/2;layers=[(3.06,DEPTH/2+.74,17.03,.61),(2.85,DEPTH/2+.51,17.12,.39),(1.88,DEPTH/2-.54,17.52,.18),(.63,DEPTH/2-2.03,17.95,.04)]
    pts=[]
    for hx,hy,z,lift in layers:
        pts.extend([(xc+x*hx,yc+y*hy,z+(lift if x and y else 0))for x,y in [(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]])
    faces=[tuple(range(7,-1,-1))]
    for j in range(len(layers)-1):
        for i in range(8):faces.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
    faces.append(tuple(range(24,32)));b.add(pts,faces,TILE,'belfry/swept hipped roof')
    for side in (-1,1):
        b.tube([(side*.60,yc-DEPTH/2+2.03,17.995),(side*.60,yc+DEPTH/2-2.03,17.995)],.061,TILE,8,'belfry/upper ridge')
def low_roof(b,side):
    a,c=sorted([side*TOWER/2,side*(WIDTH/2+1.06)])
    y0=-.73;y1=DEPTH+.73;ym=(y0+y1)/2
    # Eave ends project beyond the orthophoto ground footprint, and the ridge stops short of the gable hip.
    inner=side*TOWER/2;outer=side*(WIDTH/2+1.06);hip=outer-side*2.52;lip=LOW_EAVE+.06
    V=[(inner,y0,lip),(outer,y0,lip+.22),(outer,y1,lip+.22),(inner,y1,lip),(inner,ym,RIDGE),(hip,ym,RIDGE),
       (inner,y0,lip-.13),(outer,y0,lip+.09),(outer,y1,lip+.09),(inner,y1,lip-.13),(inner,ym,RIDGE-.13),(hip,ym,RIDGE-.13)]
    top=[(0,1,5,4),(1,2,5),(5,2,3,4)]
    faces=top+[tuple(i+6 for i in reversed(t))for t in top]
    for i,j in [(0,1),(1,2),(2,3),(3,4),(4,0)]:faces.append((j,i,i+6,j+6))
    if side<0:faces=[tuple(reversed(t))for t in faces]
    b.add(V,faces,TILE,'Teaching wing / hipped tile shell')
    b.tube([(inner,ym,RIDGE+.052),(hip,ym,RIDGE+.052)],.072,TILE,8,'Teaching wing / grey tile ridge')
def build(lod):
    b=Builder(PALETTE)
    for side in (-1,1):
        wing(b,side,True,lod);wing(b,side,False,lod);low_roof(b,side)
        sidewall=Facade(b,(side*TOWER/2,DEPTH if side<0 else 0),(side*TOWER/2,0 if side<0 else DEPTH),'Tower passage and cheek')
        sidewall.wall(.028,14.98,material=BRICK)
        sidewall.wall(14.98,16.99,material=WHITE)
        for z in [4.821,9.125,11.555,14.937]:sidewall.beam(z,.098,.008,RED)
        outer=side*WIDTH/2
        b.box((outer,DEPTH/2,LOW_EAVE/2),(.28,DEPTH,LOW_EAVE),BRICK,label='Teaching wing/end wall')
    tower_face(b,False,lod);tower_face(b,True,lod);clock_roof(b)
    b.box((0,DEPTH/2,.03),(TOWER-.65,DEPTH,.06),STONE,label='Clock passage/granite threshold and floor')
    b.box((0,DEPTH/2,4.69),(TOWER-.69,DEPTH-.61,.17),WHITE,label='Clock passage/soffit')
    return b
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    r=build(a.lod).save(a.output,META);print(a.output,r['sha256'])
