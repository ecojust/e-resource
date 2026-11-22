"""The panelled cream piers and cast iron ornament in the 2018 Xiangshan Road photograph."""
from pathlib import Path
import json
import math

import numpy as np
from shapely import affinity
from shapely.geometry import Point,Polygon,box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE.parent/'measurements/courtyard-pier-and-ironwork.json').read_text())
CREAM='9 courtyard | cream plaster'
RECESS='9 courtyard | recessed plaster'
GREY='9 courtyard | grey coping'
EDGE='9 courtyard | coping edge'
PLINTH='9 courtyard | grey rendered plinth'
IRON='9 courtyard | black painted iron'
BRONZE='9 courtyard | weathered foliate casting'
RUBBED='9 courtyard | rubbed casting edges'

def finish(rgb,roughness,metal=0.):
    c=np.asarray(rgb)/255.
    return dict(color=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),
                roughness=roughness,metallic=metal)
PALETTE={CREAM:finish([211,198,160],.91), RECESS:finish([188,176,140],.94),
         GREY:finish([112,118,116],.87), EDGE:finish([133,138,134],.82),
         PLINTH:finish([147,146,137],.94), IRON:finish([49,48,45],.67,.37),
         BRONZE:finish([63,59,48],.70,.43), RUBBED:finish([103,100,81],.57,.48)}

def slab(b,p,y0,y1,mat,name):
    b.prism(p,-y1,-y0,lambda x,z,d:(x,-d,z),mat,'9 front | '+name)

def squared(b,x,depth,profile,mat,name):
    """Join successive square sections; widths are actual full sections."""
    verts=[]
    for z,width in profile:
        r=width/2
        verts.extend([(x-r,depth-r,z),(x+r,depth-r,z),(x+r,depth+r,z),(x-r,depth+r,z)])
    faces=[(0,3,2,1),tuple(range(len(verts)-4,len(verts)))]
    for k in range(len(profile)-1):
        for j in range(4):
            a,bj=4*k+j,4*k+(j+1)%4
            faces.append((a,bj,bj+4,a+4))
    b.add(verts,faces,mat,label='9 front | '+name)

def inset_shaft(b,x,label,lod):
    # Two separate recesses are visible on the actual street face. They
    # terminate against plaster inside the pier, with a narrow second rebate.
    start=len(b.parts)
    sections=[(.354,.599,2.340,box(x-.107,.79,x+.107,2.235)),
              (.323,2.353,2.736,box(x-.222,2.385,x+.222,2.672))]
    squared(b,x,0.,[(2.340,.708),(2.346,.693),(2.353,.646)],CREAM,label+' plaster shoulder between panels')
    for i,(side,base,top,cut) in enumerate(sections):
        front=-side
        wall=box(x-side,base,x+side,top)
        slab(b,wall.difference(cut),front,side,CREAM,label+f' shaft section {i+1}')
        inner=cut.buffer(-(.021 if i==0 else .026),join_style=2)
        slab(b,cut.difference(inner),front+.020,side,CREAM,label+f' rebate step {i+1}')
        slab(b,inner,front+(.048 if i==0 else .053),side,RECESS,label+f' recessed panel {i+1}')
        if not lod:
            for j,z in enumerate((inner.bounds[1]+.016,inner.bounds[3]-.017)):
                slab(b,box(inner.bounds[0],z-.008,inner.bounds[2],z+.008),front+.039,front+.051,
                     CREAM,label+f' panel {i+1} moulding {j+1}')
    squared(b,x,0.,[(.002,.743),(.05,.757),(.520,.758),(.556,.744),(.582,.716),(.601,.681)],
            PLINTH,label+' grey base')
    squared(b,x,0.,[(2.733,.676),(2.755,.70),(2.785,.728),(2.839,.729),(2.853,.748)],
            CREAM,label+' projecting neck')
    squared(b,x,0.,[(2.849,.746),(2.86,.761),(2.875,.771),(2.89,.772),
                      (2.906,.791),(2.918,.777),(2.975,.819),(2.990,.862)],
            GREY,label+' profiled grey cornice')
    squared(b,x,0.,[(2.990,.862),(3.019,.873),(3.044,.884),(3.090,.886),(3.105,.859)],
            EDGE,label+' dripping edge of cap')
    squared(b,x,0.,[(3.105,.854),(3.151,.635),(3.153,.482),(3.202,.482),(3.217,.456)],
            GREY,label+' upper slab and square step')
    squared(b,x,0.,[(3.217,.332),(3.268,.332),(3.283,.295)],GREY,label+' small head block')
    # Independent oblique sight lines to both cap mitres constrain the
    # overhang. The plaster shoulder sits higher on both photographed piers.
    for part in b.parts[start:]:
        verts=np.array(part['vertices'])
        z=verts[:,2].copy()
        flare=1.+.067*np.interp(z,[2.849,2.990],[0.,1.])
        verts[:,0]=x+(verts[:,0]-x)*flare
        verts[:,1]*=flare
        verts[:,2]+=np.interp(z,[.601,2.340,2.733,2.849,2.990,3.105],
                              [0.,.112,.0608,.0437,.0195,0.],left=0.,right=0.)
        part['vertices']=verts.tolist()

