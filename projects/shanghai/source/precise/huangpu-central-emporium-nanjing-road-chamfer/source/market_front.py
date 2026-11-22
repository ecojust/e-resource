"""Central stone entrance and two short returns of the photographed Central Emporium."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from photo_plane import position
from corner_fanlight import fanlight_aperture, on_plane, steel_members
from material_names import MATERIAL

MEASUREMENTS=Path(__file__).resolve().parents[1]/'measurements'
TRIM='Pale grey limestone arrises'
REVEAL='Dark dressed stone returns'
FRAME='Dark shopfront metal'
BRONZE='Bronze entrance frame'
GLASS='Reflecting blue-grey upper glass'
SHOP='Dark shopfront glazing'
RECESS='Shadow beyond entrance'
PORPHYRY='Grey granite threshold'

def pigment(rgb,rough=.86,metal=0.):
    a=np.array(rgb)/255
    return dict(color=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={TRIM:pigment([174,166,154]),REVEAL:pigment([132,125,116]),FRAME:pigment([61,66,65],.53,.18),
          BRONZE:pigment([128,105,80],.50,.38),GLASS:pigment([111,133,142],.34,.09),
          SHOP:pigment([60,67,65],.41),RECESS:pigment([49,45,40]),PORPHYRY:pigment([151,139,125])}
HALF=3.18
def here(uv,depth=0):
    u,v=uv
    return position((u+.5)*7296/980-.5,(v+.5)*5472/735-.5,depth)[[0,2]]
def shape(points,depth=0):
    return Polygon([here(p,depth) for p in points])
def band(f,low,height,depth,mat,name,width=None):
    w=f.length if width is None else width
    outline=box(-w/2,low,w/2,low+height)
    if f.label=='Chamfer' and name.startswith('spring course'):
        # This projecting string course ends at the fanlight's lower steel.
        # A straight extrusion across the opening hides its photographed sill.
        front=on_plane(fan_screen(),position,-depth)
        rear=on_plane(fan_screen(),position,.018)
        outline=outline.difference(unary_union([front,rear]).convex_hull)
    f.prism(outline,-.018,depth,mat,name)
def mouldings(f):
    for label,levels in [
        ('shopfront cornice',[(3.24,.064,.075),(3.304,.045,.128),(3.349,.065,.103)]),
        ('spring course',[(4.51,.054,.088),(4.564,.04,.126),(4.604,.065,.181),(4.669,.038,.163)]),
        ('second-storey course',[(10.08,.082,.079),(10.162,.09,.135),(10.252,.095,.183),(10.347,.064,.27)]),
        ('upper entablature',[(12.97,.096,.080),(13.066,.092,.123),(13.158,.155,.175),(13.313,.059,.213),
                              (13.372,.109,.311),(13.481,.075,.355),(13.556,.114,.411),(13.670,.109,.469),(13.779,.12,.495),(13.899,.113,.52),(14.012,.162,.56),(14.174,.12,.59),(14.294,.069,.61)]),
        ('parapet rim',[(18.99,.13,.09),(19.12,.10,.145)])]:
        for j,(z,h,d) in enumerate(levels):
            band(f,z,h,d,TRIM if j%3 else REVEAL,label+f' {j+1}')
    for u in np.arange(-f.length/2+.085,f.length/2-.05,.214):
        f.prism(box(u-.037,13.448,u+.037,13.523),.163,.252,TRIM,'upper cornice dentils')
def window(f,outline,label,wide=False,ground=False):
    x0,z0,x1,z1=outline.bounds;w=x1-x0;h=z1-z0
    inner=outline.buffer(-(.045 if not ground else .071),join_style=2)
    positions=[.755] if not ground else [.76]
    if h>2.4 and not ground:positions.append(.22)
    bars=[box(x0,z0+h*t-.022,x1,z0+h*t+.022)for t in positions]
    if w>.68:
        strips=3 if wide else 2
        for i in range(1,strips):
            v=x0+w*i/strips;bars.append(box(v-.021,z0,v+.021,z1))
    grid=outline.buffer(.004,join_style=2).difference(inner.difference(unary_union(bars)))
    f.prism(outline.buffer(.015,join_style=2),-.275,-.252,SHOP if ground else GLASS,label+' glazing')
    f.prism(grid,-.248,-.188,BRONZE if ground else FRAME,label+' mullions and transoms')
    if not ground:
        f.prism(box(x0-.044,z0-.062,x1+.044,z0+.011),-.013,.077,TRIM,label+' sill')
def fan_screen():
    # The outline includes the photographed lower transom. Its ends extend
    # slightly beyond the traced arc where the metal seats on the masonry.
    return unary_union([fanlight_aperture(),*[g for _,g in steel_members()[1]]]).convex_hull

def central_front(builder,lod):
    f=Facade(builder,(-HALF,0),(HALF,0),'Chamfer')
    archive=json.loads((MEASUREMENTS/'2019-upper-frontage.json').read_text())
    windows=[Polygon(q['xz']) for q in archive['windows']]
    door=shape([(277,553),(500,555),(502,350),(279,354)],-.10)
    screen=fan_screen()
    front_open=on_plane(screen,position,0.)
    # The intrados splays into the stone on the oblique camera's sightlines.
    # Keep the street-edge footprint and the two plaster skins as measured.
    solid=box(-HALF,0.,HALF,19.22).difference(unary_union([*windows,door]))
    wall=solid.difference(front_open)
    edges=[0.,.021,.044,.068,.092,.15,.44]
    for i,(front,back) in enumerate(zip(edges,edges[1:])):
        near=on_plane(screen,position,front);far=on_plane(screen,position,back)
        hole=near.union(far).convex_hull
        f.prism(solid.difference(hole),-back,-front,MATERIAL,f'raked stone aperture layer {i+1}')
    for record,outline in zip(archive['windows'],windows):
        window(f,outline,record['floor']+f" window {record['column']}")
    # The photograph places the glass transom above the entrance leaves in a recessed opening.
    x0,z0,x1,z1=door.bounds;w=x1-x0
    # The two glazed panels occupy the left half in the 2022 street view.
    # The right-hand passage is open behind the front line. Its rear plane
    # represents interior shade; the photograph does not survey the shop.
    f.prism(door.buffer(.14,join_style=2),-.89,-.86,RECESS,'deep shade beyond the open right entrance')
    f.prism(door.buffer(.16,join_style=2).difference(door),-.89,-.43,REVEAL,'stone reveals from shop wall to interior')
    f.prism(box(x0-.15,.0,x1+.15,.075),-.89,.36,PORPHYRY,'shop threshold')
    header=shape([(280,406),(499,406),(500,354),(279,357)],.138)
    window(f,header,'doorway transom',wide=True,ground=True)
    bpt=here((280,417),.23);cpt=here((497,414),.23)
    threshold=.036;lintel=.5*(bpt[1]+cpt[1]);left=bpt[0];right=cpt[0]
    # The visible uprights lie at u approximately 280, 333, 387 on the
    # 980-pixel study. Hold the two panes behind their continuous frame.
    stile=here((387,416),.23)[0]
    for i in range(2):
        a=left+i*(stile-left)/2;c=left+(i+1)*(stile-left)/2
        leaf=box(a,threshold,c,lintel)
        f.prism(leaf,-.282,-.265,SHOP,'bronze shop door '+str(i+1)+' glass')
        f.prism(leaf.difference(leaf.buffer(-.064,join_style=2)),-.264,-.218,BRONZE,'bronze shop door '+str(i+1)+' stile')
        grip=a+.16 if i else c-.16
        f.prism(box(grip,.83,grip+.024,1.26),-.224,-.17,BRONZE,'door pull '+str(i+1))
    f.prism(box(left-.04,lintel-.044,right+.053,lintel+.071),-.39,-.17,BRONZE,'transom frame over left panels and open right passage')
    # The flat band is its own shallow face; gilt letters are built by corner_fanlight.
    tablet=shape([(281,349),(500,347),(502,282),(280,285)],-.116)
    f.prism(tablet,-.015,.116,MATERIAL,'stone sign fascia')
    for i,bounds in enumerate([[(179,551),(279,553),(279,351),(200,353)],
                               [(500,556),(604,559),(592,350),(500,351)]]):
        footprint=shape(bounds,-.10)
        f.prism(footprint,-.015,.10,MATERIAL,'entrance pier '+str(i+1))
    # The horizontal framing of the three first-floor windows is distinct from the arch below.
    group=unary_union(windows[:3]).bounds
    lx,lz,rx,rz=group
    for j,(z,d,t) in enumerate([(lz-.06,.045,.059),(lz-.22,.061,.074),(lz-.61,.048,.052),(rz+.037,.09,.065)]):
        f.prism(box(lx-.18,z,rx+.18,z+t),.0,d,TRIM,'first-window stone frame '+str(j+1))
    for side,x in enumerate((lx-.22,rx+.22)):
        f.prism(box(x-.043,lz-.61,x+.043,rz+.09),.0,.06,TRIM,'first window border '+str(side+1))
    for j,cx in enumerate((-2.51,2.51)):
        cz=9.83
        f.prism(box(cx-.243,cz-.247,cx+.243,cz+.247),0,.074,TRIM,'first-storey square badge '+str(j+1))
        theta=np.linspace(0,2*np.pi,27 if lod else 49)[:-1]
        oval=Polygon([(cx+.18*np.cos(t),cz+.182*np.sin(t))for t in theta])
        f.prism(oval.difference(oval.buffer(-.043)),.071,.104,REVEAL,'round return on stone badge '+str(j+1))
    mouldings(f)
    return wall

def side_returns(builder):
    # Included width is limited to one flanking window module. Each steps back
    # into the short adjoining wing visible in the 2019 and 2022 photographs.
    left=(-5.27,1.23);right=(5.32,1.28)
    for label,a,b in [('left',left,(-HALF,0)),('right',(HALF,0),right)]:
        f=Facade(builder,a,b,'Return '+label);span=f.length
        ranges=[(.0,3.25,span-.69),(4.86,7.27,.73),(8.12,9.59,.76),(11.05,12.58,.76),(15.01,17.62,.82)]
        holes=[box(-width/2,z0,width/2,z1)for z0,z1,width in ranges]
        f.wall(.0,19.22,holes,.42,MATERIAL)
        for j,hole in enumerate(holes):window(f,hole,'side bay '+str(j+1),ground=(j==0))
        for z,h in [(7.48,.41),(9.83,.20)]:
            plaque=box(-.35,z,.35,z+h)
            f.prism(plaque.difference(plaque.buffer(-.031,join_style=2)),0,.04,TRIM,'recessed side stone panel')
        mouldings(f)
    # Close the slight mitre void from the two adjoining wall solids.
    for x in (-HALF,HALF):
        builder.box([x,.192,9.61],[.048,.369,19.22],MATERIAL,label='Concealed stone corner closure')

def add_front(builder,lod):
    central_front(builder,lod)
    side_returns(builder)
