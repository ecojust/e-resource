"""Four-storey E building, reconstructed from the municipal elevations and two apartment plans.

The north court face is y=0. Positive x runs west along the facade. Positive y points
from the courtyard into the building. Dimensions and lower-confidence returns are
listed in measurements/south-block.json.
"""
from shapely.geometry import box
from shapely.ops import unary_union

from photo_architecture import Facade, opening
from striped_render import MATERIAL, TEXTURE, apply_to_parts

LENGTH = 67.04
DEPTH = 10.03
GROUND_TOP = 3.05
PITCH = 3.4
SILL = 0.71
TOP = GROUND_TOP + 3 * PITCH
LOW_TOP = TOP - PITCH
TOWERS = (-20.08, 0.0, 20.12)
TOWER_WIDTH = 3.32
TOWER_FRONT = -1.64
TOP_LIMIT = 20.18
ENTRY_WIDTH = 1.53
ENTRY_HEAD = 2.42

SAND = 'E warm buff cement'
FRAME = 'E pale grey sash'
GLASS = 'E courtyard glazing'
REVEAL = 'E deep reveal'
BASE = 'E dark plinth'
CAP = 'E cement coping'
ROOF = 'E weathered flat roof'
GRILLE = 'E brown grille'
STAIR_GLASS = 'E smoked stair lights'
STAIR_PANEL = 'E recessed grey stair panels'
SOUTH_PALETTE = {
    MATERIAL: {'color': [1., 1., 1.], 'roughness': .91, 'texture': str(TEXTURE)},
    SAND: {'color': [.64, .455, .307], 'roughness': .90},
    FRAME: {'color': [.52, .50, .43], 'roughness': .57},
    GLASS: {'color': [.20, .255, .254], 'roughness': .28, 'metallic': .13},
    REVEAL: {'color': [.088, .076, .066], 'roughness': .87},
    BASE: {'color': [.265, .228, .19], 'roughness': .88},
    CAP: {'color': [.57, .463, .35], 'roughness': .82},
    ROOF: {'color': [.29, .273, .246], 'roughness': .93},
    STAIR_GLASS: {'color': [.075,.094,.095], 'roughness': .31, 'metallic': .12},
    STAIR_PANEL: {'color': [.317,.304,.275], 'roughness': .79},
    GRILLE: {'color': [.20, .15, .123], 'roughness': .67, 'metallic': .14},
}


def _slab(b, label, xlo, xhi, ylo, yhi, z, thick, material):
    b.box(((xlo+xhi)/2, (ylo+yhi)/2, z-thick/2),
          (xhi-xlo, yhi-ylo, thick), material, label='E '+label)


def _windows(f, rows, lod):
    """Cut every recess and place sashes behind the wall. Rows use facade-local u."""
    for u, z, width, height, columns in rows:
        hole = opening(u, z, width, height)
        if lod:
            # Subpixel bevels on the glazed faces resolve into square-edged recesses at distance.
            # Partition the flat frame so each short transom stops at its mullion.
            l, r, bottom, top = u-width/2, u+width/2, z, z+height
            vertices, faces = [], []
            def rectangle(left, right, low, high):
                n = len(vertices)
                vertices.extend(f.point(a,c,-.17) for a,c in
                                [(left,low),(right,low),(right,high),(left,high)])
                faces.append((n,n+1,n+2,n+3))
            f.builder.add([f.point(a,c,-.267) for a,c in
                           [(l-.004,bottom-.004),(r+.004,bottom-.004),
                            (r+.004,top+.004),(l-.004,top+.004)]], [(0,1,2,3)], GLASS, f.label+'/glass')
            rectangle(l,r,bottom,bottom+.052)
            rectangle(l,r,top-.052,top)
            rectangle(l,l+.052,bottom+.052,top-.052)
            rectangle(r-.052,r,bottom+.052,top-.052)
            bars = [l+j*width/columns for j in range(1,columns)]
            for center in bars:
                rectangle(center-.017,center+.017,bottom+.052,top-.052)
            for left, right in zip([l+.052]+[x+.017 for x in bars],
                                   [x-.017 for x in bars]+[r-.052]):
                rectangle(left,right,bottom+height*.66-.019,bottom+height*.66+.019)
            f.builder.add(vertices,faces,FRAME,f.label+'/sash')
            continue
        f.prism(hole.buffer(.009, join_style=2), -.285, -.267, GLASS, 'glass')
        inset = .052
        inner = hole.buffer(-inset, join_style=2)
        bars = [box(u-width/2+width*j/columns-.017, z, u-width/2+width*j/columns+.017, z+height)
                for j in range(1, columns)]
        if not lod or height > 1.3:
            bars.append(box(u-width/2, z+height*.66-.019, u+width/2, z+height*.66+.019))
        metal = hole.difference(inner.difference(unary_union(bars)))
        f.prism(metal, -.22, -.17, FRAME, 'sash')
        if not lod:
            f.box(u, z-.026, width+.085, .052, .23, -.018, CAP, 'slender sill')


