"""Four recorded balcony levels on the courtyard elevation at 1230 Middle Huaihai Road.

X increases to photographic right, Z is measured from the court walk. The
local leading face is y=0. Place it at the survey's rail_face_y in assembly.
"""
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

CAST = 'Guangming | grey precast balcony'
DRIP = 'Guangming | green painted balcony drip'
BRICK = 'Guangming | warm courtyard brick'
FRAME = 'Guangming | charcoal painted sash'
SILVER = 'Guangming | pale metal enclosed sash'
GLASS = 'Guangming | shaded balcony glass'
IRON = 'Guangming | dark iron railing'
PALETTE = {
    CAST: {'color':[.58,.56,.52], 'roughness':.88},
    DRIP: {'color':[.24,.39,.34], 'roughness':.78},
    BRICK: {'color':[.56,.33,.20], 'roughness':.9},
    FRAME: {'color':[.16,.17,.16], 'roughness':.65},
    SILVER: {'color':[.61,.64,.62], 'metallic':.25, 'roughness':.57},
    GLASS: {'color':[.25,.31,.32], 'metallic':.10, 'roughness':.34},
    IRON: {'color':[.14,.14,.12], 'metallic':.26, 'roughness':.66}
}
WIDTH=2.82
LEFT=4.10
FRONT=-.192
DEPTH=1.26

def rect(l,b,r,t):
    return [(l,b),(r,b),(r,t),(l,t)]

def piece(builder,outline,holes,near,far,mat,label):
    if far<=near:raise ValueError('Positive material thickness required')
    poly=orient(Polygon(outline,holes),sign=1)
    vertices=[];lookup={};faces=[]
    def vert(x,z,y):
        k=(float(x),float(y),float(z))
        if k not in lookup:lookup[k]=len(vertices);vertices.append(k)
        return lookup[k]
    for tri in constrained_delaunay_triangles(poly).geoms:
        ring=list(orient(tri,sign=1).exterior.coords)[:3]
        faces += [tuple(vert(x,z,near) for x,z in ring),tuple(vert(x,z,far) for x,z in reversed(ring))]
    for ring in (poly.exterior,*poly.interiors):
        for (x,z),(u,v) in zip(ring.coords,list(ring.coords)[1:]):
            a,b,c,d=vert(x,z,near),vert(u,v,near),vert(u,v,far),vert(x,z,far)
            faces += [(a,c,b),(a,d,c)]
    builder.add(vertices,faces,mat,'1230 rear | '+label)

