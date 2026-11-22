"""Window flower shelves, lateral cut and the shared eaves outlet."""
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from frontage import finish,point,slab,SILL,RED,PLASTER,STONE
IRON='Shanyin garden | aged shelf iron'
PIPE='Shanyin garden | grey downpipe'
GLINT='Shanyin garden | metal collars'
PALETTE={IRON:finish((69,67,59),.79),PIPE:finish((95,91,80),.75),GLINT:finish((120,113,96),.74)}
def add_fittings(b,lod,layout):
    for i,r in enumerate(layout['upper_openings'],1):
        x0,x1=r['x0']-.055,r['x1']+.055;z=r['z_sill']-.025
        front=-.39-.025*(i%2);back=-.035
        slab(b,x0,x1,front,front+.032,z-.042,z,IRON,f'Flower shelf {i} | edge')
        for j,x in enumerate([x0+.035,x1-.035],1):
            slab(b,x-.016,x+.016,front,back,z-.036,z+.002,IRON,f'Flower shelf {i} | side arm {j}')
            b.tube([(x,-.014,z-.245),(x,front+.057,z-.030)],.012,IRON,5 if lod else 8,f'Flower shelf {i} | diagonal {j}')
        for j,x in enumerate(np.linspace(x0+.16,x1-.16,5 if lod else 11),1):
            slab(b,x-.007,x+.007,front+.018,back,z-.029,z-.015,IRON,f'Flower shelf {i} | bottom bars')
    left=point(layout,layout['front_u'][0],800)[0];right=point(layout,layout['front_u'][1],800)[0]
    # Show a shallow side return; the back is an explicit section of the architectural exhibit.
    for side,x in [('West',left),('Party',right-.23)]:
        slab(b,x,x+.23,.18,1.86,-.13,layout['eave_z']-.20,PLASTER,side+' | short brick return')
        for v0,v1 in [(446,478),(766,790)]:
            z0,z1=point(layout,626,v1)[2],point(layout,626,v0)[2]
            xx=x-.004 if side=='West'else x+.226
            slab(b,xx,xx+.008,.18,1.86,z0,z1,RED,side+' | return sill bands')
    z=layout['eave_z'];x=right-.010;y=-.112
    path=[(x,y,.08),(x,y,z-.88),(x,-.19,z-.77),(x,layout['eave_y']+.13,z-.38),(x,layout['eave_y']+.095,z-.18)]
    b.tube(path,.050,PIPE,8 if lod else 14,'Garden edge | rainwater pipe with two offsets')
    for zz in np.arange(.60,z-.9,1.39):
        b.tube([(x,y,zz),(x,y,zz+.047)],.060,GLINT,8 if lod else 14,'Garden edge | downpipe collars')
