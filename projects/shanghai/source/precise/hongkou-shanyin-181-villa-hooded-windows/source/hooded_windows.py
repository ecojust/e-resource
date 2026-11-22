"""The two middle upper-storey windows of the pink villa behind 181 Shanyin Road."""
from math import sin, cos, pi


def finish(rgb, rough=.9):
    return {'color': [((v/255+.055)/1.055)**2.4 for v in rgb], 'roughness':rough}


PALETTE={
    'pink plaster':finish((196,139,139)), 'window reveal':finish((148,119,113)),
    'hood stone':finish((141,139,130)), 'stone edging':finish((162,157,143)),
    'stone shadow':finish((123,122,115)), 'painted joinery':finish((198,198,178)),
    'clear pane':finish((98,124,123),.31), 'shaded transom':finish((81,96,92),.36),
    'eave underside':finish((114,108,104)), 'roof edge':finish((127,102,99)),
    'stone grain':finish((153,147,137)), 'rose grain':finish((184,130,129)),
    'tile body':finish((143,102,96)), 'weathered tile':finish((145,113,107)),
}
AXES=(-1.075,1.075)
OPEN_HALF=.43
BOTTOM=.344
TOP=1.617


def block(b,l,r,f,back,z0,z1,mat,label):
    b.box(((l+r)/2,(f+back)/2,(z0+z1)/2),(r-l,back-f,z1-z0),mat,label=label)


def course(b,x,z,width,depth,height,mat,name):
    block(b,x-width/2,x+width/2,-depth,.12,z,z+height,mat,name)


def raked_cap(b,x,lod,name):
    # Horizontal mouldings remain square on their returns; the supporting brackets taper.
    profile=[(.0,.052,1.04,.112),(.052,.096,1.077,.13),(.096,.129,1.117,.168),
             (.129,.168,1.152,.17),(.168,.196,1.20,.20)]
    for i,(l,r,span,depth) in enumerate(profile):
        course(b,x,1.625+l,span,depth,r-l,'stone edging' if i in (1,4) else 'hood stone',name+' hood course '+str(i+1))
    for sign in (-1,1):
        u=x+.473*sign
        # Broad at the stone hood, the stop contracts against the vertical surround below it.
        for j,(za,zb,span,deep) in enumerate([ (1.462,1.496,.083,.101),
                                              (1.496,1.545,.101,.126),
                                              (1.545,1.589,.127,.137),
                                              (1.589,1.628,.145,.157)]):
            course(b,u,za,span,deep,zb-za,'hood stone',name+f' hood stop {sign} step {j+1}')


def casement(b,x,name):
    block(b,x-OPEN_HALF,x+OPEN_HALF,.157,.166,BOTTOM,TOP,'clear pane',name+' recessed casement glass')
    block(b,x-.384,x+.384,.145,.157,1.224,1.548,'shaded transom',name+' upper glass')
    for u in (-.414,.414):
        block(b,x+u-.018,x+u+.018,.091,.150,BOTTOM,TOP,'painted joinery',name+' outer upright')
    for za,zb in [(BOTTOM,.39),(1.175,1.228),(1.552,1.607)]:
        block(b,x-.43,x+.43,.092,.151,za,zb,'painted joinery',name+' horizontal frame')
    for side in (-1,1):
        u=x+.198*side
        block(b,u-.012,u+.012,.102,.147,.385,1.174,'painted joinery',name+' lower glazing bar')
    block(b,x-.019,x+.019,.090,.150,.385,1.174,'painted joinery',name+' meeting stiles')
    # The upper light is horizontal in the source. The utility wire crosses the lower sash.
    block(b,x-.397,x+.397,.108,.147,1.375,1.398,'painted joinery',name+' upper horizontal glazing bar')


