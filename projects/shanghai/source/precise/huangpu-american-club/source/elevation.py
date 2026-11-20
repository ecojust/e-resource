"""Seven-bay elevation, based on the municipal head-on view and photos of both corners."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

STONE = 'carved pale stone'
CREAM = 'warm white marble'
GRAY = 'granite base'
JOINT = 'weathered mortar'
IRON = 'painted wrought iron'
GLASS = 'recessed blue-grey glass'
STILE = 'painted steel sash'
DOOR = 'stained entrance timbers'
BROWN = 'dark chocolate pressed brick'
OCHRE = 'warm chocolate pressed brick'
DARK = 'purple brown pressed brick'
PALETTE = {
    STONE:{'color':[.79,.758,.671],'roughness':.78}, CREAM:{'color':[.865,.822,.726],'roughness':.71},
    GRAY:{'color':[.49,.473,.433],'roughness':.84},JOINT:{'color':[.434,.36,.296],'roughness':.92},
    BROWN:{'color':[.294,.181,.151],'roughness':.83},OCHRE:{'color':[.36,.219,.172],'roughness':.82},
    DARK:{'color':[.245,.168,.159],'roughness':.87}, IRON:{'color':[.096,.109,.103],'metallic':.54,'roughness':.47},
    STILE:{'color':[.12,.134,.134],'metallic':.37,'roughness':.50},GLASS:{'color':[.168,.245,.274],'metallic':.23,'roughness':.31},
    DOOR:{'color':[.157,.093,.071],'roughness':.64},'roof covering':{'color':[.27,.253,.216],'roughness':.9}}
WIDTH = 23.14
RETURN = 3.48
CROWN = 25.60
TIER = [(6.14,2.98,1.85),(10.99,2.11,1.38),(14.49,2.08,1.38),(17.88,2.04,1.38)]
SEG = WIDTH / 7


def pierced_openings(positions, entrance, lod):
    result = []
    for u in positions:
        is_door = entrance and abs(u)<.02
        result.append((u,'door' if is_door else 'low', opening(u,.12 if is_door else 2.0,2.53 if is_door else 1.43,4.84 if is_door else 2.57,1.265 if is_door else 0,14 if lod else 28)))
        for n,(z,h,w) in enumerate(TIER):
            result.append((u,'balcony' if n==0 else 'office',opening(u,z,w,h)))
        result.append((u,'arcade',opening(u,21.77,1.70,2.61,.85,14 if lod else 28)))
    return result


def tile_face(f, actual_surface, lod):
    """Keep uninterrupted staggered bonds visible around real openings, including the arched ones."""
    half = f.length/2
    h,w = (.39,1.03) if lod else (.178,.47)
    row=0
    z=.40
    # Each brick is a separate original coloured face. Mortar is the continuous
    # recessed solid behind them, and jambs belong to that same watertight wall.
    colors=[BROWN,BROWN,DARK,OCHRE,BROWN,DARK,BROWN]
    all_verts={mat:[]for mat in (BROWN,DARK,OCHRE)}
    all_faces={mat:[]for mat in all_verts}
    prepared=actual_surface
    import shapely
    shapely.prepare(prepared)
    while z<21.24:
        u=-half-(w*.5 if row%2 else 0);col=0
        while u<half:
            x0,x1=max(-half,u+.008),min(half,u+w-.008); z0,z1=z+.006,min(21.24,z+h-.006)
            if x1-x0>.012 and z1-z0>.012:
                piece=box(x0,z0,x1,z1)
                colr=colors[(row*13+col*7+col*row*3+col)%len(colors)]
                lifts=.012+((row+2*col)%3)*.0007
                if prepared.covers(piece):
                    verts=all_verts[colr];ids=len(verts)
                    verts.extend(f.point(x,y,lifts)for x,y in ((x0,z0),(x1,z0),(x1,z1),(x0,z1)))
                    all_faces[colr].append((ids,ids+1,ids+2,ids+3))
                elif prepared.intersects(piece):
                    clipped=actual_surface.intersection(piece)
                    if clipped.area>.0009:f.prism(clipped,-.002,lifts,colr,'facing brick at opening')
            u+=w;col+=1
        z+=h;row+=1
    for material,verts in all_verts.items():
        if verts:f.builder.add(verts,all_faces[material],material,f.label+'/staggered dark facing bricks')


def voussoirs(f,u,z,w,lod):
    """Five light stone heads with the shell-like raised central key seen in the district close-up."""
    h=.25
    for i in (-2,-1,0,1,2):
        a=(i-.5)*w/5;b=(i+.5)*w/5
        poly=Polygon([(u+a+.007,z),(u+b-.007,z),(u+b*1.22-.008,z+h),(u+a*1.22+.008,z+h)])
        f.prism(poly,.011,.10,STONE,'radiating lintels')
    key=Polygon([(u-.12,z-.065),(u+.12,z-.065),(u+.196,z+.392),(u-.196,z+.392)])
    f.prism(key,.08,.16,CREAM,'raised centre keystone')
    if not lod:
        for s in (-1,0,1):
            f.line((u+.041*s,z-.005,.17),(u+.077*s,z+.33,.17),.014,STONE,5,'carved keystone flutes')


def fit_openings(f, rows, lod):
    for u,kind,hole in rows:
        x0,z0,x1,z1=hole.bounds;w=x1-x0
        if kind=='door':
            rim=hole.buffer(.22,join_style=2).difference(hole)
            f.prism(rim,-.01,.16,STONE,'round stone entrance arch')
            # The fanlight and paired leaves sit at separate depths in the genuine recess.
            spring=z1-w/2
            trans=hole.intersection(box(x0,spring-.02,x1,z1+.01))
            f.prism(trans,-.35,-.315,GLASS,'arched fanlight')
            f.prism(hole.intersection(box(x0,z0,x1,spring)),-.39,-.35,DOOR,'recessed paired timber doors')
            f.box(u,(spring+z0)/2,.084,spring-z0,.17,-.27,DOOR,'door centre stile')
            for off in (-.612,.612):
                f.box(u+off,2.15,.91,1.54,.085,-.30,GLASS,'paired entrance vision panels')
            f.box(u,spring,w,.115,.17,-.25,IRON,'transom bar')
            for angle in range(20,180,20 if not lod else 40):
                a=math.radians(angle)
                f.line((u,spring,-.24),(u+(w/2-.05)*math.cos(a),spring+(w/2-.05)*math.sin(a),-.24),.017,IRON,5,'fanlight radii')
            continue
        f.window(hole,2 if lod else 4,3 if lod else 4,frame=STILE,glass=GLASS,trim=False)
        if kind=='arcade':
            outline=hole.buffer(.15,join_style=2).difference(hole)
            f.prism(outline,-.004,.115,CREAM,'white arched window surround')
            f.box(u,z0-.08,w+.32,.2,.40,.036,STONE,'arcade sill')
            # Rectangular dark spandrels between the pale arch and its square panel.
            head=box(u-1.18,z1-.91,u+1.18,z1+.15).difference(hole.buffer(.144))
            f.prism(head,-.002,.017,BROWN,'arched dark spandrels')
        else:
            voussoirs(f,u,z1+.015,w,lod)
            if kind=='balcony':
                spring=z1+.082
                full=opening(u,spring-.01,w+.48,1.03,1.02,12 if lod else 24)
                ring=full.buffer(.074).difference(full).intersection(box(u-w,spring+.01,u+w,spring+1.21))
                f.prism(ring,-.003,.065,BROWN,'blind semicircular brick arches')
                f.box(u,spring+1.06,.235,.23,.14,.049,STONE,'blind arch top key')
            if kind=='low' or not lod:
                for s in (-1,1):
                    f.box(u+s*w*.39,z0-.22,.14,.24,.25,.025,STONE,'sill corbels')


def rail(b,f,z,front,lod):
    width=f.length-.19
    for h in (z,z+.79):
        f.line((-width/2,h,front),(width/2,h,front),.033,IRON,7,'continuous iron rails')
    for u in np.linspace(-width/2,width/2,max(4,int(width/(.38 if lod else .20)))):
        f.line((u,z,front),(u,z+.79,front),.017,IRON,5,'slender iron balusters')
    if not lod:
        for u in np.arange(-width/2+.25,width/2-.12,.47):
            pts=[f.point(u+.115*math.cos(a),z+.46+.24*math.sin(a),front+.008)for a in np.linspace(0,math.tau,13)]
            b.tube(pts,.012,IRON,5,f.label+'/oval ironwork')


CORNICE_COURSES = ((.24,.48,.11,GRAY),(5.81,.18,.54,STONE),(5.95,.15,.68,CREAM),
                   (9.34,.085,.072,STONE),(21.23,.13,.16,CREAM),(24.54,.14,.16,STONE),
                   (24.74,.17,.29,STONE),(25.02,.22,.44,CREAM),(25.33,.20,.68,STONE),(25.53,.14,.78,CREAM))


def cornices(f,lod):
    for u in np.arange(-f.length/2+.16,f.length/2,.56 if lod else .35):
        f.box(u,25.13,.15,.21,.47,.28,STONE,'projecting modillions')
        f.box(u,5.82,.12,.16,.35,.28,STONE,'balcony dentils')


def elevation(f,positions,is_front,lod):
    rows=pierced_openings(positions,is_front,lod)
    surface=f.wall(0,21.31,[s for _,k,s in rows if k!='arcade'],thickness=.42,material=JOINT)
    tile_face(f,surface,lod)
    f.wall(21.23,25.40,[s for _,k,s in rows if k=='arcade'],thickness=.42,material=STONE)
    fit_openings(f,rows,lod)
    gaps=(np.arange(-3.5,4)*SEG) if is_front else (-f.length/2,f.length/2)
    for x in gaps:
        for s in (-1,1):
            u=x+s*.125
            if abs(u)>f.length/2-.055:continue
            f.box(u,23.00,.161,3.0,.18,.072,CREAM,'paired attic pilasters')
            f.box(u,21.52,.23,.14,.235,.09,STONE,'pilaster bases')
            f.box(u,24.49,.265,.15,.24,.095,STONE,'pilaster capitals')
    cornices(f,lod)


def add_geometry(b,lod):
    half=WIDTH/2
    main=Facade(b,(-half,0),(half,0),'Street front')
    east=Facade(b,(-half,RETURN),(-half,0),'East return')
    west=Facade(b,(half,0),(half,RETURN),'West return')
    elevation(main,np.arange(-3,4)*SEG,True,lod)
    for flank in (east,west):
        elevation(flank,[0.0],False,lod)
    # The three facades share each full cornice course. Their union removes
    # coincident caps and inside seams where perpendicular projecting bands meet.
    for z,h,projection,stone in CORNICE_COURSES:
        outer=projection+.04
        front=box(-half-outer,-outer,half+outer,.44)
        left=box(-half-outer,-outer,-half+.44,RETURN+.05)
        right=box(half-.44,-outer,half+outer,RETURN+.05)
        continuous=unary_union([front,left,right])
        b.plan_prism(continuous,z-h/2,z+h/2,stone,'Cornice/continuous mitred courses')
    # The roof closes against the inner edge of that continuous eaves course.
    b.plan_prism(box(-half+.44,.44,half-.44,RETURN+.05),CROWN-.18,CROWN-.012,
                 'roof covering','Short roof return/roof covering')
    for x in np.arange(-1.5,1.6)*SEG:
        profile=[(.07,.325),(.21,.325),(.24,.29),(.31,.27),(.37,.248),(.52,.228),(5.25,.205),(5.31,.235),(5.38,.25),(5.45,.29),(5.51,.29)]
        b.lathe((x,-.99),profile,CREAM,16 if lod else 32,'Portico/Tuscan shaft and capitals')
        b.box((x,-.99,.095),(.72,.72,.19),GRAY,label='Entrance portico/square bases')
        b.box((x,-.99,5.53),(.62,.62,.14),STONE,label='Entrance portico/abaci')
    for z,h,depth in ((5.69,.27,1.46),(5.86,.12,1.62),(5.99,.14,1.73)):
        main.box(0,z,3.13*SEG,h,depth,.58,STONE,'portico entablature')
    for u in np.arange(-5.02,5.1,.35 if not lod else .56):
        main.box(u,5.87,.12,.15,.20,1.36,CREAM,'portico dentils')
    # Photo shows a continuous wrought-iron balustrade stepped out over the four columns.
    rail(b,Facade(b,(-half,0),(-1.55*SEG,0),'Eastern balcony'),6.06,.42,lod)
    rail(b,Facade(b,(1.55*SEG,0),(half,0),'Western balcony'),6.06,.42,lod)
    rail(b,Facade(b,(-1.55*SEG,0),(1.55*SEG,0),'Portico balcony'),6.06,1.30,lod)
    for x in (-1.55*SEG,1.55*SEG):
        b.tube([(x,-.42,6.85),(x,-1.30,6.85)],.033,IRON,6,'Portico balcony/side top rails')
    for x in (-1,1):
        main.box(x*SEG,.99,1.48,.68,.13,.057,STONE,'inset stone plaques below portico windows')
