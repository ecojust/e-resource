"""Architectural fragment of the upper paired round-headed sash at 16 Anding Fang."""
from math import sin,cos,pi,sqrt
from random import Random
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

def surface(rgb,roughness,metal=0.):
    def linear(n):
        v=n/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return {'color':[linear(x)for x in rgb],'roughness':roughness,'metallic':metal}
PALETTE={'roughcast':surface((186,179,164),.95),'dark render fleck':surface((151,145,130),1),
         'pale render fleck':surface((214,206,188),1),'window reveal':surface((133,128,115),.92),
         'metal rails':surface((68,70,64),.72,.3),'window glass':surface((119,132,130),.25,.12),
         'cut sill stone':surface((189,181,161),.83),'scalloped fascia':surface((202,193,173),.80),
         'sill shadow':surface((154,148,133),.89)}
CENTRES=(-.683,.683)
R=.485
SPRING=1.385
BOTTOM=.390
def head(cx,r,bottom,step):
    return Polygon([(cx-r,bottom),(cx+r,bottom)]+[(cx+r*cos(pi*i/step),SPRING+r*sin(pi*i/step))for i in range(step+1)])
def add_building(b,lod=False):
    n=16 if lod else 48
    def face(label,poly,front,back,mat):
        b.prism(poly,-back,-front,lambda u,z,d:(u,-d,z),mat,label)
    outside=box(-1.45,0,1.45,2.105);holes=[head(x,R,BOTTOM,n) for x in CENTRES]
    wall=outside.difference(unary_union(holes))
    face('pebbledash wall with two full-depth openings',wall,0,.22,'roughcast')
    for c,side in zip(CENTRES,('left','right')):
        outer=head(c,R,BOTTOM,n);inner=head(c,R-.038,BOTTOM+.036,n)
        face(side+' shadow on reveal',outer.difference(head(c,R-.012,BOTTOM+.012,n)),.044,.15,'window reveal')
        face(side+' round-headed outer sash',outer.difference(inner),.083,.134,'metal rails')
        face(side+' grey glass',inner,.15,.159,'window glass')
        for k in range(1,4):
            x=c-R+2*R*k/4
            poly=box(x-.010,BOTTOM+.020,x+.010,SPRING+R).intersection(inner)
            face(side+' glazing bar '+str(k),poly,.093,.124,'metal rails')
        for k,(z,thick) in enumerate([(.66,.012),(.927,.012),(1.202,.025),(1.484,.011)]):
            rail=box(c-R,z-thick,c+R,z+thick).intersection(inner)
            face(side+' transom '+str(k+1),rail,.081 if k==2 else .091,.124,'metal rails')
    face('sill continuous upper lip',box(-1.267,.324,1.267,.398),-.191,.014,'cut sill stone')
    face('sill deep back band',box(-1.247,.159,1.247,.337),-.121,.018,'sill shadow')
    face('bottom stone edge',box(-1.256,.141,1.256,.175),-.161,.018,'cut sill stone')
    low=.203; pitch=.1245;count=20;left=-pitch*count/2
    # Each shallow semicircle has its own low point and joins the next at the shoulder.
    outline=[(left,.333),(left,low+.042)]
    steps=5 if lod else 13
    for j in range(count):
        for k in range(1,steps+1):
            t=k/steps;outline.append((left+(j+t)*pitch,low+.042-.043*sin(pi*t)))
    outline.append((left+count*pitch,.333));face('continuous scalloped sill fascia',Polygon(outline),-.16,-.120,'scalloped fascia')
    # Sparse relief flecks express the visible roughcast. Irregular placement and colour
    # are reconstructed finishes rather than copied pixels from the study photograph.
    rng=Random(28416);buckets={k:([],[])for k in ('dark render fleck','pale render fleck')}
    for i in range(650 if lod else 3300):
        x=rng.uniform(-1.448,1.448);z=rng.uniform(.008,2.1)
        if any(abs(x-c)<R+.012 and z>=BOTTOM-.012 and (z<SPRING+.004 or (x-c)**2+(z-SPRING)**2<(R+.013)**2)for c in CENTRES):continue
        radius=rng.uniform(.0022,.0052);tone='dark render fleck' if i%3 else 'pale render fleck';vs,fs=buckets[tone];at=len(vs)
        vs.extend([(x-radius,-.0002,z-radius*.63),(x+radius*.8,-.0002,z-radius*.83),(x+radius*.22,-.0002,z+radius),(x-radius*.12,-.0024,z+radius*.11)])
        fs.extend([(at,at+1,at+3),(at+1,at+2,at+3),(at+2,at,at+3)])
    for mat,(vs,fs)in buckets.items():b.add(vs,fs,mat,'aggregate relief '+mat)
