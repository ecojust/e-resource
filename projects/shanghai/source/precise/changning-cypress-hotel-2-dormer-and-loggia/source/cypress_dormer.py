"""Timber dormer with deep cheeks and separate fixed and projecting window leaves."""
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from lawn import BASE, FRONT, FRONT_X, SLOPE, front_poly, plane_world, roof_z

WOOD='Red lead painted timber';DARK='Shadowed window joinery';TRIM='Sunlit terracotta timber trim';FIRED='Yellow clay on the dormer cheek'
GLASS_LEFT='Blue on left dormer glass';GLASS_RIGHT='Dark blue on projecting casement';CURTAIN='Pale curtain behind the left pane'
EDGE='Dark copper flashing';BEAD='Orange sash bead'

def sill(b,x0,x1,depth,z0,z1,mat,name):
    b.box([(x0+x1)*.5,FRONT-depth*.37,(z0+z1)*.5],[x1-x0,depth,z1-z0],mat,label='Dormer/'+name)

def add_dormer(b,lod):
    x0,x1=FRONT_X
    facade=Facade(b,[x0,FRONT],[x1,FRONT],'Lawn roof dormer')
    offset=(x0+x1)*.5
    def field(pixel):
        coords=plane_world(pixel,1,FRONT)[:,[0,2]];coords[:,0]-=offset;return Polygon(coords)
    outer=field([[479.7,186.8],[519.1,181.7],[519.1,216.6],[479.5,219.9]])
    # The two casements are different in the photograph. The light catching on the
    # bottom of the left opening and the projecting right-hand leaf are made individually.
    holes=[field(loop)for loop in [
        [[486.2,190.9],[498.1,189.7],[498.1,217.3],[486.0,219.0]],
        [[502.1,188.8],[512.6,187.4],[512.6,215.0],[502.2,214.1]]]]
    frame=outer.difference(unary_union(holes));facade.prism(frame,-.123,.012,WOOD,'painted face with two window openings')
    for i,hole in enumerate(holes):
        facade.prism(hole.buffer(.024,join_style=2),-.139,-.124,GLASS_LEFT if i==0 else GLASS_RIGHT,'deep glass '+str(i+1))
        inner=hole.buffer(-.046,join_style=2);facade.prism(hole.difference(inner),-.103,-.027,DARK,'glazing rebate '+str(i+1))
        facade.prism(hole.buffer(.041,join_style=2).difference(hole),-.018,.034,TRIM,'raised sash trim '+str(i+1))
    inset=field([[487.5,214.2],[490.4,214.7],[493.8,215.1],[497.0,214.8],[497.1,217.3],[486.9,218.3]])
    facade.prism(inset.intersection(holes[0]),-.123,-.108,CURTAIN,'pale lower curtain')
    # Construct the right leaf on its own inclined plane. Its hinge and lead are
    # based on the two photographed jambs. The exact swing angle is estimated.
    uv=[[502.15,201],[512.6,201]]
    xy=[plane_world([q],1,depth)[0,:2] for q,depth in zip(uv,[FRONT-.13,FRONT-.006])]
    leaf=Facade(b,*xy,'Open dormer leaf')
    px=[[502.2,188.8],[512.6,187.4],[512.6,215.0],[502.2,214.1]]
    q=np.array(px);from lawn import Q,EYE
    rays=np.c_[q,np.ones(4)]@np.linalg.inv(Q[:,:3]).T
    xyz=EYE+(np.dot(leaf.center-EYE,leaf.n)/(rays@leaf.n))[:,None]*rays
    leaf_shape=Polygon(np.c_[(xyz-leaf.center)@leaf.t,xyz[:,2]])
    pane=leaf_shape.buffer(-.050,join_style=2)
    leaf.prism(pane,-.025,-.011,GLASS_RIGHT,'angled glazing')
    leaf.prism(leaf_shape.difference(pane),-.055,.021,WOOD,'tilted timber frame')
    leaf.prism(leaf_shape.buffer(.011,join_style=2).difference(leaf_shape),-.013,.027,BEAD,'raised leading bead')
    low=roof_z(FRONT);up=plane_world([[518.5,181.5]],1,FRONT)[0,2];behind=(up-BASE)/SLOPE
    for side,x in [('left',x0),('right',x1)]:
        cross=Polygon([(FRONT,low-.07),(behind,roof_z(behind)-.07),(behind,up+.055),(FRONT,up+.055)])
        b.prism(cross,x-.043,x+.043,lambda y,z,u:(u,y,z),FIRED,'Dormer/'+side+' board cheek')
        step=.21
        for j,yy in enumerate(np.arange(FRONT+.07,behind-.09,step)):
            z=roof_z(yy)+.026
            if z>up-.022:continue
            seam=box(yy-.007,z,yy+.007,up-.027)
            b.prism(seam,x-.046,x+.046,lambda y,z,u:(u,y,z),TRIM,'Dormer/'+side+' boarding')
    eaves=plane_world([[474,182.2],[519.5,177.7]],1,FRONT-.222)
    # A shallow pent, with a raised side lip, returns from the front overhang
    # until its surface meets the parent slope.
    rear=behind+.24
    lower=[[p[0],p[1],p[2]]for p in eaves]
    upper=[[p[0],rear,p[2]+.145]for p in eaves]
    outline=[lower[0],lower[1],upper[1],upper[0]]
    bottom=[np.array(v)-[0,0,.105]for v in outline]
    b.add([*bottom,*outline],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],WOOD,'Dormer/shallow pent cap')
    for n,(left,right) in enumerate(zip(outline,outline[1:]+outline[:1])):
        b.tube([np.array(left)+[0,0,.022],np.array(right)+[0,0,.022]],.031,TRIM,6 if lod else 10,'Dormer/cap rim '+str(n+1))
    sill(b,x0-.055,x1+.055,.17,low-.056,low+.013,EDGE,'flashing beneath front')
