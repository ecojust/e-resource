"""One cross-bay from the historical interior plate of Edward Ezra's Adeodata Hall."""
from math import cos, pi, sin
from shapely.geometry import Point, box

PALETTE = {
    'toned ceiling plaster': {'color': [.52, .505, .485], 'roughness': .91},
    'faceted edge of plaster rib': {'color': [.63, .615, .59], 'roughness': .87},
    'incised rib fillet': {'color': [.40, .395, .38], 'roughness': .93},
    'circular rebate': {'color': [.37, .365, .35], 'roughness': .90},
    'bright round panel': {'color': [.88, .865, .83], 'roughness': .81},
    'section edge plaster': {'color': [.58, .565, .53], 'roughness': .95},
}
WIDTH_TO_HAUNCH = 2.30
COVE_RADIUS = .95
CROWN = 1.52
BAY_HALF = 1.78
RADIUS = 1.30

def horizontal_plate(builder, shape, z, thickness, material, label):
    builder.prism(shape, z, z + thickness, lambda x, y, h: (x, y, h), material, label)

def cove_point(side, t, y, offset=0):
    # Positive offset is toward a viewer looking up from below the surface.
    radius = COVE_RADIUS - offset
    return (side*(WIDTH_TO_HAUNCH + radius*sin(t)), y, CROWN-COVE_RADIUS + radius*cos(t))

def cove_strip(builder, side, y0, y1, offset, width, segments, material, label):
    # Keep face normals outward on the underside, closed edges at both crop planes.
    vertices=[]
    for i in range(segments+1):
        t=pi*.5*i/segments
        for y, off in [(y0,offset),(y1,offset),(y1,offset-width),(y0,offset-width)]:
            vertices.append(cove_point(side,t,y,off))
    faces=[(0,1,2,3)]
    for i in range(segments):
        a=i*4
        for j in range(4):
            k=(j+1)%4
            faces.append((a+j,a+4+j,a+4+k,a+k))
    end=4*segments
    faces.append((end+3,end+2,end+1,end))
    if side>0:faces=[tuple(reversed(f))for f in faces]
    builder.add(vertices,faces,material,label)

def build_ceiling(builder,lod):
    near = lod not in ('lod','far',True)
    resolution=37 if near else 20
    segments=26 if near else 13
    ring=lambda radius:Point(0,0).buffer(radius,quad_segs=resolution)
    half=WIDTH_TO_HAUNCH
    panel=box(-half,-BAY_HALF,half,BAY_HALF).difference(ring(RADIUS+.095))
    horizontal_plate(builder,panel,CROWN,.073,'toned ceiling plaster','central flat plaster field')
    # Four continuous profiles give the observed stepped silhouette of the round rim.
    rim=[(.095,.069,.008,'faceted edge of plaster rib'),
         (.069,.040,.027,'circular rebate'),(.040,.016,.022,'faceted edge of plaster rib'),
         (.016,0,.010,'incised rib fillet')]
    for idx,(outer,inner,drop,material) in enumerate(rim):
        horizontal_plate(builder,ring(RADIUS+outer).difference(ring(RADIUS+inner)),CROWN-drop,.077+drop,material,f'round plaster rim {idx+1}')
    horizontal_plate(builder,ring(RADIUS),CROWN+.012,.056,'bright round panel','bright circular ceiling panel')
    for side,side_name in [(-1,'left'),(1,'right')]:
        cove_strip(builder,side,-BAY_HALF,BAY_HALF,0,.073,segments,'toned ceiling plaster',f'{side_name} curved plaster field')
        # Paired strips run along the spring and where the cove meets the flat field.
        for t0,t1,drop,material,name in [(0,.047,.018,'faceted edge of plaster rib','upper longitudinal fillet'),
                                         (1.43,1.49,.017,'incised rib fillet','cornice shadow'),
                                         (1.49,pi/2,.037,'faceted edge of plaster rib','spring cornice')]:
            vs=[cove_point(side,t,y,d)for t in (t0,t1)for y,d in ((-BAY_HALF,drop),(BAY_HALF,drop),(BAY_HALF,-.001),(-BAY_HALF,-.001))]
            fs=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
            builder.add(vs,fs if side<0 else [tuple(reversed(f))for f in fs],material,f'{side_name} {name}')
    # The photograph resolves a raised central line flanked by two smaller fillets.
    for direction in (-1,1):
        y=direction*(BAY_HALF-.093)
        for j,(shift,width,drop,material) in enumerate([(-.065,.017,.019,'incised rib fillet'),(0,.095,.049,'faceted edge of plaster rib'),(.065,.017,.019,'incised rib fillet')]):
            at=y+shift
            builder.box((0,at,CROWN-drop/2),(2*half,width,drop),material,label=f'flat transverse rib {direction} {j}')
            for side in (-1,1):
                cove_strip(builder,side,at-width/2,at+width/2,drop,drop+.0005,segments,material,f'curved transverse rib {direction} {side} {j}')