def _band_rows(points, floors):
    return [(u, GROUND_TOP+level*PITCH+SILL, width, PITCH*.445, cols)
            for level in floors for u,width,cols in points]


def _cornice(f, top):
    f.box(0, top-.025, f.length+.08, .17, .44, .115, SAND, 'roof fascia')
    f.box(0, top+.125, f.length+.16, .095, .56, .15, CAP, 'roof lip')


def _court_bay(b, left, right, levels, points, garage_edges, lod, name):
    f = Facade(b,(left,0),(right,0),'E court '+name)
    mid=(left+right)/2
    pts=[(x-mid,width,cols) for x,width,cols in points]
    rows=_band_rows(pts, range(levels))
    garage_holes=[box(a-mid, .08, z-mid, 2.40) for a,z in garage_edges]
    f.wall(0, GROUND_TOP+levels*PITCH, garage_holes+[opening(*r[:4]) for r in rows], .23, MATERIAL)
    _windows(f, rows, lod)
    for a,z in garage_edges:
        midx=(a+z)/2
        inner=Facade(b,(a,1.12),(z,1.12),'E court '+name)
        inner.box(0,1.23,z-a,2.40,.065,-.05,REVEAL,'garage recess')
        if not lod:
            inner.box(0,2.27,z-a-.06,.13,.07,.03,GRILLE,'garage upper rail')
        f.box(midx-mid,2.50,z-a+.19,.13,.48,.12,SAND,'garage lintel')
    # The stacked short horizontal fins are separated pieces, visible between windows in plate 19.
    for idx in range(0,len(points),2):
        x=points[idx][0]
        width=min(2.45,right-x-.12,x-left-.12)
        if width<.45:
            continue
        for level in range(levels):
            sill=GROUND_TOP+level*PITCH+SILL
            for k in range(3 if lod else 4):
                f.box(x-mid,sill-.15-k*.18,width*1.28,.058,.17,.054,CAP,'short spandrel ribs')
    _cornice(f,GROUND_TOP+levels*PITCH)


