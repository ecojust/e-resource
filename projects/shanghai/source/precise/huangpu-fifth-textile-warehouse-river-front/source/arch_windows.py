"""Two rows of seven shallow-arched warehouse windows on South Suzhou Road."""
from math import cos, pi, sin, sqrt

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

LIME = 'Pale lime window surrounds'
WEATHERED = 'Warm grey cement window reveals'
CAST = 'Charcoal arch linings'
STEEL = 'Blue black upstairs window frames'
WOOD = 'Ochre timber lower windows'
SKY = 'Muted sky in warehouse glass'
SHADE = 'Cool shaded side window glass'
SASH = 'Steel flower basket wire'
LEAF = 'Deep green window plants'
GREEN = 'Yellow green hanging leaves'
ROSE = 'Crimson window flowers'
PETAL = 'Bright red petal tips'
PALETTE = {name: {'color': color, 'roughness': rough} for name,color,rough in (
    (LIME,[.81,.79,.70],.95),(WEATHERED,[.61,.60,.52],.93),
    (CAST,[.13,.14,.13],.80),(STEEL,[.15,.18,.19],.69),
    (WOOD,[.46,.32,.18],.74),(SKY,[.43,.53,.56],.38),(SHADE,[.22,.28,.29],.42),
    (SASH,[.39,.42,.36],.64),(LEAF,[.14,.26,.12],.93),(GREEN,[.30,.41,.17],.91),
    (ROSE,[.68,.055,.080],.88),(PETAL,[.88,.11,.09],.84))}

def _arch(x,width,sill,head,rise,steps):
    """The photographed opening has a flat sill, vertical jambs and a segmental crown."""
    radius=width*width/(8*rise)+rise/2
    points=[(x-width/2,sill),(x+width/2,sill)]
    for i in range(steps+1):
        u=width*(.5-i/steps)
        z=head-radius+sqrt(max(0,radius*radius-u*u))
        points.append((x+u,z))
    return Polygon(points)

def _opening(row,lod):
    return _arch(row['center'],row['width'],row['sill'],row['head'],
                 .134*row['width'],8 if lod else 16)

def apertures(d,lod):
    return [_opening(row,lod) for key in ('upper','lower') for row in d['windows'][key]]

def _surrounds(f,rows,lod,level):
    # In the straightened photograph the cement is uninterrupted between windows
    # within groups of two, three and two. The wide masonry piers remain exposed.
    for left,right in [(0,2),(2,5),(5,7)]:
        group=rows[left:right];holes=[_opening(row,lod) for row in group]
        x0=min(r['center']-r['width']/2 for r in group)-.24
        x1=max(r['center']+r['width']/2 for r in group)+.24
        bottom=min(r['sill'] for r in group)-.145
        top=max(r['head'] for r in group)+.245
        panel=box(x0,bottom,x1,top).difference(unary_union(holes))
        f.prism(panel,.008,.047,LIME,f'{level} lime panel {left+1}-{right}')

def _light(f,row,level,i,lod):
    x,w,z0,z1=row['center'],row['width'],row['sill'],row['head']
    h=z1-z0;hole=_opening(row,lod);sides=8 if lod else 16
    inner=_arch(x,w-.095,z0+.047,z1-.049,w*.126,sides)
    f.prism(hole.difference(inner),-.245,.047,WEATHERED,f'{level} {i} inner cement reveal')
    glass=_arch(x,w-.175,z0+.091,z1-.102,w*.117,sides)
    f.prism(inner.difference(glass),-.238,-.104,CAST,f'{level} {i} dark arch frame')
    # The dark upper fanlight is separated from the main panes by a deep head rail.
    top_rail=z1-h*.245
    fan=glass.intersection(box(x-w,top_rail,x+w,z1))
    f.prism(fan,-.284,-.261,CAST,f'{level} {i} shaded arched fanlight')
    panes=glass.intersection(box(x-w,z0,x+w,top_rail))
    glazing=SKY if i in (3,4,5) else SHADE
    f.prism(panes,-.284,-.268,glazing,f'{level} {i} recessed glazing')
    frame=WOOD if level=='lower' else STEEL
    inside=panes.buffer(-.038,join_style=2)
    if level=='lower':
        uprights=[(x,.042)]
        transoms=[(.245,.014),(.495,.014),(.745,.014)]
    elif i in (3,4,5):
        uprights=[(x-w*.159,.023),(x+w*.159,.023)]
        transoms=[(.30,.022),(.68,.022)]
    else:
        uprights=[(x,.031)]
        transoms=[(.39,.019),(.72,.019)]
    wires=[box(u-half,z0,u+half,top_rail)for u,half in uprights]
    for frac,half in transoms:
        z=z0+.091+(top_rail-z0-.091)*frac
        wires.append(box(x-w,z-half,x+w,z+half))
    mullions=panes.difference(inside.difference(unary_union(wires)))
    f.prism(mullions,-.259,-.200,frame,f'{level} {i} inner sash')
    if not lod:
        rail=glass.intersection(box(x-w,top_rail-.022,x+w,top_rail+.025))
        f.prism(rail,-.198,-.155,CAST,f'{level} {i} fanlight cross rail')
    f.prism(box(x-.55*w,z0-.124,x+.55*w,z0-.042),.008,.196,WEATHERED,f'{level} {i} sill')

