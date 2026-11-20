"""Hazelwood garden elevation, western loggia and complete mapped roof."""
import json
from pathlib import Path
import sys
import numpy as np
from shapely.geometry import box

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "tools"))
from package_architectural_model import build
from photo_architecture import Facade, opening

P = json.loads((HERE / "parameters.json").read_text())
IDENT = "changning-xingguo-guesthouse-01"
META = {
    "id": IDENT, "name": "兴国宾馆1号楼（太古洋行花园住宅）",
    "status": "photo-informed-exterior",
    "scope": "Garden-front exterior of Hazelwood, its west loggia return and mapped roof mass. Rear and east wall treatment is estimated.",
    "model_scope_zh": "兴国路72号花园住宅的园侧七开间、二层柱廊、宽台阶、西侧拱廊、五处阁楼窗、两座烟囱与独栋屋面，北面、东面和遮挡段以体量表达。",
    "source_register": "source/precise/" + IDENT + "/reference-review.json",
    "viewer_page": "xingguo-guesthouse-01.html", "audit_directory": "data/audit/xingguo-guesthouse-01-v1/",
    "coordinate_convention": "GLB X along garden front towards east, Y up, Z towards lawn. Origin at middle of source south edge.",
    "map_reference_license": "OpenStreetMap / Overture Maps, ODbL-1.0.",
    "interiors_modeled": False,
}
PALETTE = {
    "limestone":{"color":[.72,.666,.556],"roughness":.91},
    "carved pale stone":{"color":[.80,.748,.635],"roughness":.81},
    "garden paving":{"color":[.44,.371,.290],"roughness":.91},
    "plinth stone":{"color":[.53,.459,.367],"roughness":.84},
    "patinated copper":{"color":[.214,.345,.283],"roughness":.72,"metallic":.24},
    "roof seams":{"color":[.168,.274,.228],"roughness":.68,"metallic":.25},
    "recessed glass":{"color":[.087,.097,.094],"roughness":.3,"metallic":.33},
    "bronze window frame":{"color":[.122,.111,.101],"roughness":.54,"metallic":.31},
}
CENTER_AXES = [-6.56,-3.28,0,3.28,6.56]
WIDTH = P["facade_width_m"]
LEFT, RIGHT = -WIDTH/2, WIDTH/2
REAR = P["rear_wall_y_m"]


def facade(b, left, right, y, label):
    return Facade(b,(left,y),(right,y),label)


def roof(b,x0,x1,y0,y1,base,top,label,lod):
    """Hipped closed roof with seams following the actual four sloping planes."""
    w=x1-x0;d=y1-y0;inset=min(w,d)*.43
    if w>=d:
        ends=np.array([[x0+inset,(y0+y1)/2,top],[x1-inset,(y0+y1)/2,top]])
    else:
        ends=np.array([[(x0+x1)/2,y0+inset,top],[(x0+x1)/2,y1-inset,top]])
    corners=np.array([[x0,y0,base],[x1,y0,base],[x1,y1,base],[x0,y1,base]])
    # Endpoint assignment at each eave corner, ordered counterclockwise from garden-west.
    nearest=[0,1,1,0] if w>=d else [0,0,1,1]
    faces=[(3,2,1,0)]
    for j in range(4):
        k=(j+1)%4;a=nearest[j];c=nearest[k]
        faces.append((j,k,4+c,4+a) if a!=c else (j,k,4+a))
        b.tube([corners[j],ends[a]],.048,"roof seams",5 if lod else 8,label+"/hip rolls")
        if not lod:
            n=max(2,round(np.linalg.norm(corners[k]-corners[j])/.70))
            for i in range(1,n):
                t=i/n;start=corners[j]*(1-t)+corners[k]*t;finish=ends[a]*(1-t)+ends[c]*t
                b.tube([start+[0,0,.018],finish+[0,0,.018]],.018,"roof seams",5,label+"/standing seams")
    b.add([*corners,*ends],faces,"patinated copper",label+"/roof slopes")
    b.tube(ends,.065,"roof seams",6 if lod else 9,label+"/ridge cap")


def wainscot(f):
    for z,h,dep,mat in [(1.03,.18,.22,"plinth stone"),(5.99,.25,.34,"carved pale stone"),(6.20,.14,.40,"carved pale stone")]:
        f.beam(z,h,dep,material=mat,label="floor courses")


def cornice(f):
    for z,h,dep in [(11.29,.16,.21),(11.51,.31,.28),(11.78,.15,.43),(11.94,.12,.49)]:
        f.beam(z,h,dep,label="built-up eaves cornice")


