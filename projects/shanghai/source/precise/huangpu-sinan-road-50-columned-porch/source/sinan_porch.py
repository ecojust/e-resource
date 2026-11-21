"""The photographed east porch of 50 Sinan Road. X points north, Y inward, Z up."""
from math import ceil, cos, pi, sin
from shapely.geometry import LineString, box

PALETTE = {
    'pebble dash': {'color': [.43, .40, .35], 'roughness': .98},
    'pale aggregate': {'color': [.59,.55,.47], 'roughness': .99},
    'dark aggregate': {'color': [.33,.32,.28], 'roughness': .98},
    'painted stucco': {'color': [.75,.73,.67], 'roughness': .90},
    'granite facing': {'color': [.48,.47,.45], 'roughness': .91},
    'step edge': {'color': [.52,.52,.49], 'roughness': .85},
    'reddish tile': {'color': [.46,.25,.19], 'roughness': .88},
    'sunlit tile': {'color': [.53,.31,.23], 'roughness': .88},
    'dark tile overlap': {'color': [.30,.21,.17], 'roughness': .96},
    'eave wood': {'color': [.235,.218,.188], 'roughness': .90},
    'aged timber': {'color': [.24,.145,.105], 'roughness': .80},
    'glazing': {'color': [.18,.23,.21], 'roughness': .31},
    'door panel': {'color': [.28,.165,.12], 'roughness': .79},
    'address brass': {'color': [.59,.47,.25], 'metallic': .30, 'roughness': .63},
    'dark enamel': {'color': [.16,.14,.11], 'roughness': .70}
}

# These surfaces use the measured street threshold as zero. The rear of the
# small photographed bay meets the retained eastern wall of the city mesh.
SOUTH, NORTH = -1.87, 1.65
FRONT, BACK = -1.53, .085
EAVE, RIDGE = 3.96, 4.79
DOOR_LEFT, DOOR_RIGHT = -.78, .29
COLUMN = (.765, -1.09)

def block(builder, name, material, x0,x1, y0,y1, z0,z1):
    builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),
                (x1-x0,y1-y0,z1-z0),material,label=name)

def steps(builder):
    # Three stone treads lead to the upper landing. The outer corners are rounded.
    for n,(left,right,front,top) in enumerate([
            (-1.00,1.02,-1.43,.16),(-.95,.99,-1.23,.31),
            (-.90,.91,-1.02,.455),(-.85,.60,-.58,.59)]):
        plan=box(left+.065,front+.065,right-.065,-.01)
        plan=plan.buffer(.065,quad_segs=7)
        builder.plan_prism(plan,0,top,'granite facing','stone threshold '+str(n+1))
        edge=plan.intersection(box(left-.01,front-.01,right+.01,front+.078))
        builder.plan_prism(edge,top-.035,top+.002,'step edge','rounded step nose '+str(n+1))

def jambs(builder,lod):
    # The left beam end projects from a pebble-dashed cheek. On the right
    # the sole free column stands in front of the number plate.
    block(builder,'south porch return','pebble dash',-1.37,-.98,-1.16,.06,0,3.70)
    block(builder,'south granite base','granite facing',-1.394,-.96,-1.184,.06,0,.53)
    block(builder,'south stucco band','painted stucco',-1.391,-.96,-1.18,.06,1.47,1.525)
    block(builder,'door south reveal','pebble dash',-.99,DOOR_LEFT,-.19,.09,.46,3.70)
    block(builder,'number plate wall','pebble dash',DOOR_RIGHT,1.22,-.18,.09,.38,3.75)
    block(builder,'back wall header','pebble dash',DOOR_LEFT,DOOR_RIGHT,-.18,.09,2.84,3.75)
    block(builder,'northern stone plinth','granite facing',DOOR_RIGHT,1.23,-.20,.07,.01,.54)
    block(builder,'northern wall band','painted stucco',DOOR_RIGHT,1.24,-.207,.07,1.47,1.525)
    if not lod:
        # Small original flecks are confined to the actual stucco. Their
        # pattern approximates the aggregate. No image pixels are embedded.
        for i in range(23):
            for j in range(25):
                x=DOOR_RIGHT+.018+i*.039; z=.56+j*.118+.018*sin(17*i+13*j)
                dx=.004+.004*(.5+.5*cos(i*7+j));h=.008+.005*sin(i+j*13)
                face=[(x-.003,-.181,z-h),(x+dx,-.181,z-h*.2),
                      (x+.001,-.181,z+h)]
                builder.add(face,[(0,1,2)],'pale aggregate' if(i+2*j)%4 else 'dark aggregate','exposed aggregate')

def post_and_beam(builder,lod):
    x,y=COLUMN
    block(builder,'square stone pedestal','granite facing',x-.255,x+.255,y-.255,y+.255,.18,.694)
    block(builder,'column base plate','painted stucco',x-.229,x+.229,y-.229,y+.229,.69,.746)
    profile=[(.74,.224),(.762,.232),(.795,.208),(.817,.18),(.853,.165),
             (2.91,.146),(2.94,.165),(2.986,.166),(3.012,.19),(3.044,.196),(3.083,.22)]
    builder.lathe(COLUMN,profile,'painted stucco',16 if lod else 52,'single circular porch column')
    block(builder,'square abacus','painted stucco',x-.226,x+.226,y-.225,y+.225,3.079,3.142)
    block(builder,'front timber tie in stucco','painted stucco',-1.075,.995,-1.283,-.90,3.127,3.429)
    block(builder,'back wall tie','pebble dash',-1.23,1.06,-1.19,.09,3.428,3.767)
    block(builder,'dark open eave soffit','eave wood',SOUTH+.08,NORTH-.08,FRONT+.07,BACK,3.77,3.91)

