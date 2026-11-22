"""Street entrance of Huqiu Apartments, drawn from the photographed east front.

Positive x is north, the pavement is at negative y and the ground is z = 0.
The builder supplies an 8.16 × 4.73 m opening. Dimensions and profile depths were
estimated from the front and street views; the dark portion behind the open
leaf stops at the back of the study. All geometry, including the four sign
characters, is procedural.
"""
import math

from shapely import affinity, set_precision
from shapely.geometry import LineString, Polygon, box as rect
from shapely.ops import unary_union

from photo_architecture import Facade


STONE = 'Huqiu warm doorway stone'
MOULDING = 'Huqiu pale worn stone mouldings'
SIGN_STONE = 'Huqiu recessed inscription stone'
LETTERS = 'Huqiu burnished inscription'
WOOD = 'Huqiu dark umber joinery'
GLASS = 'Huqiu smoky blue entrance glass'
AMBER = 'Huqiu brown upper side light'
VOID = 'Huqiu unlit door reveal'
METAL = 'Huqiu dark bronze hardware'
PAVING = 'Huqiu grey threshold'
ENAMEL = 'Huqiu green street number enamel'
DIGITS = 'Huqiu ivory street number strokes'

PORTAL_MATERIALS = {
    STONE: {'color': [.55,.50,.40], 'roughness': .86},
    MOULDING: {'color': [.68,.63,.52], 'roughness': .80},
    SIGN_STONE: {'color': [.444,.423,.318], 'roughness': .87},
    LETTERS: {'color': [.70,.56,.28], 'roughness': .46, 'metallic': .53},
    WOOD: {'color': [.145,.073,.056], 'roughness': .54},
    GLASS: {'color': [.115,.184,.199], 'roughness': .29, 'metallic': .19},
    AMBER: {'color': [.27,.128,.062], 'roughness': .59},
    VOID: {'color': [.040,.036,.032], 'roughness': .97},
    METAL: {'color': [.32,.25,.157], 'roughness': .44, 'metallic': .64},
    PAVING: {'color': [.406,.400,.366], 'roughness': .91},
    ENAMEL: {'color': [.024,.24,.145], 'roughness': .48},
    DIGITS: {'color': [.86,.89,.75], 'roughness': .54},
}


def block(face, x, bottom, w, h, rear, front, material, label):
    """A horizontal bed; positive depths project towards the street."""
    face.box(x, bottom+h/2, w, h, front-rear, (rear+front)/2, material, label)


def pierced_joinery(face, x, bottom, width, height, columns, rows,
                    rear, front, name, glass=GLASS):
    """One perimeter and set of rails, with recessed individual panes."""
    outer=rect(x-width/2,bottom,x+width/2,bottom+height)
    side=.060 if width>.65 else .043
    head=.069 if height>1.1 else .044
    aperture=rect(x-width/2+side,bottom+head,x+width/2-side,bottom+height-head)
    minx,minz,maxx,maxz=aperture.bounds
    rails=[]
    for i in range(1,columns):
        a=minx+(maxx-minx)*i/columns
        rails.append(rect(a-.013,minz,a+.013,maxz))
    for i in range(1,rows):
        z=minz+(maxz-minz)*i/rows
        rails.append(rect(minx,z-.015,maxx,z+.015))
    panes=aperture.difference(unary_union(rails)) if rails else aperture
    face.prism(outer.difference(panes),rear,front,WOOD,name+' frame and rails')
    face.prism(panes,rear-.024,rear+.004,glass,name+' recessed panes')


