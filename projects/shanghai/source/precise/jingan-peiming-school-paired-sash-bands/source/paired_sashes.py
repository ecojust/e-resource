"""Study of the two light window bands at Peiming Middle School, photographed by Antigng in 2018."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ID = 'jingan-peiming-school-paired-sash-bands'
WALL = 'Horizontally jointed grey render'
STONE = 'Light grey artificial stone'
EDGE = 'Bevelled edge of the stone surround'
PANEL = 'Inset rectangular panel'
WOOD = 'Dark brown casement'
UPPER = 'Pale sky in upper glass'
LOWER = 'Deep reflected glass below'
BAR = 'Fine glazing divisions'
EAVE = 'Dark gutter and sloping eaves edge'
SOFFIT = 'Pale grooved soffit'
PALETTE = {
    name:dict(color=colour, roughness=rough) for name,colour,rough in [
        (WALL,[1,1,1],.99),(STONE,[.70,.685,.626],.91),(EDGE,[.59,.57,.51],.93),
        (PANEL,[.66,.65,.59],.98),(WOOD,[.115,.071,.055],.71),
        (UPPER,[.55,.64,.68],.36),(LOWER,[.088,.146,.146],.39),
        (BAR,[.42,.43,.39],.62),(EAVE,[.15,.09,.08],.76),(SOFFIT,[.55,.55,.50],.94)]}

def texture():
    path=Path(__file__).with_name('grey-render.png')
    if not path.exists():
        rng=np.random.default_rng(619)
        field=rng.normal(0,3.2,(512,512,1))+np.array([158,156,149])[None,None,:]
        Image.fromarray(field.clip(0,255).astype('uint8')).quantize(96).save(path)
    PALETTE[WALL]['texture']=str(path)

CENTRES=(-.94,.94)
LIGHTS=((.22,1.69,LOWER),(2.92,4.47,UPPER))
def add_building(builder, far=False):
    texture()
    def locate(x,z,depth):
        return (x,-depth,z)
    def shape(poly,d0,d1,mat,label):
        builder.prism(poly,d0,d1,locate,mat,label)
    def block(x0,x1,z0,z1,d0,d1,mat,label):
        shape(box(x0,z0,x1,z1),d0,d1,mat,label)
    strips=unary_union([box(x-.55,-.01,x+.55,4.75) for x in CENTRES])
    # Recess each horizontal bed to give a narrow shadow at the face and around the corner.
    cutout=box(-1.86,-.17,1.86,4.75).difference(strips)
    shape(cutout,-.28,-.028,WALL,'Backing within the recessed horizontal joints')
    for row,z in enumerate(np.arange(-.18,4.76,.301)):
        top=min(z+.286,4.75)
        if top<=z:continue
        face=box(-1.86,max(z,-.17),1.86,top).difference(strips)
        shape(face,-.035,0,WALL,'Grey render between horizontal joints')
        left_return=[(-1.86,0),(-1.86,.58),(-1.83,.58),(-1.83,0)]
        builder.prism(Polygon(left_return),max(z,-.17),top,
                      lambda x,y,h:(x,y,h),WALL,'Return of the joint on the left corner')
    for x in CENTRES:
        window_openings=unary_union([box(x-.375,z0,x+.375,z1) for z0,z1,_ in LIGHTS])
        border=box(x-.55,-.17,x+.55,4.75).difference(window_openings)
        shape(border,-.248,.038,STONE,'Continuous pale band joining upper and lower windows')
        for hand in (-1,1):
            a=x+hand*.492
            block(a-.018,a+.018,-.17,4.72,.035,.067,EDGE,'Raised strip along outer surround')
            if not far:
                a=x+hand*.455
                block(a-.006,a+.006,-.17,4.72,.036,.055,STONE,'Narrow return along the border')
        for z0,z1,material in LIGHTS:
            block(x-.375,x+.375,z0,z1,-.235,-.216,WOOD,'Recessed timber casement frame')
            for hand in (-1,1):
                left,right=(x-.33,x-.036) if hand<0 else (x+.036,x+.33)
                block(left,right,z0+.056,z1-.055,-.218,-.203,material,'Paired lights in pale upper or dark lower glass')
                for fraction in (.35,.67):
                    z=z0+(z1-z0)*fraction
                    block(left,right,z-.0037,z+.0037,-.207,-.197,BAR,'Fine horizontal glazing division')
                inc=(left+right)*.5
                block(inc-.0037,inc+.0037,z0+.056,z1-.055,-.207,-.198,BAR,'Fine vertical glazing division')
            block(x-.021,x+.021,z0+.012,z1-.012,-.215,-.151,WOOD,'Timber meeting stile')
            block(x-.385,x+.385,z0-.040,z0+.008,.023,.067,EDGE,'Projecting stone sill')
        frame=box(x-.372,1.891,x+.372,2.765)
        inner=box(x-.322,1.944,x+.322,2.708)
        shape(frame.difference(inner),.035,.071,EDGE,'Rectangular raised margin at the floor between windows')
        shape(inner,.037,.051,PANEL,'Flat centre of the spandrel')
        for z in [1.828,1.853,2.794]:
            block(x-.386,x+.386,z-.009,z+.009,.036,.064,STONE,'Fine horizontal moulding across the band')
    block(-1.92,1.92,4.747,4.834,-.25,.215,SOFFIT,'Projecting soffit')
    for x in np.arange(-1.91,1.92,.046 if not far else .092):
        block(x,x+.006,4.742,4.75,.030,.211,EAVE,'Fine grooves across the soffit')
    block(-1.95,1.95,4.825,4.90,-.22,.233,EAVE,'Dark outer lip of the eave')
    for part in builder.parts:
        if part['material']==WALL:
            part['texcoords']=[[(x+1.87+.2*y)/3.97,(z+.18)/5.1] for x,y,z in part['vertices']]
