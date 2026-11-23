"""Exterior closure of the folded, three-storey residence at 313 South Xiangyang Road.

All coordinates are east, north and up in metres. The stepped parapet encloses
a flat concrete roof. Two courtyard facades and the photographed west windows
are assembled separately with their own apertures and registered details.
"""
from pathlib import Path
import sys
from math import hypot
from shapely.geometry import Polygon

MEASUREMENTS = Path(__file__).resolve().parent.parent / 'measurements'
sys.path.insert(0, str(MEASUREMENTS))
from plan_points import load, ground_ring, facade_point

RENDER = 'Xiangyang 313 | pale courtyard render'
PLINTH = 'Xiangyang 313 | warm gray street-level plinth'
DECK = 'Xiangyang 313 | weathered gray flat concrete'
COPING = 'Xiangyang 313 | light cement parapet coping'
FLASHING = 'Xiangyang 313 | dull roof-edge flashing'
PALETTE = {
    RENDER: {'color':[.735,.677,.548], 'roughness':.94},
    PLINTH: {'color':[.485,.456,.392], 'roughness':.94},
    DECK: {'color':[.365,.347,.307], 'roughness':.93},
    COPING: {'color':[.674,.636,.535], 'roughness':.9},
    FLASHING: {'color':[.426,.419,.389], 'roughness':.84, 'metallic':.12},
}
WEST_RIM = 12.20
NORTH_PIPE_RIM = 11.33
NORTH_COURT_RIM = 1.43 + 1.08 * 9.4543
SOUTH_COURT_RIM = 11.33
ROOF_DECK = 11.04

def envelope():
    """Actual perimeter clockwise, with the southern upper wall overhang.

    p06 remains the original western bay junction. s06 is the actual, more
    southerly end of the photographed upper south curtain. The extra link
    between the two returns to the cadastral corner behind this projection.
    """
    record=load()
    v=ground_ring(record)
    points={f'p{i:02}':list(a) for i,a in enumerate(v)}
    front=facade_point('case1',0,0,0,record)
    rear=facade_point('case1',0,.6725,0,record)
    points['p03']=[front[0]+2.433,front[1]]
    points['p04']=[front[0]-2.163,front[1]]
    points['p05']=[rear[0]-2.125,rear[1]]
    points['s06']=[rear[0]-9.311,rear[1]]
    for key,xy in record['assembly']['west_fold']['working_points_EN_m'].items():
        points[key]=list(xy)
    return points

def strip(a,b,width=0.2,inset=0):
    """Right-side band of a clockwise exterior edge inside the building."""
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=hypot(dx,dy)
    nx,ny=dy/length,-dx/length
    return Polygon([(a[0]+nx*inset,a[1]+ny*inset),
                    (b[0]+nx*inset,b[1]+ny*inset),
                    (b[0]+nx*(width+inset),b[1]+ny*(width+inset)),
                    (a[0]+nx*(width+inset),a[1]+ny*(width+inset))])

def wall(b,a,c,z0,z1,label,material=RENDER,width=.23,inset=0):
    if z1-z0 > .001:
        b.plan_prism(strip(a,c,width,inset),z0,z1,material,label)

def tapered_head(b,a,c,base,za,zc,width,label,inset=0,material=RENDER):
    line=list(strip(a,c,width,inset).exterior.coords)[:-1]
    verts=[(x,y,base)for x,y in line]
    verts.extend((x,y,z)for (x,y),z in zip(line,(za,zc,zc,za)))
    # Clockwise plan requires the reverse top winding and direct bottom winding.
    faces=[(0,1,2,3),(7,6,5,4)]
    faces.extend((j+4,(j+1)%4+4,(j+1)%4,j)for j in range(4))
    b.add(verts,faces,material,label)