def lower(f,xs):
    holes=[opening(x,1.06,1.82 if len(xs)>1 else 2.36,4.53) for x in xs]
    f.wall(.74,5.99,holes,thickness=.48)
    for x,h in zip(xs,holes):
        f.window(h,columns=3,rows=3,trim=False,label="garden tall sash")
        f.box(x,4.29,h.bounds[2]-h.bounds[0]-.04,.10,.15,-.08,"bronze window frame","high transom")
        f.box(x,5.74,h.bounds[2]-h.bounds[0]+.47,.13,.36,.03,label="window lintels")
    wainscot(f)


def shaft(b,x,y,lod,label):
    profile=[(6.24,.205),(6.33,.224),(6.39,.24),(6.46,.196),(6.56,.172),
             (8.80,.161),(10.91,.145),(11.02,.173),(11.11,.203),(11.18,.225)]
    b.lathe((x,y),profile,"carved pale stone",10 if lod else 20,label+"/stone columns")
    for z,w,h in [(6.23,.51,.17),(11.22,.48,.15)]:
        b.box((x,y,z),(w,w,h),"carved pale stone",label=label+"/square base and capital")


def balustrade(b,x0,x1,y,z,lod,label):
    for height,hh,dep in [(z+.07,.14,.25),(z+.75,.115,.26),(z+.84,.09,.32)]:
        b.box(((x0+x1)/2,y,height),(x1-x0,dep,hh),"carved pale stone",label=label+"/rails")
    count=max(3,round((x1-x0)/(.54 if lod else .34)))
    for j in range(count):
        x=x0+(j+.5)*(x1-x0)/count
        b.lathe((x,y),[(z+.13,.090),(z+.23,.080),(z+.32,.058),(z+.46,.102),(z+.56,.088),(z+.66,.058),(z+.71,.086)],
                "carved pale stone",6 if lod else 10,label+"/turned balusters")


def loggia(b,lod,x0,x1,front,back,xs,group):
    f=facade(b,x0,x1,front,group)
    wall=facade(b,x0,x1,back,group+" recessed wall")
    apertures=[opening(x-(x0+x1)/2,6.39,1.50 if len(xs)>1 else 1.79,3.74) for x in xs]
    wall.wall(6.19,11.62,apertures)
    for h in apertures:wall.window(h,2,3,trim=True,label="recessed loggia sash")
    for z,t,mat in [(6.13,.23,"plinth stone"),(11.36,.25,"limestone")]:
        b.box(((x0+x1)/2,(front+back)/2,z),(x1-x0,back-front,t),mat,label=group+"/floor and soffit")
    cornice(f)
    if len(xs)>1:
        support=[x0+.29,x1-.29]
        for a,c in zip(xs,xs[1:]):
            axis=(a+c)/2
            support.extend([axis-.25,axis+.25])
        spans=[(x-.5*(xs[1]-xs[0])+.24,x+.5*(xs[1]-xs[0])-.24) for x in xs]
    else:
        support=[x0+1.21,x1-1.21]
        spans=[(x0+.36,x1-.36)]
    for x in support:shaft(b,x,front+.17,lod,group)
    for a,c in spans:balustrade(b,a,c,front+.20,6.23,lod,group)
    if len(xs)==1:
        for x in [x0+.32,x1-.32]:
            b.box((x,front+.31,6.13),(.65,.69,10.22),"limestone",label=group+"/corner antae")
            for z,w,h in [(1.21,.80,.21),(5.89,.85,.16),(11.23,.85,.19)]:
                b.box((x,front+.31,z),(w,.79,h),"carved pale stone",label=group+"/anta base and cap")


def dormer(b,x,lod):
    front=5.23;back=10.00;w=1.94
    f=facade(b,x-w/2,x+w/2,front,"Garden dormers")
    h=opening(0,12.33,1.50,1.24)
    f.wall(11.88,13.81,[h],material="patinated copper")
    f.window(h,2,2,frame="bronze window frame",trim=False,label="attic sash")
    for sign in [-1,1]:
        xx=x+sign*w/2
        b.add([(xx,front,11.94),(xx,back,13.56),(xx,back,13.72),(xx,front,13.81)],[(0,1,2,3)] if sign==1 else [(3,2,1,0)],
              "patinated copper","Garden dormers/sloping cheeks")
    b.add([(x-w*.57,front-.14,13.82),(x+w*.57,front-.14,13.82),(x+w*.57,back,13.75),(x-w*.57,back,13.75)],
          [(0,1,2,3)],"patinated copper","Garden dormers/lean-to caps")
    f.beam(13.81,.12,.17,material="roof seams",label="dormer drip edge")