def side_windows(face):
    for side,x in [('south',-2.97),('north',2.97)]:
        label=side+' side window '
        pocket=rect(x-.428,.682,x+.428,2.855)
        visible=rect(x-.401,.708,x+.401,2.817)
        face.prism(pocket.difference(visible),-.211,-.119,WOOD,label+'reveal trim')
        jamb=rect(x-.493,.635,x+.493,2.894).difference(rect(x-.425,.685,x+.425,2.852))
        face.prism(jamb,-.020,.018,MOULDING,label+'narrow stone surround')
        block(face,x,.586,.97,.102,-.092,.087,MOULDING,label+'projecting sill')
        pierced_joinery(face,x,.702,.815,1.46,2,3,-.196,-.111,label+'lower sash')
        block(face,x,2.166,.818,.075,-.198,-.085,WOOD,label+'transom')
        # In the 2022 street photograph the southern top panel reads brown.
        pierced_joinery(face,x,2.245,.815,.580,1,1,-.19,-.113,label+'top light',
                        AMBER if x<0 else GLASS)


def column(builder, face, x, distant):
    name=('south' if x<0 else 'north')+' portal column '
    depth=-.209
    block(face,x,.013,.78,.090,-.139,.557,PAVING,name+'square foot')
    profile=[(.104,.280),(.105,.337),(.130,.350),(.151,.354),(.177,.327),
             (.187,.299),(.223,.291),(.255,.306),(.376,.306),
             (2.87,.251),(2.948,.253),(2.973,.279),(3.009,.283),
             (3.029,.270),(3.073,.278),(3.105,.316),(3.151,.325),
             (3.159,.343),(3.203,.343)]
    if distant:
        profile=[profile[i] for i in (0,1,3,5,7,8,9,11,14,16,17,18)]
    builder.lathe((x,depth),profile,MOULDING,18 if distant else 36,name+'tapered round shaft')
    for bottom,w,h,back,front in [
        (3.204,.69,.065,-.126,.543), (3.270,.735,.060,-.12,.565),
        (3.332,.69,.065,-.112,.541), (3.398,.62,.080,-.108,.505),
        (3.478,.58,.340,-.084,.489), (3.818,.66,.067,-.102,.526),
        (3.885,.75,.072,-.130,.560)]:
        block(face,x,bottom,w,h,back,front,MOULDING,name+'capital bedding')
    if not distant:
        # Shallow slots under the square abacus appear above, not along, the shaft.
        for dx in [-.201,-.131,-.065,.066,.132,.202]:
            block(face,x+dx,3.509,.018,.263,.489,.497,STONE,name+'capital neck bead')
        for dx in [-.20,-.10,0,.10,.20]:
            block(face,x+dx,3.320,.065,.037,.531,.548,STONE,name+'short neck dentil')


# Hand-drawn stroke centre lines for 虎丘公寓, to be read from south to north.
# In the photographed sign the slightly oblique ends and central negative
# spaces remain visible. Coordinates here are a glyph grid with y down.
GLYPHS = {
    '虎': [
      [(48,10),(47,20)],[(47,15),(72,11)],[(25,26),(46,23),(83,22),(75,34)],
      [(27,25),(25,50),(18,69),(8,83)],[(35,44),(54,37),(70,34)],
      [(49,29),(46,47),(51,52),(62,51),(70,48)],
      [(39,58),(47,56),(46,66),(41,77),(30,87)],
      [(52,58),(69,54),(66,68),(66,78),(71,83),(83,83),(91,78)]],
    '丘': [
      [(75,12),(60,17),(45,22),(28,29)],[(30,27),(30,48),(31,70)],
      [(31,43),(49,40),(75,37)],[(59,41),(61,48),(57,67)],
      [(11,77),(27,75),(50,72),(72,71),(89,73)]],
    '公': [
      [(44,13),(37,24),(26,38),(13,48)],[(57,14),(66,22),(77,30),(91,32)],
      [(49,39),(42,52),(30,62),(25,67),(32,70),(49,68),(70,64)],
      [(59,56),(69,62),(78,71),(81,80)]],
    '寓': [
      [(47,8),(55,16)],[(22,20),(20,29)],[(23,23),(48,20),(82,19),(77,29)],
      [(33,34),(32,56)],[(33,33),(49,31),(69,31),(67,55)],[(36,43),(62,40)],
      [(34,54),(64,51)],[(49,34),(49,66),(48,76)],
      [(22,60),(23,71),(22,86)],[(23,60),(46,58),(76,55),(77,72),(76,86),(65,82)],
      [(34,75),(45,73),(59,70)],[(56,64),(63,72),(66,76)]]
}


