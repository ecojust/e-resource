"""No. 2 street connections between the independently observed projecting window groups."""
from shapely.geometry import box
from shapely.ops import unary_union
from central_stair import WALL,BASE,CREAM,FRAME,PANE,LANDING,SOFFIT
from stair_surface import PLAN,Camera
from street_bays import bay_layout,bay_wall_cutouts
from street_entry import openings as entry_openings
from east_end_sashes import openings as upper_end_openings, add_upper_sashes

def block(b,left,right,front,back,bottom,top,mat,label):
    if left>=right or front>=back or bottom>=top:return
    b.box(((left+right)/2,(front+back)/2,(bottom+top)/2),(right-left,back-front,top-bottom),mat,label='Street section | '+label)

def shell(b,shape,y,mat,name,thickness=.18):
    if shape.is_empty:return
    b.prism(shape,-y-thickness,-y,lambda x,z,d:(x,-d,z),mat,'Street section | '+name)

def field(b,left,right,depth,top,holes,label):
    outer=box(left,0,right,top).difference(unary_union(holes))
    shell(b,outer.intersection(box(left,0,right,.55)),depth-.01,BASE,label+' plinth')
    shell(b,outer.intersection(box(left,.55,right,top)),depth,WALL,label+' walls')

def ordinary_sash(b,bounds,y,nx,nz,name):
    left,sill,right,head=bounds;r=box(*bounds)
    shell(b,r,y+.125,PANE,name+' glazing',.017)
    trim=r.difference(box(left+.04,sill+.04,right-.04,head-.045))
    bars=[box(left+(right-left)*i/nx-.014,sill,left+(right-left)*i/nx+.014,head) for i in range(1,nx)]
    bars.extend(box(left,sill+(head-sill)*i/nz-.012,right,sill+(head-sill)*i/nz+.012)for i in range(1,nz))
    shell(b,unary_union([trim,*bars]),y+.066,FRAME,name+' steel frame',.044)
    block(b,left-.047,right+.055,y-.047,y+.02,sill-.058,sill+.012,CREAM,name+' sill')
    block(b,left-.035,right+.039,y-.035,y+.015,head-.005,head+.052,CREAM,name+' head')

def add_balconies(b,lod):
    left,right=2.32,4.55; rear=1.82
    lower_window=[v for v in bay_wall_cutouts() if v.bounds[0]>1.7 and v.bounds[0]<3.0]
    upper=[]
    for z,h in [(3.80,5.98),(6.92,9.32)]:
        upper.append((2.96,z,4.11,h))
    field(b,left,right,rear,9.86,[*lower_window,*[box(*v) for v in upper]],'balcony back wall')
    for num,(x,z,xx,h) in enumerate(upper,1):
        ordinary_sash(b,(x,z,xx,h),rear,2,5,'balcony door '+str(num))
        y=.89 if num==1 else 1.00
        block(b,left-.015,right+.02,y,rear+.04,z-.115,z,SOFFIT,'balcony slab '+str(num))
        # The 2015 winter side views show two short returns, a top rail and a
        # lower row of upright iron bars. Loose laundry and air conditioners
        # are omitted from the architecture.
        for yy in [y+.035]:
            for dz in (.080,.583,.907):
                block(b,left,right,yy,yy+.022,z+dz,z+dz+.019,LANDING,'balcony front rail '+str(num))
            count=16 if not lod else 12
            for i in range(count+1):
                u=left+.017+(right-left-.045)*i/count
                block(b,u,u+.014,yy-.005,yy+.019,z+.075,z+.922,LANDING,'balcony upright '+str(num))
        for u in (left+.009,right-.023):
            for dz in (.081,.590,.909):
                block(b,u,u+.019,y+.028,rear,z+dz,z+dz+.018,LANDING,'balcony iron return '+str(num))
            for i in (1,2,3,4):
                v=y+(rear-y)*i/5
                block(b,u,u+.016,v,v+.015,z+.08,z+.919,LANDING,'return upright '+str(num))
        block(b,left-.02,right+.03,y-.019,y+.025,z-.126,z-.050,CREAM,'pale slab edge '+str(num))

def add_joining_walls(b,lod=False):
    group=bay_layout();cut=bay_wall_cutouts()
    west=group['west']['plan'];middle=group['three-window bay']['plan'];east=group['east shoulder']['plan']
    wall_y=1.75
    # A single narrow ground window is visible in the setback between the two left groups.
    c=Camera();l=c.wall((529,955),wall_y);r=c.wall((568,1054),wall_y)
    slit=(l[0],r[2],r[0],l[2]);extra=[box(*slit)]
    left_edge=min(west[0][0],-12.53)-.12
    field(b,left_edge,PLAN[0,0],wall_y,10.19,[*cut,*extra],'street wing to left of stair')
    ordinary_sash(b,slit,wall_y,2,4,'narrow window between left projections')
    # The long folded window group leaves a short return where its end and
    # the stair wall are offset in plan.
    end_x,end_y=middle[-1]
    if PLAN[0,0]>end_x:
        field(b,end_x,PLAN[0,0],min(end_y,PLAN[0,1]),9.11,[],'left return of the stair enclosure')
    add_balconies(b,lod)
    last=8.15
    y=2.40
    right_hole=entry_openings({'right_wall_y':y})['right_window'][1]
    field(b,east[0][0],last,y,9.86,[*cut,right_hole,*upper_end_openings()],'wall by the second number 2 plate')
    add_upper_sashes(b,lod,right_wall_y=y)
    return left_edge,last