def _tower(b,xc,lod,name):
    half=TOWER_WIDTH/2
    a,e=xc-half,xc+half
    f=Facade(b,(a,TOWER_FRONT),(e,TOWER_FRONT),'E '+name+' tower')
    levels=[GROUND_TOP+i*PITCH+.15 for i in range(3)]
    # Plate 19 shows two separate narrow stair lights with a slim continuous centre pier.
    # The opaque panels above and below the stair glazing sit in the same two recessed channels.
    lights=(-.385,.385)
    rows=[(u,z,.52,2.66) for z in levels for u in lights]
    door=box(-ENTRY_WIDTH/2, -.025, ENTRY_WIDTH/2, ENTRY_HEAD)
    holes=[opening(*r) for r in rows]
    f.wall(0,TOP+.85,[door]+holes,.21,SAND)
    for u in lights:
        for z in levels:
            aperture=opening(u,z,.52,2.66)
            f.prism(aperture.buffer(.008,join_style=2),-.093,-.073,STAIR_GLASS,'stair glazing')
            for yy in (z+.48,z+1.55,z+2.14):
                f.box(u,yy,.52,.045,.06,-.034,GRILLE,'horizontal stair transoms')
        for za,zb in [(ENTRY_HEAD+.16,levels[0]),(levels[0]+2.66,levels[1]),
                      (levels[1]+2.66,levels[2]),(levels[-1]+2.66,TOP+1.70)]:
            f.box(u,(za+zb)/2,.51,zb-za,.045,.03,STAIR_PANEL,'recessed infill strip')
    # The three masonry blades rise by different amounts. The middle blade splits the tall lights.
    # At ground level the central opening is left clear for the covered way.
    for idx,(u,width,dx,rise,zmin) in enumerate([
        (-1.25,.37,.21,1.10,0),(-.72,.145,.19,1.72,ENTRY_HEAD+.08),
        (0,.16,.36,2.04,ENTRY_HEAD+.08),(.72,.145,.19,1.72,ENTRY_HEAD+.08),(1.25,.37,.21,1.10,0)]):
        zmax=TOP+rise
        f.box(u,(zmin+zmax)/2,width,zmax-zmin,.34+dx,dx/2,SAND,'stepped blade '+str(idx+1))
        f.box(u,zmax+.034,width+.04,.068,.39+dx,dx/2,CAP,'blade head')
    f.box(0,ENTRY_HEAD+.075,ENTRY_WIDTH+.18,.15,.53,.07,CAP,'door lintel')
    for x in (a,e):
        start,end=((x,0),(x,TOWER_FRONT)) if x==a else ((x,TOWER_FRONT),(x,0))
        side=Facade(b,start,end,'E '+name+' tower cheek')
        side.wall(.03,TOP+.83,thickness=.19,material=SAND)
    _slab(b,name+' tower roof',a,e,TOWER_FRONT,0,TOP+.87,.13,ROOF)
    _slab(b,name+' entrance landing',xc-ENTRY_WIDTH/2,xc+ENTRY_WIDTH/2,TOWER_FRONT-.28,1.35,.08,.08,BASE)
    for x in (xc-ENTRY_WIDTH/2-.04,xc+ENTRY_WIDTH/2+.04):
        b.box((x,-.14,1.21),(.08,2.92,2.42),BASE,label='E '+name+' portal reveal')
    # A recessed stone landing beyond the opening is distinct from the open approach.
    _slab(b,name+' inner landing',xc-.85,xc+.85,1.45,2.3,.19,.11,BASE)


def _rear(b,lod):
    blocks=[(-LENGTH/2,-TOP_LIMIT,2,'east end'),(-TOP_LIMIT,TOP_LIMIT,3,'middle'),(TOP_LIMIT,LENGTH/2,2,'west end')]
    # Bay centres follow the standard plan. Profiles and divisions on the garden side are lower-confidence.
    xs=[-31.32,-27.3,-22.9,-18.1,-13.4,-8.9,-4.2,0,4.2,8.9,13.4,18.1,22.9,27.3,31.32]
    for a,z,levels,label in blocks:
        f=Facade(b,(z,DEPTH),(a,DEPTH),'E south '+label)
        mid=(a+z)/2
        pts=[(mid-x,1.65 if abs(x)<.01 else 2.17,3) for x in xs if a+.95<x<z-.95]
        rows=_band_rows(pts,range(levels))
        rows += [(u,.85,width*.87,1.34,cols) for u,width,cols in pts]
        f.wall(0,GROUND_TOP+levels*PITCH,[opening(*r[:4]) for r in rows],.24,MATERIAL)
        _windows(f,rows,lod)
        _cornice(f,GROUND_TOP+levels*PITCH)
    for i,x in enumerate((-9.73,10.12)):
        for lev in (0,1):
            z=GROUND_TOP+lev*PITCH
            _slab(b,'garden terrace floor',x-2.52,x+2.52,DEPTH,DEPTH+.64,z+.02,.13,CAP)
            for sign in (-1,1):
                b.box((x+sign*2.46,DEPTH+.30,z+.45),(.12,.62,.9),SAND,label='E terrace return')
            b.box((x,DEPTH+.58,z+.42),(4.99,.115,.84),SAND,label='E terrace parapet')
            b.box((x,DEPTH+.58,z+.88),(5.07,.16,.075),CAP,label='E terrace coping')


