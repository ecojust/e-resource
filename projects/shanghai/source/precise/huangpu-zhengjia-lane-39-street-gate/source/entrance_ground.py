"""Photographic layout of the tiled planter and the narrow strip of 2015 access paving."""
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import Polygon,LineString,box
from courtyard_fabric import paint,solid
from zheng_gate_camera import plane

DATA=Path(__file__).resolve().parents[1]/'measurements'
TILE=['Lane entrance | pale ceramic tile '+str(i+1)for i in range(4)]
GROUT='Lane entrance | grey mortar bed'
SOIL='Lane entrance | earth inside low enclosure'
ACC='Lane entrance | grey access paving'
CURB='Lane entrance | ash-grey curb'
BLOCKS=['Lane entrance | small sidewalk paver '+str(i+1)for i in range(4)]
PALETTE={GROUT:paint([111,104,90]),SOIL:paint([83,75,57]),ACC:paint([140,136,129]),CURB:paint([161,156,147])}
PALETTE.update({m:paint(rgb)for m,rgb in zip(TILE,[[160,154,139],[172,165,151],[166,158,142],[154,149,137]])})
PALETTE.update({m:paint(rgb)for m,rgb in zip(BLOCKS,[[130,124,115],[143,138,127],[137,131,121],[151,145,137]])})

def planter_data():
    o=json.loads((DATA/'entrance-planter-2015.json').read_bytes())
    joint=json.loads((DATA/'entrance-planter-joints.json').read_bytes())
    top=np.array(o['top_uv']);bottom=np.array(o['bottom_uv'])
    floor=np.array([plane(p,2,0.,o['view'])for p in bottom])
    v=np.array([plane(p,2,0.,o['view'])for p in top]);d=np.array([plane(p,2,1.,o['view'])for p in top])-v
    h=(np.sum((floor-v)[:,:2]*d[:,:2],axis=1)/np.sum(d[:,:2]**2,axis=1))
    height=float(np.median(h[2:-1]))
    xy=(.33*(v+d*height)+.67*floor)[:,:2]
    return PchipInterpolator(top[:,0],xy,axis=0),top[:,0],height,joint

def wall_tile(b,pts,inward,z0,z1,material,label):
    # Give each glazed face a thickness and let the joints show the substrate.
    a,c=pts;v=[[*a,z0],[*c,z0],[*c,z1],[*a,z1]]
    v += [[x+inward[0],y+inward[1],z]for x,y,z in v]
    solid(b,v,[[0,1,2,3],[7,6,5,4],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]],material,label)

def planter(b,lod):
    curve,up,height,j=planter_data()
    u=np.linspace(up[0],up[-1],50);points=curve(u)
    # The interior is to the left of the line as it curves from the wall to the gate pier.
    face=LineString(points)
    core=face.offset_curve(.016).buffer(.058,single_sided=True,join_style=2)
    b.prism(core,-.012,height-.009,lambda x,y,z:(x,y,z),GROUT,'Curved ceramic planter body')
    edges=[float(up[0]),*map(float,j['vertical_joint_u_px']),float(up[-1])]
    heights=[0.,height*(1-.752),height*(1-.3961),height]
    for i,(start,end)in enumerate(zip(edges[:-1],edges[1:])):
        if end-start<.8:continue
        a,c=curve(np.array([start,end]));v=c-a;length=np.linalg.norm(v);v=v/length
        inward=np.array([-v[1],v[0]])*.021
        # The last complete tile at the foreshortened end may span several projected millimetres.
        subdivisions=max(1,int(np.ceil(length/.23)))
        for l in range(subdivisions):
            a1=a+(c-a)*(l/subdivisions)+v*.0032
            c1=a+(c-a)*((l+1)/subdivisions)-v*.0032
            for row in range(3):
                wall_tile(b,[a1,c1],inward,heights[row]+.004,heights[row+1]-.003,
                          TILE[(3*i+l+row)%4],f'Planter glazed tile {i+1:02d}-{l+1}, row {row+1}')
    bed=Polygon([*list(face.offset_curve(.075).coords),(-5.69,1.36)])
    if not bed.is_valid:bed=bed.buffer(0)
    b.prism(bed,.018,height-.090,lambda x,y,z:(x,y,z),SOIL,'Exposed bed within street planter')
    return face