def outline_xy(raw,height=.225,width=.106):
    x,y=raw
    cx=97.+(111.-97.)*(y-59.)/(258.-59.)
    return np.array([(x-cx)*width/87.,(258.-y)*height/(258.-59.)])

def ornament(b,x,plane,z,lod,tag):
    mark=DATA['cast_finial']
    profile=Polygon([outline_xy(t) for t in mark['outline_crop_px']])
    p=affinity.translate(profile,xoff=x,yoff=z)
    if lod:p=p.simplify(.0026,preserve_topology=True)
    slab(b,p,plane-.0115,plane+.0115,BRONZE,tag+' cast spear and scroll leaves')
    # A raised centre ridge gives the taper changing thickness in profile.
    points=np.array([outline_xy(v) for v in [[97,60],[82,150],[103,166],[127,151]]])
    front=[(x+u,plane-.0117,z+h) for u,h in points]
    top=(x+.001,plane-.027,z+.145)
    b.add([*front,top],[(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],RUBBED,
          label='9 front | '+tag+' blade facets')
    for i,curve in enumerate(mark['crest_ridges_crop_px'][:2 if lod else 4]):
        xyz=[(x+v[0],plane-.016,z+v[1]) for v in (outline_xy(t) for t in curve)]
        b.tube(xyz,.0051 if i<2 else .0033,RUBBED,5 if lod else 8,
               '9 front | '+tag+f' raised scroll {i+1}')
    b.lathe((x,plane),[(z-.018,.021),(z-.006,.027),(z+.003,.027),(z+.014,.022)],
            IRON,8 if lod else 12,'9 front | '+tag+' collar')

def roundel(b,x,y,z,rad,lod,name):
    n=8 if lod else 14
    disk=Point(x,z).buffer(rad,quad_segs=n)
    hoop=disk.difference(Point(x,z).buffer(rad-.0085,quad_segs=n))
    slab(b,hoop,y-.010,y+.010,IRON,name+' round iron rim')
    arm=Polygon([(-.008,.003),(-.010,.024),(-.021,.031),(-.014,.042),(0.,.056),
                 (.014,.042),(.021,.031),(.010,.024),(.008,.003)])
    arms=unary_union([affinity.rotate(arm,k*90,origin=(0.,0.)) for k in range(4)]
                     +[Point(0,0).buffer(.012,quad_segs=5)])
    arms=affinity.scale(arms,rad/.058,rad/.058,origin=(0.,0.))
    slab(b,affinity.translate(arms,xoff=x,yoff=z),y-.014,y+.005,BRONZE,name+' four cast petals')
    # The photograph catches separate highlights on four leaf midribs.
    # Cross sections are diamond shaped and taper back to the cast petal.
    factor=rad/.058
    for i in range(4):
        angle=i*math.pi/2
        vx=[]
        profile=[(.007,.004,.020),(.023,.006,.026),(.033,.011,.032),
                 (.041,.008,.029),(.051,.002,.020)]
        for t,width,crest in profile:
            for side,depth in [(-width,.014),(0.,crest),(width,.014),(0.,.009)]:
                a=side*math.cos(angle)+t*math.sin(angle)
                c=-side*math.sin(angle)+t*math.cos(angle)
                vx.append((x+a*factor,y-depth*factor,z+c*factor))
        faces=[(3,2,1,0),tuple(range(len(vx)-4,len(vx)))]
        for k in range(len(profile)-1):
            for h in range(4):
                a,bh=4*k+h,4*k+(h+1)%4
                faces.append((a,bh,bh+4,a+4))
        b.add(vx,faces,RUBBED,label='9 front | '+name+f' raised petal {i+1}')
    # The button projects toward the street from the plane of the hoop.
    b.lathe((0.,0.),[(.010,.016),(.017,.021),(.025,.018),(.030,.010),(.032,.003)],
            RUBBED,8 if lod else 14,'9 front | '+name+' domed centre')
    button=b.parts[-1]
    button['vertices']=[(x+a*factor,y-h*factor,z+c*factor) for a,c,h in button['vertices']]

def iron_span(b,left,right,lod,label):
    span=right-left
    b.box(((left+right)/2,.007,.307),(span-.708,.425,.614),PLINTH,label='9 front | '+label+' low boundary stone')
    b.box(((left+right)/2,.007,.617),(span-.707,.451,.048),GREY,label='9 front | '+label+' wall coping')
    plane=.018
    for i,z in enumerate((.87,2.382)):
        b.box(((left+right)/2,plane-.016,z),(span-.669,.046,.048),IRON,
              label='9 front | '+label+f' horizontal rail {i+1}')
    observed=DATA['iron']['measured_abscissae_m_on_winter_plane']
    anchors=[left+span*f/4.83744 for f in observed]
    for i,x in enumerate(anchors):
        name=label+f' upright {i+1}'
        b.box((x,plane,1.567),(.030,.034,1.862),IRON,label='9 front | '+name+' shaft')
        ornament(b,x,plane,2.495,lod,name)
    for i,(a,c) in enumerate(zip(anchors,anchors[1:])):
        if i%2==0:
            radius=min(.071,(c-a)*.44)
            roundel(b,(a+c)/2,plane-.013,2.382-.016-radius,radius,lod,label+f' suspended rosette {i//2+1}')

def add_courtyard_boundary(b,lod=False):
    """Assemble just the panelled piers and two adjoining visible iron spans."""
    record=json.loads((HERE.parent/'measurements/courtyard-boundary-placement.json').read_text())
    b.palette.update(PALETTE)
    offset=len(b.parts)
    scale=record['horizontal_section_scale']
    centres=np.array(record['local_pier_centres_m'])/scale
    for i,x in enumerate(centres):
        inset_shaft(b,x,f'cream pier {i+1}',lod)
    for i,(l,r) in enumerate(zip(centres,centres[1:])):
        iron_span(b,l,r,lod,f'iron bay {i+1}')
    unit=np.array(record['unit_x_in_building_xy'])
    cross=np.array([-unit[1],unit[0]])
    basis=np.array([[unit[0],cross[0],0],[unit[1],cross[1],0],[0,0,1.]])@np.diag([scale,scale,record['vertical_section_scale']])
    origin=np.array(record['origin_in_building_xyz_m'])
    for part in b.parts[offset:]:
        part['vertices']=(np.asarray(part['vertices'])@basis.T+origin).tolist()