def _ends_and_roof(b,lod):
    for sign in (-1,1):
        x=sign*LENGTH/2
        a,c=((x,DEPTH),(x,0)) if sign<0 else ((x,0),(x,DEPTH))
        f=Facade(b,a,c,'E end '+('east' if sign<0 else 'west'))
        rows=_band_rows([(-2.28,1.35,2),(2.20,1.42,2)],range(2))
        f.wall(0,LOW_TOP,[opening(*r[:4]) for r in rows],.24,MATERIAL)
        _windows(f,rows,lod)
        _cornice(f,LOW_TOP)
        # Recessed fourth floor leaves the two open roof terraces depicted in the archival top plan.
        x=sign*TOP_LIMIT
        a,c=((x,DEPTH),(x,0)) if sign<0 else ((x,0),(x,DEPTH))
        g=Facade(b,a,c,'E setback '+('east' if sign<0 else 'west'))
        door=opening(-.60,LOW_TOP+.06,1.46,2.06)
        wins=[(2.48,LOW_TOP+.72,1.86,1.48,3)]
        g.wall(LOW_TOP,TOP,[door]+[opening(*r[:4]) for r in wins],.22,MATERIAL)
        _windows(g,wins+[(-.60,LOW_TOP+.06,1.46,2.06,2)],lod)
        _cornice(g,TOP)
        lo,hi=sorted((sign*TOP_LIMIT,sign*LENGTH/2))
        _slab(b,'end roof terrace',lo,hi,.03,DEPTH-.03,LOW_TOP+.038,.14,ROOF)
        # Low perimeter parapets over the terraced ends.
        for yy in (.025,DEPTH-.025):
            b.box(((lo+hi)/2,yy,LOW_TOP+.30),(hi-lo,.17,.60),SAND,label='E low terrace parapet')
        b.box((sign*(LENGTH/2-.055),DEPTH/2,LOW_TOP+.31),(.16,DEPTH-.06,.62),SAND,label='E end parapet')
    _slab(b,'main roof',-TOP_LIMIT,TOP_LIMIT,.03,DEPTH-.03,TOP+.03,.17,ROOF)
    for yy in (.07,DEPTH-.07):
        b.box((0,yy,TOP+.20),(2*TOP_LIMIT,.14,.40),SAND,label='E high roof parapet')


def build_south(b,lod):
    """Add the complete E exterior to an existing builder and return the covered-way opening."""
    first=len(b.parts)
    half=TOWER_WIDTH/2
    # The court face between towers is measured in the nearly frontal municipal plate 19.
    edges=[-LENGTH/2,TOWERS[0]-half,TOWERS[0]+half,-half,half,TOWERS[2]-half,TOWERS[2]+half,LENGTH/2]
    for segment,(a,z) in enumerate(zip(edges[::2],edges[1::2])):
        outer=segment in (0,3)
        if outer:
            count=4
            points=[(a+(z-a)*(i+.5)/count,1.71 if i in (0,3) else 1.25,3 if i in (0,3) else 2) for i in range(count)]
        else:
            points=[(a+(z-a)*fraction,width,cols) for fraction,width,cols in
                    [(.075,.91,2),(.190,1.04,2),(.373,2.02,3),(.604,1.83,3),(.832,1.61,3)]]
        n=4 if outer else 5
        margin=.20
        spacing=(z-a-2*margin)/n
        gates=[(a+margin+i*spacing+.12,a+margin+(i+1)*spacing-.12) for i in range(n)]
        _court_bay(b,a,z,2 if outer else 3,points,gates,lod,('E end','E centre','W centre','W end')[segment])
    for idx,x in enumerate(TOWERS):
        _tower(b,x,lod,('east','centre','west')[idx])
    _rear(b,lod)
    _ends_and_roof(b,lod)
    _slab(b,'ground slab',-LENGTH/2,LENGTH/2,0,DEPTH,.015,.12,BASE)
    apply_to_parts(b.parts[first:],PITCH,GROUND_TOP+SILL)
    return {'label':'E central stair entrance','x_center':0.,'front_y':TOWER_FRONT,'inner_open_y':1.35,
            'clear_width_m':ENTRY_WIDTH,'clear_from_z':.08,'clear_to_z':ENTRY_HEAD,'approach':'north, negative y'}