def add_balconies(builder,lod=False,*,left=LEFT,width=WIDTH,front_y=FRONT,depth=DEPTH,period=2016):
    if period not in (2013,2016):raise ValueError('Expected a 2013 or 2016 facade')
    def xs(u):return left+u*width
    def slab(a,b,low,high,near,far,mat,label):
        piece(builder,rect(xs(a),low,xs(b),high),[],front_y+near,front_y+far,mat,label)
    def band(openings,bottom,top,near,far,mat,label,a=0,b=1):
        outer=rect(xs(a),bottom,xs(b),top)
        holes=[rect(xs(l),z0,xs(r),z1) for l,z0,r,z1 in openings]
        piece(builder,outer,holes,front_y+near,front_y+far,mat,label)
    def glazing(a,b,z0,z1,y,cols,head,mat,label):
        # Each pane occupies its own reveal behind the frame.
        bar=.035;edge=.047;step=(xs(b)-xs(a)-2*edge)/cols
        levels=[z0+edge]+([head] if z0+edge<head<z1-edge else [])+[z1-edge]
        holes=[]
        for c in range(cols):
            x0=xs(a)+edge+c*step+(bar/2 if c else 0)
            x1=xs(a)+edge+(c+1)*step-(bar/2 if c+1<cols else 0)
            for n,(lo,hi) in enumerate(zip(levels,levels[1:])):
                lo+=bar/2 if n else 0
                hi-=bar/2 if n+1<len(levels)-1 else 0
                holes.append(rect(x0,lo,x1,hi))
                piece(builder,rect(x0,lo,x1,hi),[],front_y+y+.025,front_y+y+.045,GLASS,label+' panes')
        piece(builder,rect(xs(a),z0,xs(b),z1),holes,front_y+y,front_y+y+.066,mat,label+' sash')
    # The concrete panels and independent floor slabs have measured horizontal voids.
    levels=[
        (.86,1.00,1.89,1.18,1.66,[.099,.186,.276,.369,.459,.552,.639,.725,.814,.903]),
        (3.86,3.99,4.90,4.17,4.68,[.105,.194,.282,.373,.458,.545,.641,.729,.812,.907]),
        (6.86,7.02,7.98,7.18,7.80,[.544,.636,.728,.811,.905])]
    for i,(soffit,floor,cap,sill,head,axes) in enumerate(levels,1):
        label=f'L{i} '
        slab(-.004,1.004,soffit,floor,.003,depth+.035,CAST,label+'slab')
        half=[.012,.012,.012][i-1]
        band([(u-half,sill,u+half,head) for u in axes],floor,cap,0,.125,CAST,label+'cast slotted front')
        if i==2:slab(-.009,1.009,soffit-.005,floor+.006,-.028,.004,DRIP,label+'green drip')
        for a,b in [(0,.042),(.958,1)]:
            slab(a,b,floor,cap,.125,depth,CAST,label+'side parapet')
    # Behind the rail of level 1 both heads are visible in Gao's picture;
    # the lower portions remain obscured. The openings are separate from the
    # doorway marked 1230, which belongs to the adjoining street wall.
    backs=[
        (1,1.00,3.86,[(.070,.338,1.1,3.12,2,2.89),(.470,.646,1.1,3.12,1,2.89)]),
        (2,3.99,6.86,[(.330,.661,4.10,6.21,2,5.91),(.755,.985,4.07,5.95,1,5.73)])]
    for idx,lo,hi,openings in backs:
        label=f'L{idx} recessed '
        band([(a,z0,b,z1)for a,b,z0,z1,_,_ in openings],lo,hi,depth,depth+.13,BRICK,label+'brick back')
        for a,b,z0,z1,cols,tr in openings:glazing(a,b,z0,z1,depth+.044,cols,tr,FRAME,label+'opening')
    # The high dark guard is present above the lower concrete plinth in Gao.
    if period==2013:
        posts=range(0,17,2 if lod else 1)
        for i in posts:
            x=.016+i*.060
            slab(x-.004,x+.004,1.89,2.16,.008,.034,IRON,'L1 added iron guard')
        slab(.01,.983,2.14,2.17,.005,.043,IRON,'L1 metal handrail')
    else:
        # On 20 January 2016 the near-right portion of the ground bay is glazed.
        # The grille runs left into the neighbour; only the section in this bay is included.
        glazing(.56,.982,1.90,3.60,.052,2,3.31,FRAME,'L1 later right screen')
        for i in range(0,13,2 if lod else 1):
            u=.012+i*.044
            slab(u,u+.006,1.90,3.60,-.018,.004,IRON,'L1 later grille bars')
        for z in [2.05,2.83,3.55]:slab(.008,.551,z,z+.027,-.023,.015,IRON,'L1 later grille rails')
    if period==2016:
        # Masa image 25 shows the near-left half screened and the right half open.
        glazing(.035,.497,7.98,10.18,.072,3,9.85,SILVER,'L3 left enclosure')
        slab(.492,.505,7.98,10.18,.075,depth,CAST,'L3 divider return')
        slab(.5,.967,7.98,8.01,.035,.085,SILVER,'L3 right low rail')
        for i in range(4):slab(.51+i*.145,.519+i*.145,7.99,8.23,.037,.063,SILVER,'L3 open guard')
        slab(.503,.973,8.20,8.23,.034,.072,SILVER,'L3 open handrail')
        slab(0,1,10.09,10.28,0,depth+.02,CAST,'L4 slab with exposed underside')
        slab(.012,.988,10.28,10.94,.006,.13,CAST,'L4 solid lower front')
        for k in range(3):slab(.025,.984,10.96+k*.13,10.983+k*.13,.018,.054,SILVER,'L4 horizontal guard')
        for u in [.025,.253,.50,.74,.976]:slab(u,u+.013,10.94,11.29,.021,.058,SILVER,'L4 thin uprights')
        glazing(.06,.480,11.65,12.86,.105,2,12.52,SILVER,'L4 left frame')
        glazing(.48,.94,10.57,12.57,depth+.015,2,12.26,FRAME,'L4 recessed frame')
        slab(-.025,1.025,12.84,12.99,-.03,depth+.08,CAST,'L4 soffit under roofline')
