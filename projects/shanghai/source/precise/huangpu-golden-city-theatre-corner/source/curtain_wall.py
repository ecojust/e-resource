"""Five glazed lanes, four full-height pale columns and the geometric guards in the upper foyer."""
from math import cos,radians,sin

from curved_front import finish

COLUMN='Theatre pale rounded columns'
STEEL='Theatre dark frame steel'
BORDER='Theatre black projecting rails'
BRONZE='Theatre patinated fretwork'
COOL='Theatre blue grey upper panes'
SHADE='Theatre shaded foyer panes'
AMBER='Theatre two amber glazed rows'
OPEN='Theatre shadows behind open casements'
PALETTE={COLUMN:finish((214,207,188),.77),STEEL:finish((68,68,66),.54,.32),
         BORDER:finish((55,55,52),.61,.26),BRONZE:finish((92,89,76),.57,.42),
         COOL:finish((135,150,151),.36,.16),SHADE:finish((105,120,123),.39,.13),
         AMBER:finish((141,122,94),.49,.10),OPEN:finish((64,69,65),.73)}


def tilted_pane(frame,u,width,z0,z1):
    """A top-hung light stands proud at its bottom, as in the upper left of the 2024 image."""
    angle=radians(15.)
    h=z1-z0
    def part(name,mat,a,b,lo,hi,back,fore):
        v=[]
        for level in (lo,hi):
            dz=h-level
            for x,y in [(a,back),(b,back),(b,fore),(a,fore)]:
                v.append(frame.tangent(u,x,-.27+y+dz*sin(angle),z1-dz*cos(angle)))
        frame.b.add(v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,name)
    part('Open hopper light',COOL,-width/2,width/2,0,h,0,.014)
    for x in (-width/2+.015,width/2-.015):
        part('Hopper steel side stile',STEEL,x-.015,x+.015,0,h,.014,.046)
    for level in (.017,h*.28,h-.017):
        part('Hopper steel crossrail',STEEL,-width/2,width/2,level-.017,level+.017,.014,.046)


def fret(frame,u,width,lo,hi,pattern):
    """Two alternating rectilinear guard patterns can be read across the foyer glass."""
    span=hi-lo
    def bar(a,b,z0,z1):
        frame.flat('Foyer geometric steel guard',BRONZE,u,a*width,b*width,-.258,-.233,
                   lo+z0*span,lo+z1*span)
    thick=.014/width
    # Horizontal guards align across the five vertical lanes at the sill.
    bar(-.46,.46,.15,.17)
    bar(-.46,.46,.79,.81)
    if not frame.detail:return
    if pattern:
        for side in (-1,1):
            dx=side*.285
            bar(dx-thick,dx+thick,.17,.60)
            aa,bb=sorted((dx,dx-side*.17))
            bar(aa,bb,.57,.59)
            dx-=side*.17
            bar(dx-thick,dx+thick,.58,.79)
    else:
        for side in (-1,1):
            x=side*.335
            bar(x-thick,x+thick,.17,.80)


def install(frame,d):
    center=d['glass_center_u']
    axes=[center+off for off in d['column_offsets_m']]
    glass_low=d['window_sill_m'];glass_top=d['window_head_m']
    edges=[d['glass_edges_m'][0],*axes,d['glass_edges_m'][1]]
    for lane,(a,b) in enumerate(zip(edges,edges[1:])):
        u=(a+b)/2
        w=b-a
        frame.flat('Glazed lane recessed backing',OPEN,u,-w*.502,w*.502,-.55,-.50,glass_low,glass_top)
        for index in range(10):
            z0=glass_low+(glass_top-glass_low)*index/10
            z1=glass_low+(glass_top-glass_low)*(index+1)/10
            pane=AMBER if index in (2,3) else (SHADE if (index+lane)%3==0 else COOL)
            is_open=frame.detail and (lane,index) in ((4,6),(3,9))
            if is_open:
                tilted_pane(frame,u,w-.085,z0+.037,z1-.04)
            else:
                frame.flat('Foyer glazing',pane,u,-w/2+.018,w/2-.018,-.345,-.314,z0+.018,z1-.018)
                fret(frame,u,w,z0,z1,(lane+index)%2)
            frame.flat('Dark sill for each glazed light',BORDER,u,-w*.51,w*.51,-.38,-.185,z0-.025,z0+.023)
        for j in (-1,1):
            frame.flat('Foyer end casing',STEEL,u,j*(w/2-.025)-.025,j*(w/2-.025)+.025,-.37,-.218,glass_low,glass_top)
    for i,axis in enumerate(axes):
        frame.post('Foyer rounded column '+str(i+1),COLUMN,axis,-.09,glass_low-.035,glass_top+.07,d['column_radius_m'])
        if frame.detail:
            # The columns are articulated by fine horizontal stone courses.
            for z in [glass_low+(glass_top-glass_low)*k/5 for k in range(1,5)]:
                frame.post('Column course seam',BRONZE,axis,-.09,z-.006,z+.006,d['column_radius_m']+.0015)
    return edges[0],edges[-1]
