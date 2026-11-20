"""Garden elevation, central five bays. X runs to the viewer's right, Y into the building."""
from math import cos, pi, sin

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import opening


PALETTE = {
    'cream render': {'color': [.72, .64, .46], 'roughness': .88},
    'ivory stone': {'color': [.84, .77, .60], 'roughness': .74},
    'buff moulding': {'color': [.59, .49, .32], 'roughness': .78},
    'reveal': {'color': [.37, .30, .22], 'roughness': .86},
    'sash': {'color': [.22, .18, .14], 'roughness': .55},
    'window glass': {'color': [.065, .093, .102], 'metallic': .24, 'roughness': .28},
    'balcony iron': {'color': [.28, .24, .18], 'metallic': .5, 'roughness': .55},
    'section': {'color': [.39, .39, .36], 'roughness': .92},
}
PIERS = [-11.40 + 4.56 * i for i in range(6)]
BAYS = [(a+b)/2 for a,b in zip(PIERS, PIERS[1:])]


def add_center(b, lod):
    """Build only visible central component. Depth signs below are local Y."""
    stone, render, moulding = 'ivory stone', 'cream render', 'buff moulding'
    seg = 12 if lod else 32
    def block(name, x, y, z, w, d, h, mat=stone):
        b.box((x,y,z), (w,d,h), mat, label=name)
    def slab(name, z, thick, front, back, width, mat=stone):
        block(name, 0,(front+back)/2,z-thick/2,width,back-front,thick,mat)
    def prism(name, poly, front, back, mat):
        b.prism(poly,-back,-front,lambda x,z,d:(x,-d,z),mat,name)
    def band(name, shape, thick, front, back, mat):
        prism(name,shape.buffer(thick, join_style='mitre').difference(shape),front,back,mat)
    def glazed(name, shape, front, bars):
        prism(name+'/glazing',shape.buffer(.012,join_style='mitre'),front+.17,front+.21,'window glass')
        inner=shape.buffer(-.058,join_style='mitre')
        bounded=unary_union(bars).intersection(inner)
        prism(name+'/sash',shape.difference(inner.difference(bounded)),front+.032,front+.12,'sash')

    slab('Plinth/stone step',.16,.16,-.50,3.32,24.45)
    arches=[opening(x,.14,2.42,4.13,1.20,seg) for x in BAYS]
    prism('Arcade/perforated wall',box(-12.15,.16,12.15,5.08).difference(unary_union(arches)),.63,1.12,render)
    for i,(x,aperture) in enumerate(zip(BAYS,arches),1):
        name=f'Arcade {i:02}/arched sash'
        spring=3.07
        strokes=[box(x-1.22,spring-.035,x+1.22,spring+.035)]
        for j in range(-2,3):
            u=x+j*.405
            strokes.append(box(u-.018,.13,u+.018,spring))
        for z in [1.18,2.15]:
            strokes.append(box(x-1.22,z-.019,x+1.22,z+.019))
        for j in range(1,6):
            a=j*pi/6
            strokes.append(LineString([(x,spring),(x+1.3*cos(a),spring+1.3*sin(a))]).buffer(.016))
        glazed(name,aperture,.75,strokes)
        # Architrave follows curved head and both jambs. The sill meets grade.
        outer=aperture.buffer(.13,join_style='mitre')
        above_sill=box(x-2,.14,x+2,5)
        prism(name+'/stone architrave',outer.difference(aperture).intersection(above_sill),.49,.70,stone)
        lip=outer.buffer(.045,join_style='mitre').difference(outer)
        prism(name+'/fillet',lip.intersection(above_sill),.50,.63,moulding)
        prism(name+'/keystone',Polygon([(x-.12,4.23),(x+.12,4.23),(x+.19,4.52),(x-.19,4.52)]),.40,.60,stone)

    for j,x in enumerate(PIERS,1):
        name=f'Axis {j:02}'
        for side,dx in [('L',-.38),('R',.38)]:
            c=f'{name}/column {side}'
            block(c+' plinth',x+dx,-.10,.23,.77,.76,.20)
            # Stepped base, taper and flared necking/capital.
            profile=[(.31,.38),(.38,.38),(.43,.33),(.51,.35),(.57,.30),
                     (1.4,.302),(4.40,.25),(4.44,.29),(4.50,.26),
                     (4.58,.28),(4.64,.35),(4.75,.38)]
            b.lathe((x+dx,-.08),profile,stone,seg,label=c+' turned shaft')
            block(c+' abacus',x+dx,-.08,4.82,.77,.78,.15)
        block(name+'/projecting capital',x,-.03,5.03,1.72,1.00,.28)
    for z,t,y,w,mat in [(5.18,.21,-.44,24.5,stone),(5.70,.52,-.26,24.36,render),
                          (5.81,.11,-.38,24.5,stone),(5.95,.14,-.46,24.63,moulding),
                          (6.08,.13,-.52,24.76,stone),(6.22,.14,-.58,24.88,stone)]:
        slab('Arcade/entablature',z,t,y,1.38,w,mat)

    octagons=[]
    for x in BAYS:
        w,h,corner=1.83,2.08,.42
        z=7.84
        offsets=[(-w/2+corner,-h/2),(w/2-corner,-h/2),(w/2,-h/2+corner),
                 (w/2,h/2-corner),(w/2-corner,h/2),(-w/2+corner,h/2),
                 (-w/2,h/2-corner),(-w/2,-h/2+corner)]
        octagons.append(Polygon([(x+a,z+c) for a,c in offsets]))
    prism('Mezzanine/perforated octagon wall',box(-12.15,6.18,12.15,9.55).difference(unary_union(octagons)),.14,.68,render)
    for i,(x,p) in enumerate(zip(BAYS,octagons),1):
        tag=f'Mezzanine {i:02}/octagon'
        band(tag+'/inner reveal',p,.11,-.01,.19,stone)
        band(tag+'/outer moulding',p.buffer(.11,join_style='mitre'),.075,-.06,.13,moulding)
        bars=[box(x+dx-.019,6.7,x+dx+.019,9.0) for dx in [-.43,0,.43]]
        bars += [box(x-1,z-.02,x+1,z+.02) for z in [7.47,8.13]]
        glazed(tag,p,.20,bars)

    for i,x in enumerate(PIERS,1):
        tag=f'Axis {i:02}/urn pedestal'
        block(tag,x,-.12,7.26,1.25,.81,2.13)
        block(tag+' recessed field',x,-.545,7.31,.84,.075,1.42,render)
        for z,w,d,h in [(6.34,1.58,1.14,.23),(8.24,1.46,1.03,.16),(8.39,1.59,1.13,.15)]:
            block(tag+' cornice',x,-.13,z,w,d,h)
        profile=[(8.45,.32),(8.56,.32),(8.63,.22),(8.72,.19),(8.79,.29),(8.88,.38),
                 (9.08,.48),(9.30,.50),(9.49,.43),(9.61,.31),(9.68,.43),(9.75,.44)]
        b.lathe((x,-.29),profile,stone,seg,label=f'Axis {i:02}/urn')

    # Balcony rear facade is cut around recessed glazed door/sidelight assemblies.
    for level,(floor,ceiling) in enumerate([(9.65,13.65),(13.65,17.96)],1):
        tag=f'Balcony L{level}'
        slab(tag+'/projecting deck',floor,.28,-.15,3.38,24.41)
        openings=[box(x-1.28,floor+.05,x+1.28,floor+3.16) for x in BAYS]
        prism(tag+'/rear wall',box(-12.12,floor,12.12,ceiling).difference(unary_union(openings)),2.7,3.30,'cream render')
        for i,(x,p) in enumerate(zip(BAYS,openings),1):
            frame=f'{tag} bay {i:02}'
            bars=[box(x+dx-.037,floor,x+dx+.037,floor+3.23) for dx in [-.81,0,.81]]
            bars += [box(x-1.29,floor+2.31,x+1.29,floor+2.38),box(x-.81,floor+1.81,x+.81,floor+1.88)]
            glazed(frame,p,2.75,bars)
            band(frame+'/jamb mould',p,.075,2.63,2.72,moulding)
            # Thin iron pickets flanking a panel of scrollwork behind the piers.
            span=3.36
            for off in [-span/2 + span*j/14 for j in range(15)]:
                block(frame+'/railing pickets',x+off,.18,floor+.59,.034,.041,1.08,'balcony iron')
            for z,h in [(floor+.07,.07),(floor+.99,.04),(floor+1.16,.073)]:
                block(frame+'/handrail',x,.18,z,span+.12,.085,h,'balcony iron')
            if not lod:
                for k in range(3):
                    for sign in [-1,1]:
                        points=[(x+sign*.124*(1-cos(t*pi/8)),.15,floor+.25+k*.26+.12*sin(t*pi/8)) for t in range(17)]
                        b.tube(points,.016,'balcony iron',6,frame+'/scroll panel')
        for i,x in enumerate(PIERS,1):
            tag_p=f'Axis {i:02}/giant pier'
            block(tag_p,x,.32,(floor+ceiling)/2,1.14,.81,ceiling-floor,stone)
            if level==2:
                block(tag_p+' capital',x,.30,17.86,1.40,1.05,.23)
    for z,t,y,w,mat in [(18.08,.20,-.24,24.52,moulding),(18.28,.20,-.50,24.85,stone),
                          (18.44,.16,-.58,25,stone)]:
        slab('Upper terrace/cornice',z,t,y,3.40,w,mat)
    if not lod:
        for j in range(25):
            block('Upper terrace/modillions',(j-12)*.99,-.21,17.94,.30,.48,.24)
    for i,x in enumerate(PIERS,1):
        tag=f'Axis {i:02}/attic pier'
        block(tag,x,.38,20.03,.92,.94,3.23)
        block(tag+' field',x,-.103,20.65,.66,.055,1.32,render)
        block(tag+' collar',x,.35,21.45,1.13,1.10,.21)
        block(tag+' projecting rail pedestal',x,-.015,19.04,1.13,.74,1.26)
    for i,x in enumerate(BAYS,1):
        name=f'Attic bay {i:02}'
        for j in range(9):
            pos=x+(j-4)*.364
            profile=[(18.50,.106),(18.57,.118),(18.62,.080),(18.70,.067),
                     (18.83,.122),(18.98,.107),(19.14,.066),(19.30,.065),
                     (19.41,.107),(19.47,.107)]
            b.lathe((pos,-.02),profile,stone,8 if lod else 18,label=name+'/turned balustrade')
        block(name+'/handrail',x,-.02,19.54,3.53,.31,.15)
    block('Attic loggia/recessed back',0,3.07,20.04,24.15,.55,3.24,render)
    for z,t,y,w,mat in [(21.63,.21,-.22,24.3,stone),(21.76,.13,-.38,24.53,moulding),
                          (21.91,.15,-.48,24.65,stone)]:
        slab('Pediment/entablature',z,t,y,3.40,w,mat)
    # Raised straight parapet visible behind the slopes in 1926 and 2015.
    block('Pediment/recessed parapet',0,2.50,23.05,22.4,.36,2.80,render)
    block('Pediment/parapet coping',0,2.5,24.46,22.52,.45,.13,stone)
    face=Polygon([(-12.24,21.90),(12.24,21.90),(0,26.59)])
    prism('Pediment/tympanum',face,.10,2.01,render)
    # Two raking cornices with a continuous mitered apex. No presumed roof behind it.
    for zlo,zhi,w,y0,y1,mat in [(-.34,-.20,12.11,-.05,.18,moulding),(-.20,-.09,12.24,-.17,.15,stone),
                                   (-.09,.03,12.39,-.26,.21,moulding),(.03,.12,12.46,-.31,.28,stone)]:
        ends=26.59-4.69*w/12.24
        shape=Polygon([(-w,ends+zlo),(0,26.59+zlo),(w,ends+zlo),
                       (w,ends+zhi),(0,26.59+zhi),(-w,ends+zhi)])
        prism('Pediment/raking cornice',shape,y0,y1,mat)
    # Caps on the true depth of individual visible elements, no closed fake wings.
    block('Section/back of lower arcade',0,1.23,5.57,24.3,.32,1.20,'section')
    for x in [-12.12,12.12]:
        block('Section/arcade side return',x,2.0,4.84,.15,2.32,9.36,'section')
        block('Section/attic side return',x,1.84,19.96,.15,2.77,3.04,render)