def door_and_address(builder,lod):
    lo,hi=DOOR_LEFT,DOOR_RIGHT
    for i,x in enumerate([lo,hi-.064]):
        block(builder,'outer door stile '+str(i),'aged timber',x,x+.064,-.199,-.064,.575,2.847)
    block(builder,'door head','aged timber',lo,hi,-.199,-.064,2.785,2.847)
    block(builder,'sill','step edge',lo,hi,-.23,-.026,.55,.612)
    block(builder,'door leaf','aged timber',lo+.064,hi-.064,-.122,-.078,.60,2.792)
    block(builder,'upper recessed glazing','glazing',lo+.124,hi-.126,-.131,-.122,1.974,2.682)
    for i,x in enumerate([lo+.34,lo+.61]):
        block(builder,'glazing bar '+str(i),'aged timber',x,x+.029,-.151,-.122,1.965,2.694)
    block(builder,'glazing cross rail','aged timber',lo+.119,hi-.119,-.153,-.123,2.24,2.274)
    for i in range(2):
        x=lo+.14+i*.40
        block(builder,'recessed door panel '+str(i),'door panel',x,x+.33,-.135,-.123,.76,1.83)
    block(builder,'50 enamel plate','address brass',.390,.714,-.203,-.181,2.325,2.570)
    # Original raised, independently drawn numerals. The indistinct small
    # characters beneath the number are omitted.
    paths=[[(.495,2.535),(.446,2.535),(.443,2.48),(.468,2.488),(.496,2.477),(.500,2.45),(.484,2.431),(.452,2.433),(.44,2.445)]]
    paths.append([(.587+.028*cos(2*pi*i/16),2.484+.055*sin(2*pi*i/16))for i in range(17)])
    for i,p in enumerate(paths):
        polygon=LineString(p).buffer(.0058 if lod else .0045,cap_style=2,join_style=2)
        builder.prism(polygon,.204,.211,lambda x,z,out:(x,-out,z),'dark enamel','enamel numeral '+str(i))

def mix(a,b,t):
    return tuple(x+(y-x)*t for x,y in zip(a,b))

def tiled_roof(builder,lod):
    # Four real roof edges frame a shallow hipped roof. The short ridge's
    # rear side is partly screened by trees in 2021; 2017 shows the end hip.
    rim=[(SOUTH,FRONT,EAVE),(NORTH,FRONT,EAVE),
         (NORTH,BACK,EAVE),(SOUTH,BACK,EAVE)]
    a=(-.40,-.69,RIDGE);b=(.38,-.69,RIDGE)
    slopes=[(rim[0],rim[1],a,b),(rim[1],rim[2],b,b),
            (rim[2],rim[3],b,a),(rim[3],rim[0],a,a)]
    for n,(lo0,lo1,hi0,hi1) in enumerate(slopes):
        builder.add([lo0,lo1,hi1,hi0],[(0,1,2),(0,2,3)],'dark tile overlap','dark roof deck '+str(n))
        side_lo=[(x,y,z-.086)for x,y,z in (lo0,lo1)]
        builder.add([*side_lo,lo1,lo0],[(0,1,2,3)],'eave wood','fascia board '+str(n))
        rows=5 if lod else 11
        n_base=ceil(((lo1[0]-lo0[0])**2+(lo1[1]-lo0[1])**2)**.5/(.308 if lod else .184))
        for row in range(rows):
            bottom=row/rows;top=(row+1)/rows
            l0,l1=mix(lo0,hi0,bottom),mix(lo1,hi1,bottom)
            h0,h1=mix(lo0,hi0,top),mix(lo1,hi1,top)
            count=max(2,round(n_base*(1-bottom*.6)))
            for j in range(count):
                left=j/count;right=(j+1)/count
                gap=.004 if lod else .016
                c0,c1=left+gap/count,right-gap/count
                vertices=[]
                for zfrac,end0,end1 in [(0,l0,l1),(1,h0,h1)]:
                    for u,camber in [(c0,0),((c0+c1)/2,.010),(c1,0)]:
                        x,y,z=mix(end0,end1,u)
                        nose=.013*(1-zfrac)
                        vertices.append((x,y,z+.006+nose+camber))
                builder.add(vertices,[(0,1,4,3),(1,2,5,4)],
                    'sunlit tile' if(5*j+3*row+n)%9<2 else 'reddish tile','tile courses '+str(n))
    builder.add([(x,y,EAVE-.09)for x,y,z in reversed(rim)],[(0,1,2,3)],'eave wood','timber underside')
    for i,(low,high) in enumerate([(rim[0],a),(rim[1],b),(rim[2],b),(rim[3],a),(a,b)]):
        path=[(x,y,z+.044)for x,y,z in (low,high)]
        builder.tube(path,.037 if i<4 else .046,'reddish tile',8 if lod else 15,'capped hipped roof seam '+str(i))

def add_building(builder,lod=False):
    steps(builder)
    jambs(builder,lod)
    post_and_beam(builder,lod)
    door_and_address(builder,lod)
    tiled_roof(builder,lod)