def glyph_outline(paths):
    # Slightly wider middle segments echo the raised, brush-like lettering.
    pieces=[]
    for path in paths:
        for j,(a,b) in enumerate(zip(path,path[1:])):
            length=math.hypot(b[0]-a[0],b[1]-a[1])
            dx,dy=(b[0]-a[0])/length,(b[1]-a[1])/length
            perpendicular=(-dy,dx)
            w0=1.45 if j==0 else 3.05
            w1=1.21 if j==len(path)-2 else 3.20
            mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
            def edge(w,point,d):
                return (point[0]+d*w*perpendicular[0],point[1]+d*w*perpendicular[1])
            pieces.append(Polygon([edge(w0,a,1),edge(3.46,mid,1),edge(w1,b,1),
                                   edge(w1,b,-1),edge(3.46,mid,-1),edge(w0,a,-1)]))
        pieces.append(LineString(path).buffer(.9,resolution=2))
    return set_precision(unary_union(pieces),.002)


def inscription(face, distant):
    block(face,0,2.958,3.59,.511,.135,.227,SIGN_STONE,'stone beneath the four-character name')
    for bottom,h,d in [(2.916,.045,.274),(2.961,.036,.264),
                        (3.474,.037,.279),(3.512,.035,.290)]:
        block(face,0,bottom,3.80,h,.083,d,MOULDING,'letter panel margin')
    for i,letter in enumerate('虎丘公寓'):
        x=(i-1.5)*.737
        shape=affinity.affine_transform(glyph_outline(GLYPHS[letter]),
                                        [.0036,0,0,-.00276,x-.18,3.345])
        if distant:
            shape=shape.simplify(.0015,preserve_topology=True)
        if not distant:
            face.prism(shape.buffer(.0045,resolution=2),.2274,.241,METAL,'dark edge of '+letter)
        face.prism(shape,.2274 if distant else .2405,.247 if distant else .251,LETTERS,'raised '+letter)


def cornice(face, distant):
    # The side lintels stop against the centre portico; the main cap projects
    # farther than the quieter side stretches seen in the full street view.
    for x in (-3.39,3.39):
        for bottom,w,h,rear,front in [
            (2.895,1.36,.062,-.135,.069),
            (3.487,1.35,.040,-.121,.094),(3.552,1.37,.055,-.160,.105)]:
            block(face,x,bottom,w,h,rear,front,MOULDING,'side lintel string')
    for bottom,w,h,rear,front in [
        (3.540,4.62,.11,-.108,.258),(3.650,4.65,.272,-.110,.270),
        (3.923,4.85,.084,-.125,.386),(4.009,5.08,.076,-.145,.451),
        (4.087,5.24,.084,-.160,.511),(4.172,5.38,.088,-.181,.561),
        (4.262,5.51,.073,-.193,.598)]:
        block(face,0,bottom,w,h,rear,front,MOULDING if h<.10 else STONE,'stepped portal cornice')
    block(face,0,4.337,.52,.363,-.052,.217,MOULDING,'central plain crest')
    block(face,0,4.366,.407,.309,.218,.239,SIGN_STONE,'inset face of crest')
    # Only the short curved ramp returning into the square centre is evident.
    for sign in (-1,1):
        points=[(sign*.258,4.338),(sign*.258,4.553),(sign*.321,4.524),
                (sign*.366,4.427),(sign*.438,4.383),(sign*.594,4.366),
                (sign*.784,4.343),(sign*.806,4.337)]
        face.prism(Polygon(points),.010,.177,STONE,'curved side of crest')
    if not distant:
        for x in (-3.86,3.86):
            block(face,x,.047,.264,3.72,-.080,.095,STONE,'outer side pilaster')
            block(face,x,2.985,.311,.098,-.080,.136,MOULDING,'outer side capital')


