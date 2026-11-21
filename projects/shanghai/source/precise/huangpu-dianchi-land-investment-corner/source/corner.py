"""Build the photographed cut corner and one bay of each adjoining street wall."""
import json
from pathlib import Path

from shapely.geometry import LineString, Polygon, box
from photo_architecture import Facade, opening
from brickwork import texture_uv

REGISTER = Path(__file__).with_name('frontage-registration.json')
EDGES = json.loads(REGISTER.read_text())['visible_edges_local_m']
BRICK = 'rose-red face brick'
RED = 'darker moulded brick'
STONE = 'carved pale stone'
GLASS = 'smoky street glazing'
WOOD = 'painted timber'
IRON = 'balcony iron'
SHOP = 'shopfront tile'
ROOF = 'dark roof flashing'
PALETTE = {
    name: {'color': color, 'roughness': roughness}
    for name, color, roughness in [
        (BRICK, [1., 1., 1.], .88), (RED, [.48, .205, .17], .88),
        (STONE, [.76, .72, .67], .83), (GLASS, [.19, .25, .255], .30),
        (WOOD, [.32, .226, .194], .72), (IRON, [.16, .17, .16], .64),
        (SHOP, [.81, .80, .76], .72), (ROOF, [.28, .24, .22], .89),
    ]
}
PALETTE[BRICK]['texture']=str(Path(__file__).with_name('red-brick.png'))
BALCONY = 3.44
EAVE = 13.91


def strip(face, x, z, width, height, material, projection=.08, thickness=.19, label='moulding'):
    face.box(x, z, width, height, thickness, projection, material, label)


def glazed(face, x, base, width, height, arch, distant, label):
    cut = opening(x, base, width, height, arch, 9 if distant else 20)
    face.window(cut, columns=2, rows=2 if distant else 3, frame=WOOD,
                trim=False, glass=GLASS, label=label)
    return cut


def keyblock(face, x, z, scale):
    cap = Polygon([(x-.16*scale,z+.17*scale),(x+.16*scale,z+.17*scale),
                   (x+.095*scale,z-.16*scale),(x-.095*scale,z-.16*scale)])
    face.prism(cap, .025, .16, STONE, 'tapered pale keystone')


def balcony(face, distant):
    width = face.length
    strip(face, 0, BALCONY, width+.012, .22, STONE, .24, .86, 'continuous balcony plate')
    for z in (BALCONY+.18, BALCONY+.84):
        strip(face, 0, z, width, .052, IRON, .60, .055, 'balcony horizontal iron')
    count = max(5, round(width/(.27 if distant else .16)))
    for n in range(count):
        x = (n+.5)*width/count-width/2
        strip(face, x, BALCONY+.50, .029, .66, IRON, .60, .03, 'iron upright')


def shopfront(face, distant):
    """The model retains the shopfront openings and their unlettered fascia."""
    width = face.length
    door = glazed(face, 0, .06, width-.44, 2.38, 0, distant, 'shop glazing')
    face.wall(0, BALCONY-.11, [door], .37, SHOP)
    strip(face, 0, 2.78, width, .52, SHOP, .058, .20, 'fascia above the street windows')
    for x in (-width/2+.10, width/2-.10):
        strip(face, x, 1.57, .18, 3.14, STONE, .075, .22, 'shop pier')


def flat_corner(face, distant):
    holes = []
    for i, (z,h) in enumerate([(3.77,2.83),(7.18,2.63),(10.48,2.73)]):
        width = 1.99 if i < 2 else 1.86
        holes.append(glazed(face, 0, z, width, h, 0, distant, 'corner French window'))
        strip(face, 0, z+h+.10, width+.58, .17, STONE, .105, .29, 'flat window head')
        keyblock(face, 0, z+h+.10, 1.06)
        if i:
            strip(face, 0, z+.52, width, .055, IRON, .125, .065, 'safety rail')
            if not distant:
                for k in range(8):
                    strip(face, (k-3.5)*width/8, z+.27, .021, .50, IRON, .125, .04)
    holes.append(glazed(face, 0, 14.48, 1.62, 1.20, 0, distant, 'attic casement'))
    face.wall(BALCONY+.10, 16.24, holes, .42, BRICK)
    strip(face, 0, 15.81, 2.06, .16, RED, .105, .25, 'attic window head')
    strip(face, 0, 16.27, face.length+.12, .19, STONE, .07, .27, 'level parapet cap')
    for x in (-face.length/2+.23, face.length/2-.23):
        strip(face, x, 8.74, .30, 10.24, RED, .045, .15, 'corner edge pier')
        for z in (6.86,10.16,13.52):
            strip(face, x, z, .44, .15, STONE, .105, .24, 'pier string return')


