"""The ochre southwest gable of the bank staff house, as photographed from 510 Jiaozhou Road."""
from math import sqrt
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'reddish brown render': {'color': [.61,.33,.24], 'roughness': .94},
    'pale timber': {'color': [.82,.71,.58], 'roughness': .84},
    'painted eave edge': {'color': [.85,.82,.74], 'roughness': .78},
    'dark wood': {'color': [.19,.17,.16], 'roughness': .75},
    'deep reveal': {'color': [.19,.17,.15], 'roughness': .96},
    'smoky glass': {'color': [.26,.31,.33], 'roughness': .32},
    'attic glass': {'color': [.39,.43,.43], 'roughness': .31},
    'window grille': {'color': [.36,.34,.32], 'roughness': .72, 'metallic': .27},
    'sill': {'color': [.47,.30,.22], 'roughness': .83},
    'red clay tile': {'color': [.62,.33,.23], 'roughness': .90},
    'tile lap': {'color': [.44,.24,.18], 'roughness': .93},
}
HALF_WIDTH = 2.81
SHOULDER = 4.87
APEX = 7.00
WINDOW_BOTTOM = .41
WINDOW_HEAD = 2.55
ATTIC_SILL = 4.24
ATTIC_HEAD = 5.16

def band(points, width):
    return LineString(points).buffer(width/2, cap_style=2, join_style=2)

def aperture(center, side, lod):
    radius = .43 if side else .46
    if not side:
        return box(center-radius, WINDOW_BOTTOM, center+radius, WINDOW_HEAD)
    # The tall jamb faces the middle window. Only the outer shoulder curves downward.
    steps = 7 if lod else 24
    pts = [(center-radius,WINDOW_BOTTOM),(center+radius,WINDOW_BOTTOM)]
    for i in range(steps+1):
        x = center+radius-2*radius*i/steps
        u = (side*(x-center)+radius)/(2*radius)
        fall = .70*(1-sqrt(max(0.,1-(.94*u)**2)))/(1-sqrt(1-.94**2))
        pts.append((x, WINDOW_HEAD-fall))
    return Polygon(pts)

def window(f, outline, label, lod, attic=False):
    inner = outline.buffer(-.062, join_style=2)
    x0,z0,x1,z1 = outline.bounds
    center=(x0+x1)/2
    f.prism(outline.difference(inner),-.18,-.055,'dark wood',label+' perimeter')
    f.prism(inner,-.231,-.211,'attic glass' if attic else 'smoky glass',label+' glass')
    for i,fraction in enumerate([.5] if attic else [.48,.76]):
        z=z0+(z1-z0)*fraction
        f.prism(box(x0,z-.018,x1,z+.018).intersection(inner),-.19,-.14,'dark wood',label+' sash '+str(i))
    f.prism(box(center-.02,z0,center+.02,z1).intersection(inner),-.193,-.141,'dark wood',label+' mullion')
    f.box(center,z0-.044,x1-x0+.12,.081,.16,.019,'sill',label+' projecting sill')
    if lod or attic:
        return
    limit=inner.intersection(box(x0,z0,x1,z0+(z1-z0)*.70))
    for col in range(2):
        x=x0+(col+.5)*(x1-x0)/2
        for row in range(2):
            z=z0+.33+row*.52
            rhomb=band([(x,z+.25),(x+.14,z),(x,z-.25),(x-.14,z),(x,z+.25)],.015)
            grille=rhomb.intersection(limit)
            if not grille.is_empty:
                f.prism(grille,-.11,-.085,'window grille',label+' grille '+str(col)+str(row))

def add_building(builder,lod=False):
    f=Facade(builder,(-HALF_WIDTH,0),(HALF_WIDTH,0),'street gable')
    outline=Polygon([(-HALF_WIDTH,0),(HALF_WIDTH,0),(HALF_WIDTH,SHOULDER),(0,APEX),(-HALF_WIDTH,SHOULDER)])
    holes=[aperture(-1.30,-1,lod),aperture(0,0,lod),aperture(1.30,1,lod),box(-.43,ATTIC_SILL,.43,ATTIC_HEAD)]
    wall=outline.difference(unary_union(holes))
    f.prism(wall,-.32,-.018,'deep reveal','four recessed openings')
    f.prism(wall,-.018,.005,'reddish brown render','rendered wall')
    for hole,label in zip(holes,['north shoulder','middle window','south shoulder','attic window']):
        window(f,hole,label,lod,attic=label=='attic window')
    f.box(0,4.04,2*HALF_WIDTH-.10,.125,.085,.044,'pale timber','horizontal rail')
    for i,x in enumerate([-2.59,-.88,-.47,.54,1.04,2.53]):
        high=APEX-abs(x)/HALF_WIDTH*(APEX-SHOULDER)-.10
        low=3.89 if abs(x)>1.1 else 3.73
        f.box(x,(high+low)/2,.14 if abs(x)<1.1 else .114,high-low,.071,.055,'pale timber','upright '+str(i+1))
    f.box(0,ATTIC_HEAD+.03,1.16,.116,.078,.055,'pale timber','attic lintel')
    for side in [-1,1]:
        x=side*(HALF_WIDTH+.13);z0=SHOULDER-.03;z1=APEX+.12
        for offset,thick,back,front,mat,name in [(0,.155,-.30,.20,'painted eave edge','bargeboard'),(-.09,.052,-.26,.14,'dark wood','shadow'),(.095,.07,-.62,.145,'red clay tile','roof return')]:
            f.prism(band([(x,z0+offset),(0,z1+offset)],thick),back,front,mat,name+' '+str(side))
        if not lod:
            for i in range(1,17):
                a=i/17;b=a+.012
                cut=band([(x*(1-t),z0+(z1-z0)*t+.137)for t in (a,b)],.038)
                f.prism(cut,-.61,.142,'tile lap','joint '+str(side)+' '+str(i))