def pavement(b,lod):
    paths=json.loads((DATA/'entrance-ground-observations.json').read_bytes())
    c=np.array([plane(q,2,-.065,'center20')for q in paths['stone_curb_line_2020']])
    cy=np.polyfit(c[:,0],c[:,1],1)
    threshold=np.array([plane(q,2,-.025,'center15')for q in paths['2015_paver_to_lane_seam']])
    sy=np.polyfit(threshold[:,0],threshold[:,1],1)
    lo,hi=-5.85,3.45
    curb=lambda x:float(np.polyval(cy,x));seam=lambda x:float(np.polyval(sy,x))
    walkway=Polygon([(lo,curb(lo)),(hi,curb(hi)),(hi,seam(hi)),(lo,seam(lo))])
    z=lambda x,y:float(-.064+.039*(y-curb(x))/(seam(x)-curb(x)))
    cast=lambda x,y,h:(x,y,z(x,y)+h)
    b.prism(walkway,-.100,-.012,cast,GROUT,'Mortar beneath the paved sidewalk')
    # Near and far datasets preserve the boundary. The far model combines each adjacent pair.
    dx,dy=(.209,.106)if not lod else(.418,.212)
    for j,y in enumerate(np.arange(min(curb(lo),curb(hi))-.12,max(seam(lo),seam(hi))+.14,dy)):
        for k,x in enumerate(np.arange(lo-dx*(.5 if j%2 else 1.),hi,dx)):
            piece=box(x+.003,y+.002,x+dx-.003,y+dy-.002).intersection(walkway)
            if piece.area<.00020:continue
            b.prism(piece,-.015,-.001,cast,BLOCKS[(k+2*j+k*j)%4],f'Sidewalk sett course {j+1:02d}, brick {k+1:02d}')
    curve,stations,_,_=planter_data()
    flank=curve(np.linspace(stations[0],stations[-1],55))
    # Follow the actual tile face wherever it meets the approach. Farther in
    # both the street planter and flanking wall end before the lane widens.
    access=Polygon([(lo,seam(lo)-.015),(hi,seam(hi)-.015),(hi,.29),(2.12,.71),(2.11,4.75),(-2.66,4.75),*reversed(flank.tolist())])
    if not access.is_valid:access=access.buffer(0)
    b.prism(access,-.12,-.005,lambda x,y,z:(x,y,z+min(0.,.012*y)),ACC,'Inner approach visible through both gate piers')
    for i,(a,cx)in enumerate(zip(np.arange(lo,hi,.86),np.arange(lo+.86,hi+.86,.86))):
        cx=min(hi,cx)
        if cx-a<.05:continue
        part=Polygon([(a,curb(a)-.15),(cx-.005,curb(cx)-.15),(cx-.005,curb(cx)),(a,curb(a))])
        b.prism(part,-.164,-.066,lambda x,y,z:(x,y,z),CURB,f'Street kerbstone {i+1:02d}')

FLANK_TILE=['Flanking wall | muted ochre tile '+str(i+1) for i in range(4)]
FLANK_JOINT='Flanking wall | brown-grey mortar'
PALETTE[FLANK_JOINT]=paint([107,89,70])
PALETTE.update({m:paint(col)for m,col in zip(FLANK_TILE,[[139,99,71],[146,106,77],[132,94,67],[150,110,82]])})

def flanking_wall(b,lod):
    from courtyard_fabric import rect
    row=json.loads((DATA/'flanking-tiled-wall.json').read_bytes())
    x0,x1=row['wall_x_bounds_m'];y=row['surface_plane_y_m'];z=row['top_z_m']
    # A shallow return runs from the exposed corner back towards the gate pier.
    rect(b,x0,x1,y+.016,y+.19,-.015,z,FLANK_JOINT,'Short flanking wall facing the sidewalk')
    rect(b,x0,x0+.16,y+.18,row['inner_return_y_m'],-.01,z,FLANK_JOINT,'Return of short flanking wall by western pier')
    levels=sorted([.005,z]+[plane([628,v],1,y,'center15')[2]for v in row['visible_bed_rows_center15']])
    for r,(a,c) in enumerate(zip(levels[:-1],levels[1:])):
        if c-a<.016:continue
        for col,(left,right) in enumerate(zip(np.linspace(x0,x1,13)[:-1],np.linspace(x0,x1,13)[1:])):
            rect(b,left+.003,right-.003,y,y+.019,a+.003,c-.003,FLANK_TILE[(col+3*r)%4],f'Flank tile row {r+1:02d} block {col+1:02d}')
        for col,(left,right) in enumerate(zip(np.linspace(y+.014,row['inner_return_y_m'],10)[:-1],np.linspace(y+.014,row['inner_return_y_m'],10)[1:])):
            rect(b,x0-.015,x0+.005,left+.003,right-.003,a+.003,c-.003,FLANK_TILE[(col+3*r+1)%4],f'Flank return row {r+1:02d} block {col+1:02d}')

def add_entrance_ground(b,lod=False):
    planter(b,lod)
    pavement(b,lod)
    flanking_wall(b,lod)