def side_bay(face, distant):
    holes = []
    for base, height, rise in ((3.91,2.80,.42),(7.16,2.90,.10),(10.53,2.77,0)):
        for x in (-.87,.87):
            holes.append(glazed(face,x,base,1.31,height,rise,distant,'paired tall street sash'))
            if base < 5:
                band = holes[-1].buffer(.13).difference(holes[-1])
                band = band.intersection(box(x-1,base+height-.53,x+1,base+height+.30))
                face.prism(band,.015,.13,STONE,'paired balcony arch')
        if base > 6:
            for x in (-1.68,0,1.68):
                strip(face,x,base+height/2,.26,height+.22,STONE,.06,.22,'pale jamb and centre mullion')
            strip(face,0,base+height+.12,3.74,.22,STONE,.10,.28,'paired window lintel')
        if 7 < base < 8:
            crest = Polygon([(-1.64,base+height+.19),(-.90,base+height+.29),
                             (-.48,base+height+.55),(0,base+height+.72),
                             (.48,base+height+.55),(.90,base+height+.29),(1.64,base+height+.19)])
            face.prism(crest,.06,.23,STONE,'curved pediment above the middle-floor pair')
    face.wall(BALCONY+.1,EAVE,holes,.42,BRICK)
    for x in (-face.length/2+.17,face.length/2-.17):
        strip(face,x,8.63,.28,10.08,RED,.058,.17,'brick pier to cornice')
    width=face.length/2
    outline=Polygon([(-width,EAVE-.01),(width,EAVE-.01),(width,14.52),
                     (1.88,14.52),(1.66,15.64),(.23,16.78),(0,16.90),
                     (-.23,16.78),(-1.66,15.64),(-1.88,14.52),(-width,14.52)])
    arch=glazed(face,0,14.08,2.39,1.91,.88,distant,'arched attic opening in the gable')
    face.wall(EAVE-.01,16.90,[arch],.37,BRICK,outline=outline)
    voussoirs=arch.buffer(.16).difference(arch).intersection(box(-1.5,15.08,1.5,16.25))
    face.prism(voussoirs,.018,.155,RED,'attic arch ring')
    for sign in (-1,1):
        a=face.point(sign*1.70,15.64,.07)
        b=face.point(sign*.17,16.81,.07)
        face.builder.tube([a,b],.102,STONE,6 if distant else 10,'gable coping')
    strip(face,0,16.86,.45,.18,RED,.06,.22,'gable apex cap')


def add_building(builder, distant):
    for i, (a,b) in enumerate(zip(EDGES, EDGES[1:])):
        face=Facade(builder,a,b,['Sichuan wall','corner','Dianchi wall'][i])
        shopfront(face,distant)
        balcony(face,distant)
        if i==1:
            flat_corner(face,distant)
        else:
            side_bay(face,distant)
        for z,height,depth in [(6.94,.17,.26),(10.19,.12,.19),(13.70,.22,.38),(13.95,.16,.46)]:
            face.beam(z,height,depth,STONE,label='continuous horizontal stone course')
        if not distant:
            count=round(face.length/.31)
            for n in range(count):
                strip(face,(n+.5)*face.length/count-face.length/2,13.54,.105,.115,
                      STONE,.15,.18,'cornice dentil')
    for part in builder.parts:
        if part['material']==BRICK:
            uv=[texture_uv(*v) for v in part['vertices']]
            part['texcoords']=[(u,1-v) for u,v in uv]
    line=LineString(EDGES)
    roof=line.buffer(1.95,single_sided=True,join_style='mitre',cap_style='flat')
    builder.plan_prism(roof,13.82,13.99,ROOF,'visible shallow roof behind parapet')
