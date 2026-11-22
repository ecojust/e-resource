"""One recessed garden balcony at Fushi Gardens, Shanghai.

The broken-line lintel and 18 double-curved railing heads are separate from
the rear wall, so the rail is genuinely open from either side.
"""
from math import cos,sin,pi
from shapely.geometry import box,Polygon,LineString
from shapely.ops import unary_union

def finish(rgb, rough=.88, metal=0):
    def channel(x):
        v=x/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return dict(color=[channel(v) for v in rgb],roughness=rough,metallic=metal)
PALETTE={'roughcast':finish((207,204,181)), 'soffit plaster':finish((172,164,141)),
 'window render':finish((188,179,157)), 'cast sill':finish((200,196,171)),
 'rail iron':finish((65,63,54),.62,.23),'sash joinery':finish((79,70,58),.77),
 'shadowed glass':finish((105,117,116),.26,.17),'gallery floor':finish((150,143,127))}
WIDTH=1.79
ARCH=[(-WIDTH,2.22),(-1.29,2.36),(-.77,2.414),(.68,2.414),(1.36,2.33),(WIDTH,2.22)]
CENTRES=[(-WIDTH+.077)+i*(2*WIDTH-.154)/17 for i in range(18)]

def add_building(b,lod=False):
    def panel(label,shape,y0,y1,material):
        b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),material,label)
    def bar(label,x0,x1,z0,z1,y0,y1,material):
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)
    outer=box(-2.03,-.115,2.03,2.83)
    aperture=Polygon([(-WIDTH,.12),(WIDTH,.12)]+list(reversed(ARCH)))
    panel('front render and shallow polygonal arch',outer.difference(aperture),0,.234,'roughcast')
    for i,((x,z),(x1,z1)) in enumerate(zip(ARCH,ARCH[1:])):
        polygon=Polygon([(x,z),(x1,z1),(x1,z1+.016),(x,z+.016)])
        panel('soffit return '+str(i+1),polygon,.022,.251,'soffit plaster')
    bar('upper floor slab',-2.03,2.03,.039,.114,.225,1.31,'gallery floor')
    bar('stone threshold and drip',-1.86,1.86,.080,.136,-.055,.237,'cast sill')
    bar('gallery ceiling',-2.025,2.025,2.625,2.826,.232,1.44,'soffit plaster')
    for x in (-2.028,1.79):
        bar('side reveal '+str(round(x)),x,x+.236,.113,2.627,.23,1.32,'window render')
    openings=[box(x-.615,.117,x+.615,2.035) for x in (-.845,.875)]
    panel('back wall behind deep balcony',box(-1.805,.103,1.805,2.658).difference(unary_union(openings)),1.302,1.477,'window render')
    for idx,x in enumerate((-.845,.875)):
        area=openings[idx]
        panel('rear frame '+str(idx),area.difference(box(x-.561,.161,x+.561,1.982)),1.34,1.465,'sash joinery')
        bar('rear glass '+str(idx),x-.568,x+.568,.151,1.989,1.413,1.45,'shadowed glass')
        for j,dx in enumerate((-.281,0,.281)):
            wid=.025 if j==1 else .014
            bar('vertical window bar '+str(idx)+' '+str(j),x+dx-wid,x+dx+wid,.15,1.99,1.323,1.439,'sash joinery')
        for j,z in enumerate((.67,1.11,1.582)):
            bar('horizontal window bar '+str(idx)+' '+str(j),x-.562,x+.562,z-.014,z+.014,1.318,1.438,'sash joinery')
    # Square pins register the guard behind the threshold, with visible ends.
    for j,z in enumerate((.205,.888,1.075)):
        bar('continuous rail '+str(j),-1.79,1.79,z-.012,z+.012,.092,.129,'rail iron')
    bar('wide handrail',-1.803,1.803,1.075,1.113,.076,.142,'rail iron')
    half=(CENTRES[1]-CENTRES[0])/2
    for i,c in enumerate(CENTRES):
        bar('upright '+str(i+1),c-.009,c+.009,.137,.93,.093,.112,'rail iron')
        for sign in (-1,1):
            # Each frond has a low central spring and curls out toward the top.
            n=3 if lod else 10
            arc=[(c+sign*half*(1-cos((pi/2)*k/n)),.92+.152*sin((pi/2)*k/n)) for k in range(n+1)]
            panel('fork rail '+str(i+1),LineString(arc).buffer(.0075,cap_style=2,join_style=2),.093,.113,'rail iron')
        if not lod:
            for z in (.205,.888):
                bar('weld lug '+str(i+1),c-.014,c+.014,z-.014,z+.014,.087,.105,'rail iron')
