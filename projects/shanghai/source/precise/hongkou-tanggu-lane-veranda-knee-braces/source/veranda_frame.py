"""A pair of diagonal timber braces and the gallery front recorded in the lane at 73 Tanggu Road."""
from math import hypot
from random import Random


def finish(rgb, rough=.91):
    return {'color': [((v/255+.055)/1.055)**2.4 for v in rgb], 'roughness':rough}


PALETTE={
    'oxblood paint':finish((135,73,66)), 'dark red joinery':finish((108,63,58)),
    'light paint':finish((157,88,77)), 'aged board':finish((116,85,75)),
    'back of timber':finish((84,64,58)), 'dark metal':finish((62,62,57),.56),
    'wood highlight':finish((153,101,87)), 'worn edge':finish((128,98,84)),
}


def board(b,l,r,front,back,lo,hi,material,label):
    b.box(((l+r)/2,(front+back)/2,(lo+hi)/2),(r-l,back-front,hi-lo),material,label=label)


def brace(b,side):
    start=(side*.069,1.184)
    end=(side*.717,1.792)
    x0,z0=start;x1,z1=end
    dx=x1-x0;dz=z1-z0;length=hypot(dx,dz);halfw=.051
    # Faces of this diagonal remain in the vertical plane behind the post and plate.
    nx=-dz/length*halfw;nz=dx/length*halfw
    poly=[(x0+nx,z0+nz),(x0-nx,z0-nz),(x1-nx,z1-nz),(x1+nx,z1+nz)]
    verts=[(x,y,z)for y in(-.04,.067)for x,z in poly]
    b.add(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'oxblood paint','diagonal knee brace '+('right'if side>0 else 'left'))
    # Two joins are fastened to the partly overlapping timbers.
    for ratio in (.165,.82):
        x=x0+dx*ratio;z=z0+dz*ratio
        b.tube([(x,-.043,z),(x,-.053,z)],.011,'dark metal',8,'brace fixing heads')


def paint_grain(b,lod):
    rng=Random(7312)
    verts=[];faces=[]
    for region,front,bounds in [('post',-.08,(-.081,.080,.025,1.746)),('fascia',-.087,(-1.47,1.46,1.889,1.966))]:
        l,r,lo,hi=bounds
        for i in range(52 if lod else 570):
            x=rng.uniform(l,r);z=rng.uniform(lo,hi);e=rng.uniform(.002,.007);g=rng.uniform(.0007,.0018)
            dx,dz=(g,e) if region=='post' else (e,g)
            i0=len(verts)
            verts.extend([(x-dx,front-.0007,z),(x+.2*dx,front-.0007,z-dz),(x+dx,front-.0007,z),(x,front-.0007,z+dz)])
            faces.append((i0,i0+1,i0+2,i0+3))
    b.add(verts,faces,'wood highlight','paint wear on upright and fascia')


def add_building(b,lod=False):
    extent=1.50
    board(b,-.09,.09,-.08,.104,0,1.78,'oxblood paint','central square post')
    for side in (-1,1):brace(b,side)
    board(b,-extent,extent,-.077,.148,1.751,1.882,'dark red joinery','continuous beam under balcony')
    board(b,-extent,extent,-.087,.151,1.882,1.982,'oxblood paint','red painted fascia')
    board(b,-extent,extent,-.108,.159,1.982,2.015,'light paint','slender front sill strip')
    for k in range(-4,5):
        x=k*.332
        board(b,x-.039,x+.039,.09,1.05,1.806,1.982,'back of timber','soffit joist '+str(k+5))
    for i in range(14):
        left=-extent+i*(extent*2/14);r=left+extent*2/14-.003
        board(b,left,r,.085,1.06,1.981,2.025,'aged board','floorboards of upper gallery')
    # The central joint separates two neighbouring frontage finishes. The left panel is plain.
    board(b,-extent,.061,-.003,.043,2.017,2.473,'dark red joinery','back of left plain panel')
    for i in range(10):
        l=-extent+.156*i
        board(b,l+.002,l+.154,-.017,.014,2.041,2.448,'aged board','left vertical boarding')
    board(b,.061,extent,-.009,.049,2.017,2.473,'dark red joinery','recess of patterned parapet')
    for lo,hi in [(2.020,2.045),(2.409,2.433),(2.457,2.486)]:
        board(b,.059,extent,-.047,.051,lo,hi,'light paint' if lo!=2.409 else 'oxblood paint','three horizontal borders to infill')
    # Slim leaves of the right-hand field are interrupted by the staggered short horizontals.
    field_left=.096;field_right=extent-.025
    step=(field_right-field_left)/14
    for i in range(14):
        x0=field_left+step*i
        board(b,x0,x0+.022,-.04,-.004,2.051,2.403,'oxblood paint','vertical parapet slips')
        if i%2:
            board(b,x0+.021,x0+step,-.04,-.004,2.173,2.194,'oxblood paint','staggered inlay cross pieces')
        else:
            board(b,x0+.021,x0+step,-.04,-.004,2.282,2.304,'oxblood paint','staggered inlay cross pieces')
    for x in (.064,extent-.014):
        board(b,x-.016,x+.016,-.055,.024,2.019,2.491,'dark red joinery','end stiles of relief panel')
    paint_grain(b,lod)