def _blossoms(f,x,z,w,index,lod,label):
    """Three-dimensional, separately coloured leaves and blossoms on a shallow tray."""
    meshes={mat:([],[])for mat in (LEAF,GREEN,ROSE,PETAL)}
    def leaf(mat,u,zz,depth,rx,rz):
        verts,faces=meshes[mat];base=len(verts)
        verts.extend([f.point(u,zz+rz,depth),f.point(u,zz-rz,depth)]+[
            f.point(u+rx*cos(j*pi/3),zz,depth+.60*rx*sin(j*pi/3)) for j in range(6)])
        for j in range(6):
            a=base+2+j;b=base+2+(j+1)%6
            faces.extend([(base,a,b),(base+1,b,a)])
    n=10 if lod else 18
    for k in range(n):
        t=k/(n-1);u=x+w*(t-.5)*.95
        vary=sin(2.31*k+.46*index)
        leaf(LEAF,u,z+.026+.045*vary,.265,.076 if lod else .054,.083+.025*cos(k))
        if k%3!=2:
            drop=.065+.055*(1+sin(k*1.43+index))
            leaf(GREEN,u+.012,z-.062-drop*.43,.305,.044,drop)
        for dy,du,mat in [(0.,.0,ROSE)]+([]if lod else [(.025,.027,PETAL)]):
            leaf(mat,u+du,z+.249+.034*vary+dy,.322+.032*cos(index+k),
                 .095 if lod else .075,.088 if lod else .072)
    for mat,(verts,faces) in meshes.items():
        if verts:f.builder.add(verts,faces,mat,label+' '+mat)

def _basket(f,row,level,i,lod):
    x,z,w=row['center'],row['sill'],row['width']*.70
    low=z-.035;high=z+.21;half=w/2
    # Each box has an open wire cage held from two brackets placed on the stone sill.
    f.box(x,z-.024,w,.042,.24,.175,CAST,f'{level} {i} planter floor')
    for u in (x-half,x+half):
        f.line((u,z-.17,.048),(u,low,.32),.017,SASH,5,f'{level} {i} planter bracket')
        f.line((u,low,.32),(u,high,.32),.013,SASH,5,f'{level} {i} box corner')
        f.line((u,high,.32),(u,high,.033),.013,SASH,5,f'{level} {i} side rail')
    for zz in (low,high):
        f.line((x-half,zz,.32),(x+half,zz,.32),.015,SASH,5,f'{level} {i} front rail')
    if not lod:
        for j in range(1,6):
            u=x-half+w*j/6
            f.line((u,low,.32),(u,high,.32),.009,SASH,5,f'{level} {i} fine wire')
    _blossoms(f,x,z,w,i+(7 if level=='upper' else 0),lod,f'{level} {i} flower box')

def install(facade,d,lod):
    for level in ('upper','lower'):
        rows=d['windows'][level]
        _surrounds(facade,rows,lod,level)
        for i,row in enumerate(rows,1):
            _light(facade,row,level,i,lod)
            _basket(facade,row,level,i,lod)
