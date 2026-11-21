"""The east pier of the Shaoxing Road entrance to Lane 18, photographed in February 2020."""
from shapely.geometry import LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'grey dressed stone': {'color':[.52,.54,.53],'roughness':.94},
    'light stone face': {'color':[.70,.71,.67],'roughness':.89},
    'stepped stone edging': {'color':[.64,.65,.61],'roughness':.86},
    'recessed stone joint': {'color':[.30,.32,.31],'roughness':.97},
    'raised bronze gold': {'color':[.52,.37,.14],'metallic':.58,'roughness':.56},
    'green enamel sign': {'color':[.032,.22,.16],'roughness':.43},
    'cream sign letters': {'color':[.87,.88,.78],'roughness':.58},
    'weathered stone base': {'color':[.51,.49,.43],'roughness':.97}
}

# Original skeletal lettering drawn in a 1 x 1 design cell, x right and z up.
# Positions and spacing follow the cast characters; stroke ends are approximate.
STROKES={
    '金': [[(.51,.95),(.33,.74),(.06,.63)],[(.50,.89),(.70,.72),(.95,.64)],
          [(.30,.68),(.71,.68)],[(.18,.51),(.82,.51)],[(.51,.65),(.51,.13)],
          [(.23,.40),(.33,.27)],[(.77,.43),(.66,.25)],[(.09,.13),(.91,.13)]],
    '谷': [[(.34,.94),(.14,.76)],[(.65,.94),(.84,.77)],
          [(.51,.77),(.36,.59),(.18,.46),(.05,.40)],[(.49,.74),(.65,.58),(.84,.45),(.95,.41)],
          [(.29,.42),(.29,.11),(.72,.11),(.72,.42),(.29,.42)]],
    '邨': [[(.06,.77),(.55,.83)],[(.11,.68),(.13,.38),(.47,.43),(.49,.67)],
          [(.31,.93),(.30,.14),(.38,.08),(.53,.10)],
          [(.61,.06),(.61,.87),(.89,.87),(.76,.61),(.88,.50),(.91,.36),(.85,.28),(.69,.28)]],
    '1': [[(.29,.70),(.51,.87),(.51,.10)],[(.28,.10),(.73,.10)]],
    '8': [[(.50,.53),(.26,.65),(.24,.79),(.40,.89),(.64,.87),(.75,.75),(.68,.63),(.50,.53),(.28,.41),(.22,.24),(.33,.11),(.60,.08),(.76,.19),(.77,.35),(.64,.46),(.50,.53)]],
    '3': [[(.22,.80),(.40,.88),(.64,.86),(.72,.73),(.64,.59),(.42,.51),(.63,.50),(.78,.36),(.74,.19),(.59,.10),(.36,.11),(.20,.20)]],
    '–': [[(.19,.49),(.81,.49)]],
    '弄': [[(.20,.89),(.82,.89)],[(.27,.71),(.74,.71)],[(.51,.87),(.51,.56)],
          [(.13,.53),(.87,.53)],[(.09,.37),(.90,.37)],[(.36,.47),(.36,.30),(.32,.14),(.19,.06)],[(.66,.47),(.66,.07)]],
    '号': [[(.24,.90),(.24,.63),(.75,.63),(.75,.90),(.24,.90)],[(.10,.49),(.89,.49)],
          [(.36,.47),(.28,.34),(.74,.34),(.68,.12),(.59,.07),(.40,.10)]]}

def glyph(face,char,x,z,width,height,depth,stroke,lod,metal):
    shapes=[]
    for path in STROKES[char]:
        points=[(x+(u-.5)*width,z+(v-.5)*height) for u,v in path]
        shapes.append(LineString(points).buffer(stroke/2,cap_style='round',join_style='round',quad_segs=2 if lod else 5))
    body=unary_union(shapes)
    face.prism(body,depth,depth+(.015 if metal else .0025),'raised bronze gold' if metal else 'cream sign letters',('cast 'if metal else 'enamel ')+char)

def ring(face,x0,z0,x1,z1,width,d0,d1,material,label):
    face.prism(box(x0,z0,x1,z1).difference(box(x0+width,z0+width,x1-width,z1-width)),d0,d1,material,label)

def add_building(builder,lod=False):
    face=Facade(builder,(-.5,0),(.5,0),'Lane 18 east pier')
    # The left edge is the actual passage. The short boundary wall is wholly
    # on the right, clear of the gate and separate from the mapped row houses.
    face.box(0,.110,.86,.22,.53,-.21,'weathered stone base','single street plinth')
    face.box(0,.246,.79,.052,.49,-.205,'stepped stone edging','sloped plinth shoulder')
    face.box(0,1.13,.706,1.716,.425,-.2025,'recessed stone joint','pier core')
    for i,(low,high) in enumerate([(.272,.688),(.699,1.027),(1.038,1.348),(1.359,1.646),(1.657,1.992)]):
        face.box(0,(high+low)/2,.71,high-low,.44,-.207,'grey dressed stone','dressed pier course '+str(i+1))
    face.box(0,2.013,.67,.042,.415,-.197,'stepped stone edging','pier upper set-back')
    face.box(0,2.056,.59,.047,.37,-.188,'light stone face','low cap')
    face.box(0,1.048,.509,1.418,.035,.030,'recessed stone joint','shadow around title tablet')
    ring(face,-.248,.354,.248,1.747,.035,.045,.065,'stepped stone edging','thick tablet surround')
    if not lod:ring(face,-.237,.365,.237,1.736,.014,.065,.072,'light stone face','thin bevel on tablet surround')
    face.box(0,1.050,.436,1.340,.021,.051,'light stone face','name tablet')
    for char,high in zip('金谷邨',(1.457,1.071,.636)):
        glyph(face,char,0,high,.251,.255,.062,.021 if lod else .019,lod,True)
    # Chamfered enamel sign and its readable address. The tiny lower line in
    # the available 2020 images cannot be transcribed and is left unlettered.
    board=box(-.237,1.805,.237,1.967).buffer(.018,join_style='round',quad_segs=2 if lod else 8)
    face.prism(board,.040,.060,'green enamel sign','green Lane 18 address')
    for i,ch in enumerate('18弄1–83号'):
        glyph(face,ch,(i-3.5)*.048,1.913,.038,.061,.060,.0065 if lod else .0054,lod,False)
    face.box(.640,.813,.568,1.626,.25,-.215,'light stone face','short wall beside entrance')
    face.box(.640,.170,.568,.34,.279,-.21,'weathered stone base','wall base course')
    face.box(.640,1.661,.568,.070,.29,-.21,'stepped stone edging','wall coping')
    face.box(.640,1.715,.568,.038,.269,-.21,'light stone face','wall top')
    # Only the span immediately adjoining the pier is included. No second
    # entrance or shop structure is inferred beyond the photographed panel.
    if not lod:
        ring(face,.391,.407,.903,1.281,.026,-.096,-.072,'stepped stone edging','adjoining recessed panel border')
    else:
        face.box(.65,.843,.50,.806,.016,-.084,'stepped stone edging','wall panel edge')
