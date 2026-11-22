"""Brick facade, pale infills, garden porch slab, steps and the masonry eaves."""
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from material_names import PLASTER,RED,TEXTURES
from ground_arcade import openings as ground_cuts
from shanyin_arches import opening_polygon

SILL='Shanyin garden | light plaster spandrels'
STONE='Shanyin garden | warm pale stone'
TRIM='Shanyin garden | red-brown wood'
SOFFIT='Shanyin garden | eaves underside'
DARK='Shanyin garden | shaded edge of gallery'
PLANK='Shanyin garden | shaded brown paint'
def finish(rgb,rough=.87):
    x=np.asarray(rgb,float)/255.
    return dict(color=np.where(x>.04045,((x+.055)/1.055)**2.4,x/12.92).tolist(),roughness=rough,metallic=0.)
PALETTE={PLASTER:dict(texture=str(TEXTURES[PLASTER]),color=[1.,1.,1.],roughness=.94,metallic=0.),
         RED:dict(texture=str(TEXTURES[RED]),color=[1.,1.,1.],roughness=.93,metallic=0.),
         SILL:finish((181,172,154)),STONE:finish((160,145,121)),TRIM:finish((107,62,46)),
         SOFFIT:finish((143,117,92)),DARK:finish((86,78,65)),PLANK:finish((102,73,55))}
def point(layout,u,v,y=0.):
    P=np.asarray(layout['camera_P']);m=P[:2]-np.array([u,v])[:,None]*P[2]
    x,z=np.linalg.solve(m[:,[0,2]],-m[:,1]*y-m[:,3]);return np.array([x,y,z])
def wall(b,poly,y0,y1,mat,label):
    b.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)
def field(layout,u0,y0,u1,y1):
    return Polygon([point(layout,u,v)[[0,2]]for u,v in [(u0,y1),(u1,y1),(u1,y0),(u0,y0)]])
def slab(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def add_frontage(b,lod,layout):
    left,right=layout['front_u'];xmin=point(layout,left,800)[0];xmax=point(layout,right,800)[0]
    W=layout['middle_window_width'];ops=layout['upper_openings']
    ground=unary_union(ground_cuts(layout,outer=True))
    upper=unary_union([opening_polygon(o)for o in ops])
    # At the two outer piers the outer arch curves stop at their axes. Below the capitals,
    # the outer half of each shaft also belongs to the separately modelled pier.
    edges=[field(layout,left-2,923,280,1132), field(layout,983,923,right+2,1132)]
    fixed=field(layout,left,442,right,1128).difference(unary_union(edges))
    # The arches carry their own brick rings and lower piers. The backing plate has true openings.
    plate=fixed.difference(unary_union([ground,upper]))
    depth=.14*W
    wall(b,plate,0.,depth,PLASTER,'Garden facade | grey brick spandrels and true openings')
    # Three strips read as different construction courses at the upper sill,
    # above the ground arcade and immediately beneath the wood eaves.
    for i,(a,c,y,mat,label) in enumerate([
            (442,479,-.016,RED,'red eaves frieze'),(766,791,-.046,RED,'continuous red string course'),
            (758,767,-.061,STONE,'upper sill course cap'),(792,798,-.016,RED,'string course lower roll'),
            (829,851,-.002,RED,'lower red belt above arcade')]):
        skin=field(layout,left,a,right,c).difference(unary_union([ground,upper]))
        wall(b,skin,y,.001,mat,'Garden facade | '+label)
    for i,row in enumerate(ops,1):
        x0,x1=row['x0'],row['x1']; sill=row['z_sill']
        a=point(layout,626,757)[2];edge=.065*W
        wall(b,box(x0-edge,a,x1+edge,sill-.022),-.018,.004,SILL,f'Upper bay {i} | pale spandrel below sash')
        slab(b,x0-.055,x1+.055,-.080,.08,sill-.064,sill+.001,STONE,f'Upper bay {i} | pale sill')
    for i,(u0,u1) in enumerate([(257,299),(489,539),(725,777),(963,1002)],1):
        for low,high in [(735,757),(578,588)]:
            wall(b,field(layout,max(left,u0),low,min(right,u1),high),-.022,.003,RED,f'Upper pier {i} | red facing course {low}')
    eave=layout['eave_z'];front=layout['eave_y']
    slab(b,xmin-.16,xmax,front+.035,.32,eave-.19,eave-.105,SOFFIT,'Garden facade | eaves soffit')
    slab(b,xmin-.19,xmax,front-.03,front+.106,eave-.113,eave+.012,TRIM,'Garden facade | projecting fascia')
    # The local exhibit includes only the short, visible gallery behind the front arches.
    depth_gallery=1.83
    slab(b,xmin,xmax,-.080,depth_gallery,-.155,0.,STONE,'Garden gallery | continuous raised landing')
    slab(b,xmin,xmax,.11,depth_gallery,3.92,4.09,SOFFIT,'Garden gallery | shallow ceiling return')
    slab(b,xmin,xmax,depth_gallery,depth_gallery+.15,-.02,4.10,DARK,'Garden gallery | shaded back plane')
    # The original shows a dark central recess. At the right the timber transom, glazed sidelights,
    # brick jambs and low blue-grey wall remain readable behind the front arcade.
    def backfield(u0,v0,u1,v1,mat,label,offset):
        outline=Polygon([point(layout,u,v,depth_gallery)[[0,2]] for u,v in [(u0,v1),(u1,v1),(u1,v0),(u0,v0)]])
        wall(b,outline,depth_gallery-offset,depth_gallery+.003,mat,'Garden gallery | '+label)
    for u0,v0,u1,v1,mat,label,offset in [
            (773,853,803,1119,PLASTER,'right opening brick jamb',.018),
            (802,987,850,1116,PLASTER,'right brick sill wall',.018),
            (773,991,849,997,RED,'right sill wall red course',.031),
            (805,859,812,989,PLANK,'sidelight west stile',.046),
            (845,858,852,1117,PLANK,'door jamb',.052),
            (814,858,818,989,PLANK,'sidelight narrow stile',.046),
            (831,850,837,987,PLANK,'sidelight central stile',.046),
            (803,879,938,886,PLANK,'cross transom',.050),
            (927,881,934,1112,PLANK,'east door jamb',.047),
            (881,840,887,879,PLANK,'transom upright',.045),
            (803,985,851,991,PLANK,'sidelight sill',.051),
            (560,878,566,1116,PLANK,'central recess left jamb',.044),
            (572,904,698,910,PLANK,'central recess head',.046)]:
        backfield(u0,v0,u1,v1,mat,label,offset)
    # The photographed three rises are confined to the right bay. The two other bays keep their raised plinth.
    x0=point(layout,756,1128)[0]+.195;x1=point(layout,984,1128)[0]-.18
    for i in range(3):
        slab(b,x0,x1,-.40*(i+1),-.40*i-.002,-.63,-.16*(i+1),STONE,f'Garden gallery | visible step {i+1}')
    for i,x in enumerate([x0-.096,x1+.096],1):
        profile=Polygon([(-1.22,-.63),(-1.22,-.29),(-.05,.24),(.11,.24),(.11,-.63)])
        b.prism(profile,x-.09,x+.09,lambda y,z,d:(d,y,z),STONE,f'Garden steps | sloping side curb {i}')
    slab(b,xmin,x0-.17,-.079,.22,-.63,-.155,SILL,'Garden gallery | plastered plinth at garden edge')
