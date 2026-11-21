"""Three pale rectangular units and their offset round grilles visible in the 2005 view."""
import math
from shapely.geometry import Point,Polygon,box

CASE='Grey enamel casing'
METAL='Dark grille metal'
BLADES='Weathered fan blades'

def add_fixtures(face,builder,units,lod):
    for i,unit in enumerate(units):
        x0,z0,x1,z1=unit['front_xz'];cx,cz=unit['centre_xz']
        width=x1-x0;height=z1-z0;radius=min(.365*height,x1-cx-.035)
        n=24 if lod else 40
        ring=Point(cx,cz).buffer(radius,quad_segs=n//4)
        shell=box(x0,z0,x1,z1)
        name='Lawn unit '+str(i+1)
        face.prism(shell.difference(ring),.13,.43,CASE,name+' enamel housing')
        face.prism(ring,.140,.192,METAL,name+' dark recess')
        for blade in range(3):
            a=math.tau*blade/3
            pts=[]
            for r,offset in [(.12,-.24),(.78,-.14),(.91,.22),(.66,.57),(.18,.45)]:
                pts.append((cx+radius*r*math.cos(a+offset),cz+radius*r*math.sin(a+offset)))
            face.prism(Polygon(pts),.232,.251,BLADES,name+' blade silhouette')
        for j,r in enumerate([.46,.80,1.0]if lod else [.32,.51,.68,.83,.99]):
            band=Point(cx,cz).buffer(radius*r+.006,quad_segs=n//4).difference(Point(cx,cz).buffer(radius*r-.006,quad_segs=n//4))
            face.prism(band,.426,.444,METAL,name+' grille rings')
        for j in range(4 if lod else 8):
            a=math.tau*j/(4 if lod else 8)
            builder.tube([face.point(cx,cz,.452),face.point(cx+radius*math.cos(a),cz+radius*math.sin(a),.452)],
                         .006,METAL,5 if lod else 7,label=name+'/radial guard')
        face.prism(Point(cx,cz).buffer(radius*.15,quad_segs=n//4),.440,.466,CASE,name+' spindle cover')
        # Two short support rails connect the casing to the plaster pier.
        for x in (x0+width*.22,x1-width*.22):
            face.box(x,z0-.036,.061,.072,.38,.231,METAL,name+' support feet')
