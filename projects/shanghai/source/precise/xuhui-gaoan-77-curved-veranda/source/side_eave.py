"""Six timber brackets and the exposed brick chimney breast on the west-facing side."""
from math import ceil
from shapely.geometry import Polygon
from materials import BRICK, DARK, JOINT, STONE

# Along the west wall, s increases from the rear toward the southern garden facade.
# The dimensions are measured between supports, not between assumed property corners.
SADDLES = (0., .14880, .65010, .76717, .88276, 1.)
REFERENCE_SPAN = 6.88234

def add_side_eave(side, lod=False, layout=None):
    """Place on an outward-facing Facade. Lengths and elevations are local metres.

    first_s and last_s mark the centres of the two end brackets. seat_z is the
    centreline of the masonry saddles. eave_z is the underside of the outer
    eave where the timber reaches it. The host supplies the roof, chimney above
    the roof, wall shell, windows and window sills.
    """
    cfg=layout or {}
    start=cfg.get('first_s',0.)
    end=cfg.get('last_s',start+REFERENCE_SPAN)
    band_z=cfg.get('seat_z',9.55)
    soffit=cfg.get('eave_z',band_z+1.31)
    ground=cfg.get('ground_z',0.)
    scale=(end-start)/REFERENCE_SPAN
    if scale<=0 or soffit<=band_z+.35 or band_z<=ground+2.5:
        raise ValueError('The side-eave span and two absolute elevations must be ordered.')
    def s(x):return start+scale*x
    def rectangle(a,b,z0,z1,back,front,mat,name):
        side.rect(s(a),s(b),z0,z1,back,front,mat,name)

    def brickwork(a,b,z0,z1,depth,name,soldier=False):
        # The joints come from the brick course period observed on the 2013 photo.
        # In the coarse mesh the long chimney panels retain taller rows.
        width=(b-a)*scale
        course=.0655 if not lod else .131
        rows=1 if soldier else max(1,round((z1-z0)/course))
        brick_width=(.068 if soldier else .217) * (1.55 if lod else 1.)
        rectangle(a,b,z0,z1,.005,depth-.008,JOINT,name+' bed')
        dz=(z1-z0)/rows
        for row in range(rows):
            offset=0. if soldier or row%2==0 else -brick_width/2
            z=z0+row*dz
            n=ceil((width-offset)/brick_width)
            for col in range(n):
                left=max(0.,offset+col*brick_width)+.0025
                right=min(width,offset+(col+1)*brick_width)-.0025
                if right>left:
                    side.rect(s(a)+left,s(a)+right,z+.003,z+dz-.003,
                              depth-.008,depth,BRICK,name+' faces')

    # Under the red soldier band, four short brick tongues are visible on the two views.
    xs=[REFERENCE_SPAN*r for r in SADDLES]
    cover=.155
    exposed=[(xs[0]+cover,xs[1]-cover),(xs[1]+cover,2.42),
             (3.84,xs[2]-cover)]+[(xs[i]+cover,xs[i+1]-cover) for i in (2,3,4)]
    for i,(left,right) in enumerate(exposed):
        brickwork(left,right,band_z-.17,band_z+.11,.052,'Eave soldier strip '+str(i+1),True)
    for i,x in enumerate(xs):
        tag='Side eave support '+str(i+1)
        if i in (1,2,3,4):
            rectangle(x-.077,x+.077,band_z-.305,band_z-.16,.006,.042,BRICK,tag+' brick tab')
        rectangle(x-.14,x+.14,band_z-.175,band_z+.095,.008,.160,STONE,tag+' stone block')
        rectangle(x-.161,x+.161,band_z+.095,band_z+.151,.009,.189,STONE,tag+' stone cap')
        rectangle(x-.127,x+.127,band_z+.151,band_z+.195,.010,.166,STONE,tag+' cap lip')
        base=band_z+.195
        nose=cfg.get('eave_projection',.70)
        # Photographs 26 and 39 show an open triangle under the horizontal head.
        # The sloping knee meets the underside of the head with a level bearing cut.
        head_bottom=soffit-.17
        half=.090
        knee=Polygon([(.027,base),(.167,base),(nose,head_bottom),(nose-.19,head_bottom)])
        side.b.prism(knee,-s(x)-half,-s(x)+half,
                     lambda outward,z,minus_u:side.point(-minus_u,-outward,z),
                     DARK,side.label+' | '+tag+' raking knee')
        rectangle(x-half/scale,x+half/scale,head_bottom,soffit,.018,nose,
                  DARK,tag+' horizontal head')
        # Thin red brick backing is exposed under the horizontal head in the oblique views.
        if i>0:
            brickwork(x-.105,x+.105,base,head_bottom,.022,tag+' backing strip')
    # At the stone shoulder, the upper flue steps out on its rear-facing side.
    # The narrower lower breast descends behind the white plinth.
    # The measured upper and lower edges of the stone belt share their datum with the six saddles.
    belt_top=cfg.get('chimney_waist_z',band_z-4.653)
    belt_bottom=belt_top-.323
    base=cfg.get('chimney_base_z',ground+.54)
    brickwork(2.91,3.80,base,belt_bottom,.105,'Side chimney lower breast')
    rectangle(2.51,3.86,belt_bottom,belt_top,.010,.158,STONE,'Side chimney stone shoulder')
    # Under the projecting end only, the soffit turns back to the narrower brick shaft.
    cove=Polygon([(s(2.53),belt_bottom),(s(2.922),belt_bottom),(s(2.922),belt_bottom-.275),
                  (s(2.815),belt_bottom-.275),(s(2.815),belt_bottom-.228),(s(2.755),belt_bottom-.219),
                  (s(2.685),belt_bottom-.193),(s(2.627),belt_bottom-.154),(s(2.580),belt_bottom-.107),
                  (s(2.546),belt_bottom-.054)])
    side.solid(cove,.011,.113,STONE,'Side chimney corbel under projecting end')
    brickwork(2.55,3.80,belt_top,band_z+.27,.135,'Side chimney upper breast')
    rectangle(2.12,3.81,band_z+.27,band_z+.55,.010,.160,STONE,'Side chimney upper stone belt')
    brickwork(2.12,3.80,band_z+.55,soffit-.025,.134,'Side chimney top panel')