def mineral_flecks(b,lod):
    # Scatter slight changes of aggregate colour on the stone head, sill and pink wall.
    # Neither a street photograph nor surrounding shopfronts are included in the model.
    from random import Random
    rng=Random(5181)
    for material,regions in [
        ('stone grain',[(x-.554,x+.554,-.168,1.727,1.749) for x in AXES]
                      +[(x-.528,x+.528,-.135,.301,.327) for x in AXES]),
        ('rose grain',[(-.49,.49,0,.113,1.945),(-1.87,-1.66,0,.032,1.99),
                       (1.66,1.87,0,.032,1.99)])]:
        vertices=[];faces=[]
        for l,r,y,lo,hi in regions:
            for i in range(45 if lod else 440):
                x=rng.uniform(l,r);z=rng.uniform(lo,hi);h=rng.uniform(.0014,.0046)
                idx=len(vertices)
                vertices.extend([(x-h,y-.0005,z),(x+h*.32,y-.0005,z-h*.65),
                                 (x+h,y-.0005,z+h*.16),(x-h*.4,y-.0005,z+h*.70)])
                faces.extend([(idx,idx+1,idx+2),(idx,idx+2,idx+3)])
        b.add(vertices,faces,material,material+' on facade surfaces')


def add_building(b,lod=False):
    limit=1.885
    block(b,-limit,limit,0,.26,.022,BOTTOM,'pink plaster','lower plaster spandrel')
    block(b,-limit,limit,0,.26,TOP,2.060,'pink plaster','plaster under eave')
    for i,(l,r) in enumerate([(-limit,AXES[0]-OPEN_HALF),(AXES[0]+OPEN_HALF,AXES[1]-OPEN_HALF),
                              (AXES[1]+OPEN_HALF,limit)]):
        block(b,l,r,0,.26,BOTTOM,TOP,'pink plaster','plaster wall pier '+str(i+1))
    for i,x in enumerate(AXES):
        name=('first' if i==0 else 'second')+' middle window'
        casement(b,x,name)
        for side in (-1,1):
            u=x+side*.472
            block(b,u-.047,u+.047,-.066,.142,.320,1.653,'hood stone',name+' stone surround')
            u=x+side*.421
            block(b,u-.011,u+.011,-.085,.130,.318,1.631,'stone edging',name+' projecting inner stone bead')
        block(b,x-.44,x+.44,-.064,.135,1.595,1.636,'hood stone',name+' top jamb')
        raked_cap(b,x,lod,name)
        course(b,x,.291,1.074,.135,.050,'stone edging',name+' sill upper course')
        course(b,x,.258,1.012,.120,.034,'hood stone',name+' sill lower course')
        for side in (-1,1):
            u=x+.355*side
            for j,(lo,hi,span,deep) in enumerate([(.164,.192,.093,.066),(.192,.225,.125,.084),
                                                   (.225,.261,.154,.102)]):
                course(b,u,lo,span,deep,hi-lo,'hood stone',name+f' sill bracket {side} step {j+1}')
    mineral_flecks(b,lod)
    # Two continuous eave positions recorded above both central windows.
    course(b,0,2.023,2*limit,.045,.055,'hood stone','plaster band directly below eave')
    course(b,0,2.077,2*limit,.097,.062,'stone shadow','dark lower eave fascia')
    course(b,0,2.134,2*limit+.030,.197,.054,'eave underside','overhanging eave board')
    course(b,0,2.186,2*limit+.039,.221,.035,'roof edge','red tile eave lip')
    # The roof strip stops short of the ridge. Its pitch is approximate; individual tiles overlap.
    rows=6; pitch=.270
    for j in range(rows):
        y0=-.210+j*.094; y1=y0+.111
        z0=2.219+(y0+.210)*pitch
        tile_length=.388 if lod else .194
        for k in range(-10,11):
            off=tile_length/2 if j%2 else 0
            l=max(-limit-.017,k*tile_length+off-tile_length/2+.002);r=min(limit+.017,k*tile_length+off+tile_length/2-.002)
            if r-l<.016:continue
            pts=[(a,v,z0+(v-y0)*pitch+dz) for dz in (0,.018) for v in (y0,y1) for a in (l,r)]
            faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
            b.add(pts,faces,'weathered tile' if (j+k)%5==0 else 'tile body','eaves tiles row '+str(j+1))