def add_courtyard_shell(b,lod=False):
    for name,material in PALETTE.items():
        b.palette.setdefault(name,material)
    v=envelope();keys=['p00','p01','p02','p03','p04','p05','s06','p06','p07','p08','p09','p10']
    upper=Polygon([v[k] for k in keys]);assert upper.is_valid
    lower=Polygon(ground_ring())
    b.plan_prism(lower,-.075,.025,PLINTH,'courtyard shell / folded ground-bearing slab')
    # Only the projecting part between the two measured west roof elevations
    # is raised. Its unphotographed rear joint is the shortest straight chord
    # between the endpoints of the projection.
    raised=Polygon([v[k] for k in ('p06','p07','p08','p09')])
    lower_deck=upper.difference(raised)
    b.plan_prism(lower_deck,ROOF_DECK-.17,ROOF_DECK,DECK,'courtyard shell / main flat concrete slab')
    high_deck=ROOF_DECK+WEST_RIM-NORTH_PIPE_RIM
    b.plan_prism(raised,high_deck-.17,high_deck,DECK,'courtyard shell / raised western bay flat deck')
    wall(b,v['p06'],v['p09'],ROOF_DECK-.17,high_deck,'courtyard shell / west roof vertical change of level',DECK,.15)


    # The eastern wall and northern wing return are independently distinguishable
    # in plan. Outer east-side openings are unmeasured and are left unornamented.
    east=v['p02'],v['p03']
    wall(b,*east,.025,10.98,'courtyard shell / long east wall')
    tapered_head(b,*east,10.98,NORTH_PIPE_RIM,SOUTH_COURT_RIM,.23,'courtyard shell / east parapet')
    for j,k,label in [('p00','p01','north wing recessed link'),('p01','p02','north wing end wall')]:
        wall(b,v[j],v[k],.025,NORTH_PIPE_RIM,'courtyard shell / '+label)
    # This 0.85 m side closes between the plan corner p06 and the photographic
    # outer plane, without spanning the window wall between the two south bays.
    wall(b,v['s06'],v['p06'],.025,SOUTH_COURT_RIM,'courtyard shell / west end of projected southern wall')
    # The photographed undercut and upper return between p04 and p05 are
    # supplied by the south facade. Only its unobserved lower continuation is filled.
    wall(b,v['p04'],v['p05'],.025,1.43,'courtyard shell / under southern bay return',PLINTH)
    wall(b,v['p03'],v['p04'],.025,1.43,'courtyard shell / lower southern projecting base',PLINTH)
    wall(b,v['p05'],v['s06'],.025,1.43,'courtyard shell / lower southern recessed base',PLINTH)
    north_grade=facade_point('case2',0,0,.8989)[2]
    wall(b,v['p10'],v['p00'],.025,north_grade,'courtyard shell / northern window wall below photographed panel',PLINTH,.225)
    # The registered aperture panel ends 105.5 mm before the northern return.
    # Continue its facing on the same wall plane, keeping the photographed left slit.
    north_panel_end=facade_point('case2',-3.3245,0,0)[:2]
    wall(b,north_panel_end,v['p00'],north_grade,NORTH_COURT_RIM,
         'courtyard shell / upright infill at north window wall junction',RENDER,.225)
    # Narrow sub-grade slab echoes the measured discrepancy at the southern face.
    extension=upper.difference(lower)
    if not extension.is_empty:
        b.plan_prism(extension,.025,.115,PLINTH,'courtyard shell / footprint transition at projecting ends')

    # The parapet is resolved in the street views at the western bay and north
    # pipe, and in the registered northern court view. A constant roof slab
    # and variable upstand preserve those observed exterior levels.
    top={'p00':NORTH_COURT_RIM,'p01':NORTH_PIPE_RIM,'p02':NORTH_PIPE_RIM,
         'p03':SOUTH_COURT_RIM,'p04':SOUTH_COURT_RIM,'p05':SOUTH_COURT_RIM,
         's06':SOUTH_COURT_RIM,'p06':WEST_RIM,'p07':WEST_RIM,'p08':WEST_RIM,
         'p09':NORTH_PIPE_RIM,'p10':NORTH_PIPE_RIM}
    for j,k in zip(keys,keys[1:]+keys[:1]):
        a,c=v[j],v[k]; za,zc=top[j],top[k];label='courtyard shell / '+j+'–'+k
        # The trim is behind every other author's external skin. On the
        # northern photo wall the full-length aperture-bearing panel reaches
        # its own constant photographic eave datum.
        if (j,k)==('p10','p00'):za=zc=NORTH_COURT_RIM
        if (j,k)==('s06','p06'):za=zc=SOUTH_COURT_RIM
        if (j,k)==('p00','p01'):za=zc=NORTH_PIPE_RIM
        west_high=j in ('p06','p07','p08')
        if west_high:za=zc=WEST_RIM
        if j=='p09':za=zc=NORTH_PIPE_RIM
        deck=high_deck if west_high else ROOF_DECK
        tapered_head(b,a,c,deck-.002,za-.035,zc-.035,.135,label+' inner parapet',inset=.195,material=DECK)
        # Western coping profiles belong to the street window model.
        if j not in ('p06','p07','p08','p09'):
            # Flat top portions match the panel top exactly.
            if abs(za-zc)<.001:
                wall(b,a,c,za-.034,za+.014,label+' coping',COPING,.32,-.015)
        if not lod:
            wall(b,a,c,deck+.002,deck+.059,label+' base flashing',FLASHING,.063,.321)