def door_joinery(builder, face, distant):
    # A narrow dark backing shades the photographed open bay while leaving the
    # front woodwork freestanding. No room plan is inferred from this entrance.
    block(face,0,.027,3.01,2.819,-.445,-.430,VOID,'shadow behind open doorway')
    block(face,0,0,3.12,.046,-.444,.291,PAVING,'low centre threshold')
    for x in (-1.491,1.491):
        block(face,x,.041,.093,2.823,-.26,-.139,WOOD,'side jamb')
    for x in (-.989,0,.989):
        pierced_joinery(face,x,1.890,.980,.883,3,2,-.228,-.158,'upper transom')
    block(face,0,1.796,2.986,.09,-.254,-.126,WOOD,'transom rail over doors')
    for x in (-1.058,1.058):
        pierced_joinery(face,x,.044,.807,1.739,2,3,-.229,-.156,'fixed side light')
    # The right central leaf stands ajar in the 2022 doorway photograph. The
    # lower handle and glazing are attached to that leaf's own angled plane.
    hinge=(.652,.166)
    angle=math.radians(28)
    leaf_width=.759
    inner=(hinge[0]-leaf_width*math.cos(angle),hinge[1]-leaf_width*math.sin(angle))
    leaf=Facade(builder,inner,hinge,'131 open leaf')
    pierced_joinery(leaf,0,.049,leaf_width,1.720,1,3,-.030,.028,'open leaf and three panes')
    block(leaf,0,.050,leaf_width,.139,-.030,.030,WOOD,'deep kick rail')
    for x in (-.64,.646):
        block(face,x,.049,.045,1.744,-.225,-.150,WOOD,'mullion beside central doors')
    block(face,-.974,1.813,.285,.124,-.134,-.105,ENAMEL,'green 131 street plate')
    one=[[(.1,.72),(.45,.91),(.45,.1)],[(.18,.1),(.74,.1)]]
    three=[[(.1,.81),(.3,.91),(.69,.91),(.83,.77),(.80,.66),(.52,.51),
            (.78,.46),(.87,.32),(.76,.15),(.51,.08),(.2,.10),(.07,.20)]]
    for i,paths in enumerate([one,three,one]):
        for line in paths:
            sign=[(-1.047+i*.064+.047*x,1.83+.078*z) for x,z in line]
            face.prism(LineString(sign).buffer(.0045,resolution=2),-.105,-.100,DIGITS,
                       'street number 131 stroke')
    if not distant:
        block(leaf,-.287,.82,.032,.201,.027,.053,METAL,'pull plate')
        leaf.line((-.287,.865,.076),(-.287,.968,.076),.012,METAL,8,'upright pull')
        for z in (.865,.968):
            leaf.line((-.287,z,.047),(-.287,z,.078),.011,METAL,8,'pull standoff')


def add_entrance(builder, lod):
    """Fill the reserved 8.16-m street opening in the supplied local frame."""
    first_part=len(builder.parts)
    face=Facade(builder,(-4.08,0),(4.08,0),'131 door')
    openings=[rect(-1.536,0,1.536,2.871)]
    openings.extend(rect(x-.425,.685,x+.425,2.852) for x in (-2.97,2.97))
    skin=rect(-4.08,0,4.08,4.09).difference(unary_union(openings))
    face.prism(skin,-.419,-.004,STONE,'recessed stone body with three openings')
    side_windows(face)
    door_joinery(builder,face,lod)
    for x in (-2.045,2.045):
        column(builder,face,x,lod)
    inscription(face,lod)
    cornice(face,lod)
    # Capitals, muntins and glyph islands are independently selectable in
    # Blender, whose object names have a 63-byte limit.
    ordinal={}
    for part in builder.parts[first_part:]:
        label=part['label']
        number=ordinal.get(label,0)+1
        ordinal[label]=number
        if number>1:
            part['label']=f'{label} {number}'
        if len(part['label'].encode('utf-8'))>63:
            raise ValueError('Door component name exceeds the Blender limit: '+part['label'])
