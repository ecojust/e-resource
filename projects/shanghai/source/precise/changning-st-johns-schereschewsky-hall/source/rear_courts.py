"""Roof study of the two adjoining service courts and of the short central link."""
from shapely.geometry import Polygon,box
def folded_roof(b,points,faces,m,label):
    n=len(points);top=[tuple(f) for f in faces]
    all_faces=top+[tuple(v+n for v in reversed(f))for f in top]
    edges={}
    for f in top:
        for i,j in zip(f,f[1:]+f[:1]):
            if (j,i) in edges:del edges[j,i]
            else:edges[i,j]=True
    all_faces.extend((j,i,i+n,j+n)for i,j in edges)
    b.add(points+[(x,y,z-.12)for x,y,z in points],all_faces,m,label)
def link_roof(b,arch,west,east,tip,ridge,joining):
    """A north–south linked roof, with measured unequal inner eave coordinates."""
    x0,y0=west[0];x1,y1=east[0];x3,y3=west[1];x2,y2=east[1]
    h=8.42;peak=10.70
    points=[(x0,y0,h),(x1,y1,h),(x2,y2,h),(x3,y3,h),(ridge,joining,peak),(ridge,tip,peak)]
    folded_roof(b,points,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)],arch.TILE,'Northern courts / '+str(ridge)+' longitudinal roof')
    b.tube([(ridge,joining,peak+.034),(ridge,tip,peak+.034)],.063,arch.TILE,8,'Northern courts/linked ridge')
def add(b,arch):
    # Ground-level wall offsets here are estimates. Aerials resolve roof edges,
    # while neither river windows nor small-court doors have a registered elevation.
    outer=21.20;rear=78.50;south=54.56;north=69.45;eave=8.42
    link_roof(b,arch,[(-outer,south),(-outer,north)],[(-12.4,south),(-12.8,north)],north-1.0,-16.7,south+1.22)
    link_roof(b,arch,[(10.8,south),(11.78,north)],[(outer,south),(outer,north)],north-1.0,16.30,south+1.22)
    link_roof(b,arch,[(-6.5,50.10),(-6.8,65.98)],[(3.8,50.10),(3.6,66.14)],64.03,-1.90,50.14)
    wall_a=[(-20.27,south-.03),(-12.82,south-.03),(-13.15,north+.04),(-20.27,north+.04)]
    wall_b=[(11.20,south-.05),(20.27,south-.05),(20.27,north+.07),(12.15,north+.07)]
    wall_c=[(-6.10,south-.17),(3.42,south-.17),(3.23,65.70),(-6.42,65.55)]
    for label,path in [('west wing',wall_a),('east wing',wall_b),('short middle wing',wall_c)]:
        poly=Polygon(path);shell=poly.difference(poly.buffer(-.25,join_style=2))
        b.plan_prism(shell,0,eave-.025,arch.BRICK,'Northern court/'+label+' conditional outer shell')
    # A continuous open throat passes between the end of the short wing and the
    # inner eave of the riverside range; no high wall closes the two small yards.
    back=box(-20.27,north+.44,20.27,rear-.77)
    b.plan_prism(back.difference(back.buffer(-.25,join_style=2)),0,eave-.025,arch.BRICK,'Riverside range / conditional masonry envelope')
    ry=74.52;ph=10.70;points=[(-outer,north,eave),(outer,north,eave),(outer,rear,eave),(-outer,rear,eave),(-outer+2.21,ry,ph),(outer-2.21,ry,ph)]
    folded_roof(b,points,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],arch.TILE,'Riverside range / hipped roof')
    b.tube([(-outer+2.21,ry,ph+.052),(outer-2.21,ry,ph+.052)],.07,arch.TILE,8,'Riverside range / axial ridge')
    ground=box(-13.2,south-.12,12.2,north+.55)
    b.plan_prism(ground,-.095,-.036,'court pebble paving','Rear courts / two yards and connecting passage')
