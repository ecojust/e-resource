"""South front of the documented No. 12 dwelling inside Lane 820, Julu Road."""
from math import cos,pi,sin
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import box,Polygon
from shapely.ops import unary_union

from photo_architecture import Facade
from sign_lettering import lettering_shapes

WALL='grooved buff render'
CREAM='ivory rendered trim'
DARK='grey cement base'
SEAM='fine stucco joint'
WOOD='dark brown timber'
PANEL='raised door panel'
SASH='deep green painted steel'
GLASS='smoke blue glass'
LIGHTGLASS='pale curtains behind glass'
IRON='dark lamp iron'
BRASS='weathered brass'
SIGN='green enamel'
LETTER='ivory enamel'
SOIL='planter earth'
PALETTE={
  WALL:{'color':[.666,.590,.480],'roughness':.89}, CREAM:{'color':[.815,.803,.722],'roughness':.82},
  DARK:{'color':[.397,.404,.386],'roughness':.92}, SEAM:{'color':[.516,.459,.382],'roughness':.91},
  WOOD:{'color':[.185,.113,.083],'roughness':.58}, PANEL:{'color':[.225,.148,.110],'roughness':.61},
  SASH:{'color':[.104,.205,.178],'roughness':.58}, GLASS:{'color':[.173,.220,.234],'roughness':.35,'metallic':.18},
  LIGHTGLASS:{'color':[.428,.478,.448],'roughness':.47,'metallic':.11},
  IRON:{'color':[.272,.280,.254],'roughness':.66,'metallic':.24},
  BRASS:{'color':[.529,.521,.427],'roughness':.43,'metallic':.52},
  SIGN:{'color':[.115,.362,.274],'roughness':.49},LETTER:{'color':[.864,.855,.737],'roughness':.55},
  SOIL:{'color':[.180,.159,.131],'roughness':.99}}
WIDTH=5.78
HALF=WIDTH/2
DOOR=-1.77
DOOR_WIDTH=1.045
FONT=Path(__file__).parent/'fonts/JinghuaAddress.otf'

def ring(p,inset):
    return p.difference(p.buffer(-inset,join_style=2))

def window(f,cx,bottom,width,height,columns,transoms,projection=.0,glazing=GLASS):
    pane=box(cx-width/2,bottom,cx+width/2,bottom+height)
    f.prism(pane.buffer(.009,join_style=2),projection-.181,projection-.158,glazing,'window glazing')
    left=cx-width/2;cuts=[]
    for i in range(1,columns):
        u=left+i*width/columns
        cuts.append(box(u-.025,bottom,u+.025,bottom+height))
    for frac in transoms:
        z=bottom+height*frac; cuts.append(box(left,z-.027,left+width,z+.027))
    inner=pane.buffer(-.046,join_style=2)
    f.prism(pane.difference(inner.difference(unary_union(cuts))),projection-.109,projection-.051,SASH,'painted casements')
    trim=pane.buffer(.114,join_style=2).difference(pane)
    f.prism(trim,projection-.063,projection+.031,CREAM,'rendered window band')
    f.box(cx,bottom-.065,width+.28,.10,.228,projection+.010,CREAM,'projecting window sill')

def text(f,label,cx,z,width,height):
    for ch,g in lettering_shapes(label,width,height,font=FONT):
        f.prism(translate(g,xoff=cx,yoff=z),.043,.050,LETTER,'address plate lettering')

def lantern(b,f,u):
    z=2.59
    f.box(u,z,.046,.238,.053,.111,IRON,'lantern backplate')
    b.tube([f.point(u,z+.07,.110),f.point(u,z+.03,.198)],.015,IRON,8,'lantern brackets')
    x,y,_=f.point(u,z,.208)
    b.lathe([x,y],[(z-.142,.013),(z-.105,.050),(z+.04,.073),(z+.13,.016)],LIGHTGLASS,6,'paired porch lantern glass')
    for ang in [i*pi/3 for i in range(6)]:
        b.tube([(x+.049*cos(ang),y+.049*sin(ang),z-.105),
                (x+.073*cos(ang),y+.073*sin(ang),z+.042)],.0055,IRON,5,'porch lantern ribs')
    b.lathe([x,y],[(z+.035,.085),(z+.045,.085),(z+.110,.025),(z+.140,.003)],IRON,6,'lantern pointed caps')

