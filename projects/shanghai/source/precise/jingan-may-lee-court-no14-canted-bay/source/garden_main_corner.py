"""Photographed wing of May Lee Court no. 14. Local coordinates follow garden_bay."""
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
import garden_bay

X, Y = -3.00883, 1.555
SIDE_END, FRONT_END = 6.10, -1.53
SOFFIT_Z = 9.52883
EDGE_X, EDGE_Y = .54704, .37374
STONE = 'Garden side | warm grey cement window dressings'
LEDGE = 'Garden side | pale projecting stool'
REVEAL = 'Garden side | shaded plaster reveal'
METAL = 'Garden side | deep brown black casement'
HEAVY = 'Garden side | double meeting stile'
UNDER = 'Garden eave | warm soffit'
BROWN = 'Garden eave | brown stepped fascia'
DARK = 'Garden eave | dark weathered outer edge'
PANEL = 'Garden eave | pale inset face'
GLASS = tuple('Garden side | reflected glass '+str(i) for i in range(5))
PALETTE = {name:{'color': color,'roughness':rough} for name,color,rough in (
    (STONE,[.59,.515,.424],.88),(LEDGE,[.68,.593,.493],.87),
    (REVEAL,[.53,.465,.381],.90),(METAL,[.048,.049,.044],.48),
    (HEAVY,[.036,.039,.037],.50),(UNDER,[.58,.479,.359],.92),
    (BROWN,[.133,.091,.071],.78),(DARK,[.060,.063,.061],.70),
    (PANEL,[.53,.486,.362],.63),
    *[(m,c,.27) for m,c in zip(GLASS,([.069,.080,.079],[.112,.130,.134],
        [.151,.171,.177],[.210,.225,.216],[.292,.313,.303]))])}
# Face-coordinate contours: near and far jamb, stool and head, the measured
# horizontal rails and the vertical bars visible across the three deep reveals.
WINDOWS = (
    ('ground',3.371,4.995,.876,2.722,(1.333,1.632,1.916,2.248),(3.659,3.958,4.267,4.586)),
    ('middle',3.371,4.953,4.191,6.030,(4.592,4.890,5.185,5.507),(3.670,3.961,4.281,4.589)),
    ('upper',3.321,4.911,7.472,9.202,(7.873,8.169,8.463,8.785),(3.766,4.055,4.352,4.655)))
SETBACK = .19
def side(u,z,out):
    return X-out,-u,z
def front(x,z,out):
    return x,Y-out,z
def brick_uv(part,side_wall):
    # Use the same original running-bond material as the projecting bay and
    # repeat it at its physical scale rather than stretching a full facade.
    part['texcoords']=[(((-y if side_wall else x)+5)/3.06,1.-z/7.58)
                       for x,y,z in part['vertices']]
def add_walls(b):
    apertures=[box(-b_+.064,z0+.059,-a-.064,z1-.055) for _,a,b_,z0,z1,_,_ in WINDOWS]
    side_shape=box(-SIDE_END,0.,-Y,SOFFIT_Z).difference(unary_union(apertures))
    b.prism(side_shape,-.31,0.,side,garden_bay.BRICK,'Garden wing | return wall with three true openings')
    brick_uv(b.parts[-1],True)
    # Stop the new panel exactly on the existing terrace panel over its own
    # height. At lower levels the projecting bay has its own side face.
    front_shape=box(X,0.,FRONT_END,SOFFIT_Z).difference(box(-1.77,6.51,FRONT_END+.1,8.67))
    b.prism(front_shape,-.245,0.,front,garden_bay.BRICK,'Garden wing | brickwork beside projecting bay')
    brick_uv(b.parts[-1],False)

def strip(b,a,c,z0,z1,d0,d1,mat,label):
    b.prism(box(-c,z0,-a,z1),d0,d1,side,mat,label)
def window(b,definition,lod):
    level,a,c,z0,z1,rails,bars=definition
    prefix='Garden '+level+' side casement | '
    def trim(near,far,low,high,d0,d1,mat,label):
        strip(b,near,far,low,high,d0,d1,mat,prefix+label)
    jamb=.098;ledge=.103;lintel=.088
    l,r,lo,hi=a+jamb,c-jamb,z0+ledge,z1-lintel
    for edge0,edge1,label in ((a,l,'near jamb'),(r,c,'far jamb')):
        trim(edge0,edge1,lo,hi,-SETBACK-.056,.020,REVEAL,label+' deep plaster return')
        trim(edge0,edge1,lo,hi,-.018,.032,STONE,label+' outer face')
    trim(a,c,hi,z1,-SETBACK-.056,.036,STONE,'head and recessed soffit')
    # Sloping weathering surface and a lower nose cast the narrow dark line
    # visible under the pale sill. Run the section past both outer jamb faces.
    sill=Polygon([(-SETBACK-.058,z0-.014),(.081,z0-.014),(.104,z0+.008),
                  (.104,z0+.052),(.086,z0+.072),(-.035,lo),(-SETBACK-.058,lo)])
    b.prism(sill,a-.022,c+.022,lambda d,z,y:(X-d,y,z),LEDGE,prefix+'weathered projecting stool')
    if not lod:
        trim(a-.028,c+.028,z0+.009,z0+.034,.057,.101,STONE,'stool drip moulding')
        trim(a-.018,c+.018,z1-.021,z1+.013,.013,.062,LEDGE,'bead over head')
    d=-SETBACK; border=.032
    for left,right,label in ((l,l+border,'near stile'),(r-border,r,'far stile')):
        trim(left,right,lo,hi,d-.040,d+.009,METAL,label)
    for bot,top,label in ((lo,lo+border,'bottom rail'),(hi-border,hi,'top rail')):
        trim(l+border,r-border,bot,top,d-.040,d+.009,METAL,label)
    u_edges=(l+border,*bars,r-border);z_edges=(lo+border,*rails,hi-border)
    swatches=GLASS_TONES[level]
    for j,(zb,zt) in enumerate(zip(z_edges,z_edges[1:])):
        for i,(ya,yb) in enumerate(zip(u_edges,u_edges[1:])):
            trim(ya,yb,zb,zt,d-.046,d-.035,GLASS[swatches[j][i]],f'pane {j+1}.{i+1}')
    for i,yy in enumerate(bars):
        meeting=i==2;half=.016 if meeting else .010
        trim(yy-half,yy+half,lo+border,hi-border,d-.041,d+.012 if meeting else d-.004,
             HEAVY if meeting else METAL,'meeting stile' if meeting else 'slender vertical bar')
    for i,zz in enumerate(rails):
        half=.014 if i==3 else .010
        trim(l+border,r-border,zz-half,zz+half,d-.033,d+.001,METAL,'transom' if i==3 else 'horizontal bar')