def assemble(b,lod):
    wing=8.53;garden=3.66;endfront=3.03;back=7.03
    # The original polygon contains the stone entrance apron. Its open stairs have a separate collision boundary.
    for i in range(6):
        start=.17+i*.38
        b.box((0,(start+3.92)/2,.074*(i+1)),(22.6,3.92-start,.148*(i+1)),"garden paving",label="Garden/stone approach steps")
    for sign in [-1,1]:
        mid=sign*(11.32+(WIDTH/2-11.32)/2);span=WIDTH/2-11.32
        b.box((mid,2.08,.50),(span,3.80,1.00),"plinth stone",label="Garden/terrace flanks")
        balustrade(b,mid-span/2+.2,mid+span/2-.2,.34,1.00,lod,"Garden/terrace ends")
    b.box((0,(3.01+REAR)/2,.45),(WIDTH,REAR-3.01,.90),"plinth stone",label="Villa/foundation")
    for x0,x1,y,xs,group in [(LEFT,-wing,endfront,[(LEFT-wing)/2],"West pavilion"),(-wing,wing,garden,CENTER_AXES,"Garden gallery"),(wing,RIGHT,endfront,[(RIGHT+wing)/2],"East pavilion")]:
        f=facade(b,x0,x1,y,group)
        lower(f,[x-(x0+x1)/2 for x in xs])
        loggia(b,lod,x0,x1,y,back,xs,group)
        if x0 in [LEFT,wing]:
            for xx in [x0,x1]:
                # Pavilions project toward the garden, exposing narrow masonry returns.
                b.box((xx+.14 if xx==x0 else xx-.14,(y+garden)/2,5.87),(.28,garden-y,10.60),"limestone",label=group+"/forward returns")
    for sign,name in [(-1,"West return"),(1,"East return")]:
        x=sign*WIDTH/2
        make=lambda y0,y1,label: Facade(b,(x,y1),(x,y0),label) if sign<0 else Facade(b,(x,y0),(x,y1),label)
        # Two vertically aligned, round-headed openings are legible on the west return in the 2007 view.
        short=make(endfront,back,name+" at loggia")
        if sign<0:
            h0=opening(0,1.16,2.05,4.20,.98,12 if lod else 24)
            h1=opening(0,6.80,2.11,3.65,1.05,12 if lod else 24)
            short.wall(.81,11.72,[h0,h1]);short.window(h0,2,3,trim=False,label="lower arched sash")
            for z in [6.78,7.21]:short.box(0,z,1.98,.11,.28,.02,label="open arcade rail")
            for k in range(8):short.box((k-3.5)*.236,6.98,.075,.39,.16,.02,label="open arcade balusters")
        else:short.wall(.81,11.72,[])
        rest=make(back,REAR,name+" sheltered elevation")
        rest.wall(.82,11.69,[])
        for f in [short,rest]:wainscot(f);cornice(f)
    rear=Facade(b,(RIGHT,REAR),(LEFT,REAR),"North elevation")
    rear.wall(.81,11.70,[]);wainscot(rear);cornice(rear)
    roof(b,LEFT-.25,RIGHT+.25,garden-.20,REAR+.21,11.95,14.72,"Copper main roof",lod)
    for x0,x1,name in [(LEFT,-wing,"West pavilion roof"),(wing,RIGHT,"East pavilion roof")]:
        roof(b,x0-.24,x1+.24,endfront-.25,10.25,11.96,13.53,name,lod)
    for x in [-6.53,-3.27,0,3.27,6.53]:dormer(b,x,lod)
    for x in [-7.70,7.70]:
        label="Paired chimney stacks"
        b.box((x,11.12,14.04),(1.56,1.03,4.91),"limestone",label=label+"/shafts")
        for z,w,d,h in [(16.22,1.62,1.12,.11),(16.42,1.72,1.16,.16),(16.57,1.83,1.24,.13)]:
            b.box((x,11.12,z),(w,d,h),"carved pale stone",label=label+"/oversailing caps")
        b.box((x,11.12,16.65),(1.37,.78,.06),"interior shadow",label=label+"/chimney top")


if __name__ == "__main__":
    from final_preview import finish
    build(HERE,META,PALETTE,assemble)
    finish()
