"""Two photo-registered, intersecting surfaces at the garden entrance and Yanqing Road."""
from shapely.geometry import Point,Polygon,box
from shapely.ops import unary_union
from photo_architecture import opening
from court_layout import (COURT_END,STREET_END,COURT_WINDOWS,STREET_WINDOWS,apertures,
                           DOOR_CENTER,ARCH_BOTTOM,ARCH_SPRING,ARCH_HEIGHT)
from residence_materials import (IVORY_RENDER,PEBBLEDASH,GREEN,IRON,LIGHT,SHADE,SILL,
                                 PLINTH,LEAD,CLAY)
from sashes import glazing,shutters


def shell(f,outline,holes,overlay,name):
    surface=outline.difference(unary_union(list(holes.values())))
    f.solid(surface,-.24,0,PEBBLEDASH,name+' | exposed aggregate wall and opening reveals')
    f.solid(surface.intersection(overlay),.001,.018,IVORY_RENDER,name+' | continuous ivory render')


def dress(f,bounds,name,lod,head=False):
    x0,z0,x1,z1=bounds
    hole=box(*bounds)
    surround=box(x0-.078,z0-.064,x1+.079,z1+.096).difference(hole)
    f.solid(surround,.003,.039,IVORY_RENDER,name+' | cement surround')
    f.rect(x0-.10,x1+.10,z0-.058,z0+.004,.005,.104,SILL,name+' | weathered sill')
    if head:
        f.rect(x0-.106,x1+.106,z1+.056,z1+.167,.018,.079,IVORY_RENDER,name+' | raised lintel')
        if not lod:
            f.rect(x0-.124,x1+.124,z1+.155,z1+.182,.015,.10,SILL,name+' | thin hood lip')


def entrance(f,lod):
    holes=apertures(COURT_WINDOWS)
    door=opening(DOOR_CENTER,ARCH_BOTTOM,.96,ARCH_HEIGHT-ARCH_BOTTOM,ARCH_HEIGHT-ARCH_SPRING,18 if lod else 36)
    holes['recessed arch']=door
    field=unary_union([box(COURT_END,0,-3.04,6.84),box(-3.04,0,0,5.15)])
    rendered=unary_union([box(COURT_END,0,-8.57,6.85),box(-6.75,0,-5.71,6.85),
                          box(-5.79,0,-2.84,3.25),box(-.29,0,0,6.85)])
    shell(f,field,holes,rendered,'East entrance')
    cut=unary_union(list(holes.values()))
    f.solid(box(COURT_END,0,0,.84).difference(cut),.008,.023,PLINTH,'East entrance | plinth')
    for name,bounds in COURT_WINDOWS.items():
        dress(f,bounds,name,lod,name in {'court upper sash','landing louvres'})
        if name=='landing louvres':
            shutters(f,bounds,name,lod,(7,6))
        elif name!='court upper sash':
            glazing(f,bounds,name,1 if name in ('stair side light','stair upper light') else 2,3)
    # The arched aperture has a continuous hollow lining and an actual recessed back.
    outer=door.buffer(.087,join_style=1)
    f.solid(outer.difference(door).intersection(box(-5.3,ARCH_BOTTOM,-3.74,2.78)),
            -.005,.069,IVORY_RENDER,'Recessed entrance | arched render')
    inner=door.buffer(-.055)
    f.solid(door.difference(inner),-.54,-.229,IVORY_RENDER,'Recessed entrance | deep lining')
    f.solid(inner,-.55,-.521,SHADE,'Recessed entrance | shaded rear')
    badge=Point(DOOR_CENTER,2.98).buffer(.175,quad_segs=8 if lod else 20)
    f.solid(badge,.018,.039,SILL,'Recessed entrance | circular medallion')
    f.solid(badge.difference(badge.buffer(-.037)),.038,.071,IVORY_RENDER,'Recessed entrance | raised circular rim')
    f.rect(-5.74,-2.83,3.17,3.23,.014,.105,SILL,'Recessed entrance | cornice')
    # The cheeks' continuous sloping tops are visible. Intermediate treads are masked.
    for side in [-5.33,-3.80]:
        along=f.face(side,-2.25,0,1)
        profile=Polygon([(0,.0),(2.25,.0),(2.25,.70),(1.87,.70),(0,.16)])
        along.solid(profile,-.12,.02,IVORY_RENDER,'Recessed entrance | sloping stair cheek')
        along.band([(0,.16),(1.87,.70),(2.25,.70)],.052,-.14,.036,SILL,'Recessed entrance | cheek coping')
    f.b.plan_prism(box(-5.32,-.39,-3.79,.03),.015,.605,SILL,'Recessed entrance | visible upper landing')
    # Visible drainpipe with offset below the upper sill and a projecting discharge elbow.
    f.rail([(-2.66,-.10,.04),(-2.66,-.10,3.02),(-2.82,-.14,3.19),
            (-2.82,-.14,5.64),(-2.77,-.29,5.75)],.050,IRON,'East entrance | cast iron downpipe',8 if lod else 14)
    for z in (1.40,3.37,4.71):
        f.rail([(-2.82,-.015,z),(-2.82,-.145,z)],.064,IRON,'East entrance | pipe socket',8)


def street(f,lod):
    holes=apertures(STREET_WINDOWS)
    outline=unary_union([box(0,0,3.,5.15),box(3.,0,STREET_END,6.08)])
    cap=unary_union([box(0,4.39,2.98,6.14),box(2.97,5.45,STREET_END,6.14),
                     box(0,0,.27,6.1),box(STREET_END-.21,0,STREET_END,6.14)])
    shell(f,outline,holes,cap,'North street elevation')
    f.solid(box(0,0,STREET_END,.82).difference(unary_union(list(holes.values()))),
            .009,.023,PLINTH,'North street elevation | plinth')
    for name,bounds in STREET_WINDOWS.items():
        dress(f,bounds,name,lod, name in {'middle shutters','far shutters','near-open'})
        if name in ('middle shutters','far shutters'):
            shutters(f,bounds,name,lod,(73,66) if name=='middle shutters' else (9,13))
        elif name not in ('near-open','attic-green','attic-pale'):
            glazing(f,bounds,name,4 if name=='garden lower divided sash' else 2,3)
    f.rail([(3.01,-.073,.05),(3.01,-.073,5.82),(3.08,-.24,6.03)],
           .042,IRON,'North street elevation | rainwater pipe',8 if lod else 14)
