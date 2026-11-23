"""The tall paired lights, clearstory rails, and fired-clay panels of the garden facade."""
from shapely.geometry import box
from materials import BRICK,FRAME,GLASS,RECESS,STONE
from house_layout import D,FIT,U,Z

def registered_openings():
    openings={}
    for group in ['left','middle','right']:
        a,_,t=FIT['vertices']['south_'+group+'_sash_TL'];b,_,lo=FIT['vertices']['south_'+group+'_sash_BR']
        openings[group]=box(U(a),Z(lo),U(b),Z(t))
    return openings

def sash(f,hole,name,columns=2,transoms=(.16,.33),sill=True,depth_scale=1.):
    a,z,b,top=hole.bounds
    f.solid(hole,-.174*depth_scale,-.162*depth_scale,RECESS,name+' | window reveal lining')
    inner=hole.buffer(-.046,join_style=2)
    f.solid(inner,-.160*depth_scale,-.148*depth_scale,GLASS,name+' | glazing')
    f.solid(hole.difference(inner),-.15*depth_scale,-.072*depth_scale,FRAME,name+' | timber casement')
    for j in range(1,columns):
        x=a+(b-a)*j/columns;r=.026 if columns==4 and j==2 else .016
        f.rect(x-r,x+r,z+.028,top-.026,-.148*depth_scale,(-.074 if r>.02 else -.102)*depth_scale,FRAME,name+' | glazing upright')
    for frac in transoms:
        h=top-(top-z)*frac
        f.rect(a+.035,b-.035,h-.016,h+.016,-.147*depth_scale,-.099*depth_scale,FRAME,name+' | upper glazing rail')
    if sill:f.rect(a-.042,b+.042,z-.088,z+.006,-.017,.079,BRICK,name+' | single brick sill')

def garden_window_group(f,holes):
    for name,hole in holes.items():
        sash(f,hole,'south upper | '+name,4 if name=='middle' else 2,depth_scale=.39)
    # Both original winter photographs show masonry only between the openings, recessed at the soffit and sill.
    for before,after in [('left','middle'),('middle','right')]:
        a,z,b,head=holes[before].bounds;c,lo,d,top=holes[after].bounds
        f.rect(b,c,z+(head-z)*.13,head-(head-z)*.17,-.006,.021,BRICK,'south upper | brick pier between lights')
