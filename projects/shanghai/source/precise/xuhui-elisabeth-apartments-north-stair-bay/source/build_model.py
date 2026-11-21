"""Build the central north elevation of the Elisabeth Apartments at 1327 Middle Fuxing Road."""
from pathlib import Path
from math import ceil, hypot
import argparse
import json
import os
import sys

from shapely.geometry import Polygon, box as rectangle

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
import package_architectural_model as package
sys.path.insert(0, str(SOURCE.parents[1] / 'huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade
from stair_render import STONE, assign_uvs

ID = 'xuhui-elisabeth-apartments-north-stair-bay'
META = dict(id=ID, name='伊丽莎白公寓北立面主楼梯间与雨厦',
            viewer_page='elisabeth-apartments-north-stair-bay.html', heritage_group='4D011',
            heritage_address='复兴中路1327号', status='documented-north-stair-elevation',
            scope='中央主楼梯间、方雨厦、双柱和入口铁门，及两侧各一跨钢窗。',
            coordinate_convention='Local metres. X increases to the right in the published north elevation, Y into the building, Z up.')
DIMS = json.loads((SOURCE.parent/'measurements/north-elevation-dimensions.json').read_bytes())
SCALE = DIMS['metres_per_pixel']
MORTAR = 'Recessed sand mortar'
BRICK = 'Weathered red facing brick'
LIGHT_BRICK = 'Painted lower brick band'
GLASS = 'Grey green stair glass'
SKY = 'Cloud reflection in glass'
FRAME = 'Oxide red window steel'
PIGMENT = 'Dark red entrance render'
GREEN = 'Bottle green gate'
GATE_BACK = 'Shade inside vestibule'
METAL = 'Dark steel glazing bead'
CAP = 'Projecting cement sill'
COLUMN = 'Warm cement canopy columns'
CROWN = 'Shaded cement at the crown'
FIN = 'Pale folded crown bands'
PLAQUE = 'Green enamel address plate'
LETTER = 'Ivory address lettering'


def colour(rgb, roughness, metal=0):
    def linear(v):
        c = v / 255
        return c / 12.92 if c <= .04045 else ((c+.055)/1.055)**2.4
    return dict(color=[linear(i) for i in rgb], roughness=roughness, metallic=metal)


PALETTE = {STONE: dict(color=[1,1,1], roughness=.91, texture=str(SOURCE/'cement-render.png')),
           MORTAR: colour((115,102,88),.91), BRICK: colour((126,81,71),.82),
           LIGHT_BRICK: colour((177,160,137),.87), GLASS: colour((95,112,110),.28,.19),
           SKY: colour((135,149,141),.26,.26), FRAME: colour((106,66,63),.54,.2),
           PIGMENT: colour((121,68,60),.82), GREEN: colour((46,96,78),.47,.36),
           GATE_BACK: colour((54,64,56),.86), METAL: colour((63,63,57),.48,.46),
           CAP: colour((182,174,154),.83), COLUMN: colour((182,174,150),.82),
           CROWN: colour((145,135,118),.83), FIN: colour((202,193,170),.78), PLAQUE: colour((33,106,75),.42,.24),
           LETTER: colour((222,228,209),.53)}


def x(pixel):
    return (pixel-DIMS['x_origin'])*SCALE


def z(pixel):
    return (DIMS['grade_y']-pixel)*SCALE


def pane_grid(f, low, high, columns, rows, label, lod, depth=-.10):
    """Glazing and frame share one local facade plane, including the two facets of the V."""
    width = f.length
    a, b = low+.025, high-.025
    cw, rh = width/columns, (b-a)/rows
    for j in range(rows):
        for i in range(columns):
            center = -width/2+(i+.5)*cw
            mat = SKY if (i+2*j)%5 in (0,1) else GLASS
            f.box(center,a+(j+.5)*rh,cw,rh,.024,depth-.04,mat,label+' glass')
    for i in range(columns+1):
        stile = .052 if i in (0,columns) else .033
        f.box(-width/2+i*cw,(low+high)/2,stile,high-low,.078,depth,FRAME,label+' metal stiles')
    for j in range(rows+1):
        rail = .052 if j in (0,rows) else .029
        f.box(0,a+j*rh,width,rail,.068,depth-.003,FRAME,label+' sash rails')
    if not lod:
        for u in [-width/2+.038,width/2-.038]:
            f.box(u,(a+b)/2,.012,b-a,.020,depth+.01,METAL,label+' putty edge')


STAIR_HALF = (DIMS['tower_glazing_x'][1]-DIMS['x_origin'])*SCALE
TIP_DEPTH, EDGE_DEPTH = .78, .12
STAIR_FACE = hypot(STAIR_HALF,TIP_DEPTH-EDGE_DEPTH)


def folded_strip(builder, left, right, back, front, low, high, material, label):
    """Build both returns of a mitred band with the same front and back edge at its apex."""
    def at(s, depth):
        x = s*STAIR_HALF/STAIR_FACE
        # Cut each band at a fixed vertical plane. The offset faces of very narrow
        # steel meeting posts would cross if their ends moved along both normals.
        face_y = -TIP_DEPTH + abs(x)*(TIP_DEPTH-EDGE_DEPTH)/STAIR_HALF
        return x, face_y-depth*STAIR_FACE/STAIR_HALF
    stations=[left,0,right] if left<0<right else [left,right]
    outline=[at(t,back)for t in stations]+[at(t,front)for t in reversed(stations)]
    builder.prism(Polygon(outline),low,high,lambda u,v,h:(u,v,h),material,label)


def brick_band(builder, bottom, top, material, label, lod):
    """Give each course a joined return at the point, with recessed running-bond joints."""
    folded_strip(builder,-STAIR_FACE,STAIR_FACE,-.057,.052,bottom,top,MORTAR,label+'/Mortar bed')
    courses=max(2,round((top-bottom)/.071))
    pitch=(top-bottom)/courses
    for j in range(courses):
        low=bottom+j*pitch+.004
        high=bottom+(j+1)*pitch-.004
        if lod:
            edges=[-STAIR_FACE,STAIR_FACE]
        else:
            length=.223
            start=-STAIR_FACE
            offset=length/2 if j%2 else length
            edges=[start]+[start+offset+i*length for i in range(ceil(2*STAIR_FACE/length))
                           if start+offset+i*length<STAIR_FACE-.016]+[STAIR_FACE]
        for i,(a,c) in enumerate(zip(edges,edges[1:])):
            seam=0 if lod else .003
            folded_strip(builder,a+(seam if i else 0),c-(seam if c<STAIR_FACE else 0),
                         .045,.090,low,high,material,label+' brick courses')


def crown(builder,bottom,top):
    """The street photographs show eight deep continuous chevrons above the top stair window."""
    folded_strip(builder,-STAIR_FACE,STAIR_FACE,-.11,.074,bottom,top,CROWN,'Crown/Continuous recessed faces')
    count=8
    pitch=(top-bottom-.10)/count
    for i in range(count):
        base=bottom+.04+i*pitch
        folded_strip(builder,-STAIR_FACE-.028,STAIR_FACE+.028,.035,.280,
                     base,base+.125,FIN,'Crown horizontal fins')
        folded_strip(builder,-STAIR_FACE-.018,STAIR_FACE+.018,.030,.205,
                     base-.040,base,CROWN,'Crown/Stepped soffits')
    folded_strip(builder,-STAIR_FACE-.032,STAIR_FACE+.032,-.10,.285,
                 top-.074,top+.052,FIN,'Crown/Mitred upper coping')


def gate(f, b, lod):
    """Draw the paired green gate and its geometric grilles from the frontal entrance view."""
    width, top = 1.42, 2.24
    for side in (-1,1):
        u = side*(width/2+.087)
        f.box(u,top/2,.16,top,.29,-.048,PIGMENT,'Red door jambs')
    f.box(0,2.40,2.18,.34,.28,-.057,PIGMENT,'Red head over green door')
    # The frontal photograph shows a dark, continuous reveal below the red lintel.
    # Overlap the inner backstop with the masonry edges, so the thin frame casts
    # its own shadow when seen obliquely from under the entrance canopy.
    f.box(0,1.125,1.50,2.27,.044,-.30,GATE_BACK,'Vestibule behind gate')
    f.box(0,2.204,width+.020,.051,.098,-.177,GREEN,'Top frame of the green gate')
    for side in (-1,1):
        mid = side*width/4
        for edge in (-1,1):
            f.box(mid+edge*(width/4-.022),1.10,.044,2.20,.092,-.178,GREEN,'Gate leaf frames')
        for level in [.04,.79,1.0,2.15]:
            f.box(mid,level,width/2,.057,.085,-.179,GREEN,'Gate horizontal rails')
        for j in range(1,9):
            u = mid-width/4+j*width/18
            for low,high in [(.062,.77),(1.02,2.12)]:
                f.box(u,(low+high)/2,.025,high-low,.043,-.182,GREEN,'Gate vertical grilles')
        for h in [.82,.87,.92,.97]:
            f.box(mid,h,width/2-.04,.021,.056,-.182,GREEN,'Gate waist louvers')
    f.box(0,2.393,.56,.19,.026,.099,PLAQUE,'Number plate 1327')
    segments = {'a':((0,1),(1,1)),'b':((1,1),(1,.5)),'c':((1,.5),(1,0)),
                'd':((0,0),(1,0)),'e':((0,.5),(0,0)),'f':((0,1),(0,.5)),'g':((0,.5),(1,.5))}
    for i,(digit,strokes) in enumerate(zip('1327',['bc','abgcd','abged','abc'])):
        for key in strokes:
            a,c = segments[key]
            b.tube([f.point(-.173+i*.102+ux*.061,2.346+uz*.095,.119)for ux,uz in (a,c)],
                   .006,LETTER,4 if lod else 7,'Enamel plate/1327 numerals')
    for side in (-1,1):
        label = 'Left' if side<0 else 'Right'
        profile=[(.055,.183),(.11,.184),(2.15,.173),(2.46,.177)]
        for i in range(5):
            h=2.46+i*.038
            profile.extend([(h+.008,.180),(h+.016,.190),(h+.028,.190),(h+.035,.181)])
        profile.extend([(2.655,.191),(2.687,.205),(2.705,.205)])
        b.lathe((side*1.135,-.84),profile,COLUMN,16 if lod else 48,label+' round canopy column')
    f.box(0,.026,2.77,.052,1.43,.39,CAP,'Doorstep slab')
    f.box(0,2.812,3.54,.224,1.75,.435,STONE,'Flat entrance canopy')
    f.box(0,2.935,3.57,.034,1.78,.435,CAP,'Canopy drip edge')


def add_building(b, lod):
    f=Facade(b,(-4.04,0),(4.04,0),'North entrance')
    side_windows=[(z(bottom),z(top))for top,bottom in DIMS['side_windows_top_and_bottom_y']]
    tower_windows=sorted((z(bottom),z(top))for top,bottom in DIMS['tower_windows_top_and_bottom_y'])
    side_width=(450-375)*SCALE
    for side, edges in zip(('Left','Right'),DIMS['flank_glazing_x']):
        midpoint=(x(edges[0])+x(edges[1]))/2
        leaf=Facade(b,(midpoint-side_width/2,.21),(midpoint+side_width/2,.21),side+' flank')
        outer_width=2.48
        wall=Facade(b,(midpoint-outer_width/2,.18),(midpoint+outer_width/2,.18),side+' wall')
        holes=[rectangle(-side_width/2,low,side_width/2,high)for low,high in side_windows]
        vent=rectangle(-.17,.35,.17,.68)
        wall.wall(0,z(90),[*holes,vent],.38,STONE)
        wall.box(0,.515,.344,.336,.036,-.091,METAL,'Recessed base vent')
        for v in range(5):
            wall.box(0,.37+v*.063,.34,.024,.044,-.056,CAP,'Base vent louvers')
        for i,(low,high) in enumerate(side_windows):
            pane_grid(leaf,low,high,4,5,'Bay '+str(4-i),lod)
            wall.box(0,low-.034,side_width+.10,.068,.21,.020,CAP,'Window sills')
        for i,(above,below) in enumerate(zip(side_windows,side_windows[1:])):
            bottom,top=below[1]+.04,above[0]-.05
            n=round((top-bottom)/.083)
            for j in range(n):
                wall.box(0,bottom+(j+.5)*(top-bottom)/n,side_width-.015,(top-bottom)/n-.012,
                         .029,.020,CAP,'Scored cement spandrels')
        wall.box(0,z(90)-.038,outer_width+.04,.076,.51,-.09,CAP,'Flat parapet coping')
    tower_top=z(DIMS['tower_top_y'])
    inner=x(DIMS['tower_glazing_x'][1])
    for sign,tag in [(-1,'Left'),(1,'Right')]:
        outer=(DIMS['x_origin']-DIMS['tower_outer_x'][0])*SCALE if sign<0 else x(DIMS['tower_outer_x'][1])
        width=outer-inner
        f.box(sign*(inner+width/2),(tower_top+2.92)/2,width,tower_top-2.92,.60,.067,STONE,tag+' tall stair pier')
        f.box(sign*(outer-.054),(tower_top+2.93)/2,.109,tower_top-2.93,.093,.40,CAP,tag+' narrow outer arris')
        f.box(sign*(inner+width/2),tower_top+.025,width+.037,.05,.68,.072,CAP,tag+' pier coping')
        for h in (z(78),z(58),z(36)):
            f.box(sign*(outer+.066),h,.43,.07,.62,.061,CAP,tag+' crown return bands')
    span=x(547);tip_depth=.78
    faces=[Facade(b,(-span,-.12),(0,-tip_depth),'West stair facet'),
           Facade(b,(0,-tip_depth),(span,-.12),'East stair facet')]
    previous=2.952
    for i,(low,high) in enumerate(tower_windows):
        brick_band(b,previous,low-.028,LIGHT_BRICK if i==0 else BRICK,'Landing '+str(i+1),lod)
        for side in faces:
            pane_grid(side,low,high,2,5,'Landing '+str(i+1),lod,-.047)
        folded_strip(b,-STAIR_FACE-.003,STAIR_FACE+.003,-.076,.092,low-.036,low+.011,CAP,'Folded window sills')
        # The pressed steel meeting post closes the two glazing planes at their shared point.
        folded_strip(b,-.037,.037,-.073,.004,low+.009,high,FRAME,'Stair glazing/Mitred meeting post')
        previous=high+.02
    crown(b,previous,tower_top)
    # Put the wall behind the door back from the piers and preserve the actual open porch.
    f.wall(0,2.70,[rectangle(-.735,.018,.735,2.24)],.32,STONE,
           outline=rectangle(-1.55,0,1.55,2.70))
    gate(f,b,lod)
    assign_uvs(b)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,extra=parser.parse_known_args()
    os.environ['ELISABETH_STAIR_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