def add_front(b,lod=False):
    f=Facade(b,(-HALF,0),(HALF,0),'South face')
    door=box(DOOR-DOOR_WIDTH/2,0,DOOR+DOOR_WIDTH/2,2.89)
    floor_window=box(-.72,.74,2.43,2.96)
    middle=box(-1.91,4.12,1.91,6.18)
    top=box(-1.91,7.64,1.91,8.99)
    shapes=unary_union([door,floor_window,middle,top])
    elevation=box(-HALF,0,HALF,9.70).difference(shapes)
    f.prism(elevation,-.91,0,WALL,'cutaway front wall')
    plinth=elevation.intersection(box(-HALF,0,HALF,.76))
    f.prism(plinth,.001,.028,DARK,'cement plinth')
    if not lod:
        for i in range(45):
            z=.87+i*.199
            band=elevation.intersection(box(-HALF+.04,z-.0043,HALF-.04,z+.0043))
            f.prism(band,.002,.006,SEAM,'horizontal render lines')
    for x in (-HALF+.071,HALF-.071):
        f.box(x,5.19,.142,9.03,.588,.069,WALL,'party-wall blade')
        f.box(x,9.637,.15,.14,.615,.071,CREAM,'blade weather cap')
    f.box(0,9.560,WIDTH-.21,.150,.635,.145,CREAM,'deep roof eave')
    f.box(0,9.672,WIDTH-.20,.073,.631,.145,WALL,'eave top')
    for win in [(0,4.12,3.82,2.06,5,[.25,.50,.75]),(0,7.64,3.82,1.35,5,[.34,.68])]:
        window(f,*win)
    window(f,.855,.74,3.15,2.22,4,[.72],glazing=LIGHTGLASS)
    # The central second-floor window occupies most of the bay. Its separate flat hood is seen in the row photograph.
    f.box(0,6.49,4.12,.185,.618,.155,WALL,'upper casement canopy')
    f.box(0,6.36,4.16,.063,.642,.158,CREAM,'upper canopy edge')
    f.box(0,3.275,WIDTH-.27,.144,.637,.148,CREAM,'ground floor canopy')
    f.box(0,3.375,WIDTH-.27,.081,.633,.147,WALL,'ground canopy fascia')
    # Barred transom and deeply recessed timber door, with separate door jambs.
    outer=box(DOOR-DOOR_WIDTH/2-.122,0,DOOR+DOOR_WIDTH/2+.122,3.055)
    f.prism(outer.difference(door),-.037,.068,CREAM,'squared doorway surround')
    leaf=box(DOOR-DOOR_WIDTH/2+.028,.01,DOOR+DOOR_WIDTH/2-.028,2.094)
    f.prism(leaf,-.355,-.279,WOOD,'timber door leaf')
    f.prism(door.difference(box(DOOR-.47,.00,DOOR+.47,2.096)).difference(box(DOOR-.47,2.184,DOOR+.47,2.814)),-.335,-.204,WOOD,'timber door jambs')
    for col in range(3):
        x=DOOR-.332+col*.332
        for z,h in [( .62,.81),(1.59,.64)]:
            rect=box(x-.122,z-h/2,x+.122,z+h/2)
            f.prism(ring(rect,.022),-.281,-.258,PANEL,'recessed door panels')
    transom=box(DOOR-.475,2.176,DOOR+.475,2.824);f.prism(transom,-.327,-.298,GLASS,'dark glazed transom')
    for z in (2.32,2.49,2.66):
        f.box(DOOR,z,.95,.020,.029,-.222,WOOD,'horizontal transom guards')
    if not lod:
        f.box(DOOR+.382,1.025,.046,.191,.019,-.246,BRASS,'door lockplate')
        f.box(DOOR+.331,1.057,.123,.026,.056,-.210,BRASS,'door lever')
    for x in (DOOR-.646,DOOR+.646):lantern(b,f,x)
    # Address material and raised lettering are confined to the photographed plate.
    cx=-.947
    f.box(cx,1.934,.278,.187,.035,.020,SIGN,'green civic number')
    text(f,'12',cx,1.927,.130,.095)
    if not lod:text(f,'巨鹿路八二〇弄',cx,1.861,.224,.029)
    # The window planter is described in the June 2026 visit; its moulding and dimensions are estimates.
    rim=box(-.71,-.61,2.42,-.07)
    b.plan_prism(rim,0,.245,DARK,'flower box base')
    b.plan_prism(ring(rim,.066),.244,.325,DARK,'planter rim')
    b.plan_prism(rim.buffer(-.064,join_style=2),.244,.268,SOIL,'planter earth')
    f.box(DOOR,.035,1.19,.070,.305,.072,DARK,'door threshold')