# Grouped values from per-pane native source swatches, with hidden panes following
# the nearest clear pane. The original photographs are never textures.
GLASS_TONES = {
    'ground': ((2, 2, 2, 4, 3), (2, 2, 2, 4, 3), (2, 2, 2, 4, 3), (2, 2, 2, 4, 3), (0, 0, 0, 4, 0)),
    'middle': ((1, 1, 1, 4, 4), (2, 2, 2, 4, 4), (2, 2, 2, 4, 3), (1, 1, 1, 4, 2), (0, 0, 0, 0, 0)),
    'upper': ((4, 4, 3, 4, 4), (4, 4, 3, 4, 4), (4, 4, 3, 3, 4), (4, 4, 4, 3, 4), (1, 1, 0, 0, 2)),
}
def swept_trim(b,profile,material,label):
    # Each end is one closed profile. Carry the same profile through one
    # mitred corner, with the terminal planes available to the adjacent wing.
    n=len(profile);vertices=[]
    for edge in ('side','corner','front'):
        for t,z in profile:
            x=X-t*EDGE_X if edge!='front' else FRONT_END
            y=Y-t*EDGE_Y if edge!='side' else SIDE_END
            vertices.append((x,y,z))
    faces=[tuple(reversed(range(n))),tuple(range(2*n,3*n))]
    for sec in range(2):
        for j in range(n):
            k=(j+1)%n
            faces.append((sec*n+j,sec*n+k,(sec+1)*n+k,(sec+1)*n+j))
    # The section is convex here, including the inner bevel of the dark band.
    import numpy as np
    vv=np.array(vertices)
    volume=sum(np.dot(vv[f[0]],np.cross(vv[f[j]],vv[f[j+1]]))
               for f in faces for j in range(1,len(f)-1))
    if volume<0:faces=[tuple(reversed(f)) for f in faces]
    b.add(vertices,faces,material,label)
def eaves(b,lod):
    z=SOFFIT_Z
    swept_trim(b,[(0,z),(1.,z),(1.,z+.081),(0,z+.081)],UNDER,'Garden turn | continuous pale eave soffit')
    swept_trim(b,[(.917,z+.065),(1.025,z+.065),(1.055,z+.094),(1.055,z+.146),
                  (.917,z+.146)],BROWN,'Garden turn | returned brown fascia')
    if not lod:
        swept_trim(b,[(.984,z+.025),(1.025,z+.025),(1.042,z+.047),(1.042,z+.066),
                      (.984,z+.066)],BROWN,'Garden turn | bead below fascia')
    swept_trim(b,[(.83,z+.14),(1.043,z+.14),(1.10,z+.245),(1.10,z+.414),
                  (1.035,z+.477),(.83,z+.477)],DARK,'Garden turn | curved dark outer roof edge')
    swept_trim(b,[(.92,z+.468),(1.06,z+.468),(1.082,z+.485),(1.082,z+.518),
                  (.92,z+.518)],DARK,'Garden turn | projecting upper rim')
    # A pale face in a dark frame is visible on each of the two approaching
    # eaves. The first is separate from the downpipe head on the same fascia.
    b.box((-2.49,Y-EDGE_Y-.038,z+.174),(.439,.045,.292),DARK,label='Garden eave | inset panel casing')
    b.box((-2.49,Y-EDGE_Y-.065,z+.174),(.355,.014,.222),PANEL,label='Garden eave | pale rectangular inset')
    b.box((X-EDGE_X-.048,4.286,z+.176),(.043,.404,.291),DARK,label='Garden return eave | inset panel casing')
    b.box((X-EDGE_X-.076,4.286,z+.176),(.014,.319,.220),PANEL,label='Garden return eave | pale rectangular inset')
def add_garden_main_corner(b,lod=False):
    garden_bay.texture()
    b.palette.update({garden_bay.BRICK:dict(garden_bay.PALETTE[garden_bay.BRICK]),**PALETTE})
    add_walls(b)
    for definition in WINDOWS:window(b,definition,lod)
    eaves(b,lod)
