"""Closed double gate at 429 Wusheng Road, traced from the 2020 and 2021 public street views."""
from math import cos, hypot, pi, sin

PALETTE={'Gate frame iron':dict(color=[.034,.037,.033],metallic=.52,roughness=.59),'Gate picket iron':dict(color=[.048,.046,.039],metallic=.41,roughness=.68)}
# Endpoints on the calibrated facade plane, in X and Z, width and depth in metres.
MEMBERS=[
    ('west top frame', [[-1.405434, 2.323761], [0.062102, 2.351949]], 0.05, 0.051, 'frame'),
    ('west hinge stile', [[-1.405434, 2.323761], [-1.443089, 0.108121]], 0.04, 0.051, 'frame'),
    ('west meeting stile', [[0.062102, 2.351949], [0.006831, 0.102214]], 0.04, 0.051, 'frame'),
    ('west bottom frame', [[-1.443089, 0.108121], [0.006831, 0.102214]], 0.047, 0.051, 'frame'),
    ('west upper notice rail', [[-1.412357, 1.948492], [0.057312, 1.973763]], 0.035, 0.039, 'transverse'),
    ('west shoulder rail', [[-1.428753, 1.160052], [0.036672, 1.190655]], 0.044, 0.039, 'transverse'),
    ('west ornament centre rail', [[-1.429454, 1.008263], [0.035926, 1.025834]], 0.017, 0.039, 'transverse'),
    ('west bottom-band rail', [[-1.431705, 0.835219], [0.025482, 0.860227]], 0.032, 0.039, 'transverse'),
    ('east top frame', [[0.119347, 2.3486], [1.472302, 2.384931]], 0.05, 0.051, 'frame'),
    ('east meeting stile', [[0.119347, 2.3486], [0.075298, 0.111341]], 0.04, 0.051, 'frame'),
    ('east hinge stile', [[1.472302, 2.384931], [1.472724, 0.083392]], 0.04, 0.051, 'frame'),
    ('east bottom frame', [[0.075298, 0.111341], [1.472724, 0.083392]], 0.047, 0.051, 'frame'),
    ('east upper notice rail', [[0.1147, 1.970844], [1.480426, 2.012364]], 0.035, 0.039, 'transverse'),
    ('east shoulder rail', [[0.094379, 1.188605], [1.47511, 1.204292]], 0.044, 0.039, 'transverse'),
    ('east ornament centre rail', [[0.0943, 1.033655], [1.484786, 1.032117]], 0.017, 0.039, 'transverse'),
    ('east bottom-band rail', [[0.08333, 0.858538], [1.476243, 0.869342]], 0.032, 0.039, 'transverse'),
    ('west lower picket 1 segment 1', [[-1.22741, 0.841482], [-1.221259, 0.111964]], 0.013, 0.018, 'picket'),
    ('west lower picket 2 segment 1', [[-1.100554, 0.844389], [-1.101311, 0.113579]], 0.013, 0.018, 'picket'),
    ('west lower picket 3 segment 1', [[-0.974763, 0.847141], [-0.982309, 0.114855]], 0.013, 0.018, 'picket'),
    ('west lower picket 4 segment 1', [[-0.859486, 0.849682], [-0.852033, 0.115875]], 0.013, 0.018, 'picket'),
    ('west lower picket 5 segment 1', [[-0.675614, 0.485021], [-0.679244, 0.291513]], 0.013, 0.018, 'picket'),
    ('west lower picket 6 segment 1', [[-0.485436, 0.4125], [-0.484981, 0.126874]], 0.013, 0.018, 'picket'),
    ('west lower picket 7 segment 1', [[-0.371662, 0.857489], [-0.362253, 0.116102]], 0.013, 0.018, 'picket'),
    ('west lower picket 8 segment 1', [[-0.257402, 0.858875], [-0.24028, 0.115253]], 0.013, 0.018, 'picket'),
    ('west lower picket 9 segment 1', [[-0.127413, 0.860021], [-0.117045, 0.114022]], 0.013, 0.018, 'picket'),
    ('east lower picket 1 segment 1', [[0.236046, 0.862218], [0.233569, 0.118579]], 0.013, 0.018, 'picket'),
    ('east lower picket 2 segment 1', [[0.356811, 0.864255], [0.362103, 0.115731]], 0.013, 0.018, 'picket'),
    ('east lower picket 3 segment 1', [[0.47691, 0.866065], [0.490121, 0.112476]], 0.013, 0.018, 'picket'),
    ('east lower picket 4 segment 1', [[0.613176, 0.867399], [0.619776, 0.10875]], 0.013, 0.018, 'picket'),
    ('east lower picket 5 segment 1', [[0.796226, 0.8043], [0.796309, 0.71679]], 0.013, 0.018, 'picket'),
    ('east lower picket 5 segment 2', [[0.796458, 0.461867], [0.796478, 0.343052]], 0.013, 0.018, 'picket'),
    ('east lower picket 6 segment 1', [[0.991585, 0.375066], [0.984232, 0.106006]], 0.013, 0.018, 'picket'),
    ('east lower picket 7 segment 1', [[1.106348, 0.870532], [1.108219, 0.0908]], 0.013, 0.018, 'picket'),
    ('east lower picket 8 segment 1', [[1.229835, 0.871073], [1.247473, 0.084541]], 0.013, 0.018, 'picket'),
    ('east lower picket 9 segment 1', [[1.351386, 0.871083], [1.369837, 0.078622]], 0.013, 0.018, 'picket'),
    ('west exposed upper upright 1', [[-1.214784, 1.949228], [-1.250907, 1.166861]], 0.016, 0.021, 'picket'),
    ('west exposed upper upright 2', [[-1.10066, 1.963488], [-1.126499, 1.174348]], 0.016, 0.021, 'picket'),
    ('west exposed upper upright 3', [[-0.96719, 1.976636], [-0.954061, 1.731952]], 0.016, 0.021, 'picket'),
    ('west exposed upper upright 4', [[-0.417532, 1.988211], [-0.413922, 1.747926]], 0.016, 0.021, 'picket'),
    ('west exposed upper upright 5', [[-0.239589, 2.017441], [-0.24202, 1.682778]], 0.016, 0.021, 'picket'),
    ('west exposed upper upright 6', [[-0.106649, 1.972572], [-0.093629, 1.724094]], 0.016, 0.021, 'picket'),
    ('east exposed upper upright 1', [[0.267117, 1.963076], [0.250011, 1.221387]], 0.016, 0.021, 'picket'),
    ('east exposed upper upright 2', [[0.401523, 1.984467], [0.373889, 1.216564]], 0.016, 0.021, 'picket'),
    ('east exposed upper upright 3', [[0.495935, 1.979591], [0.498036, 1.857113]], 0.016, 0.021, 'picket'),
    ('east exposed upper upright 4', [[1.088816, 2.004902], [1.105848, 1.807629]], 0.016, 0.021, 'picket'),
    ('east exposed upper upright 5', [[1.256672, 2.005438], [1.257997, 1.687362]], 0.016, 0.021, 'picket'),
    ('east exposed upper upright 6', [[1.395435, 1.988845], [1.390617, 1.199126]], 0.016, 0.021, 'picket'),
]

def add_gate_leaves(builder,lod=False):
    for name,(a,b),width,depth,kind in MEMBERS:
        dx=b[0]-a[0];dz=b[1]-a[1];length=hypot(dx,dz)
        nx=-dz/length;nz=dx/length;hw=width/2;hd=depth/2
        if lod:
            profile=[(-hw,-hd),(hw,-hd),(hw,hd),(-hw,hd)]
        else:
            bevel=min(hw,hd)*.22
            profile=[(-hw+bevel,-hd),(hw-bevel,-hd),(hw,-hd+bevel),(hw,hd-bevel),(hw-bevel,hd),(-hw+bevel,hd),(-hw,hd-bevel),(-hw,-hd+bevel)]
        count=len(profile);verts=[]
        for x,z in (a,b):
            for along,y in profile:verts.append((x+nx*along,y,z+nz*along))
        faces=[tuple(range(count)),tuple(reversed(range(count,2*count)))]
        for k in range(count):faces.append(((k+1)%count,k,k+count,(k+1)%count+count))
        builder.add(verts,faces,'Gate picket iron' if kind=='picket' else 'Gate frame iron',name)

    add_lower_fittings(builder,lod)

add_leaves=add_gate_leaves

# Each fitting is a round boss and the four exposed, paired inflections around it.
FITTINGS=[["west",[-0.68571,0.576631],0.031044,[[[-0.661191,0.594258],[-0.636769,0.621745],[-0.593743,0.646925],[-0.560465,0.652394],[-0.533989,0.644121],[-0.524104,0.629178],[-0.538667,0.615551]],[[-0.657982,0.555476],[-0.628246,0.523359],[-0.584829,0.494087],[-0.55145,0.486798],[-0.527053,0.495488],[-0.515413,0.509266],[-0.533104,0.522367]],[[-0.710503,0.594767],[-0.737357,0.621868],[-0.783068,0.647158],[-0.816847,0.652463],[-0.84462,0.640769],[-0.852498,0.625901],[-0.838515,0.616824]],[[-0.713227,0.557981],[-0.7407,0.523316],[-0.779193,0.497589],[-0.814906,0.489775],[-0.843815,0.498939],[-0.853857,0.512009],[-0.835984,0.52193]]]],["east",[0.787333,0.562029],0.029306,[[[0.811061,0.579037],[0.834648,0.605958],[0.87641,0.630097],[0.908851,0.634717],[0.934775,0.625703],[0.944542,0.610404],[0.930397,0.597092]],[[0.814442,0.540039],[0.843609,0.506961],[0.88614,0.476302],[0.918784,0.467985],[0.942574,0.476019],[0.953866,0.489543],[0.936472,0.503235]],[[0.763125,0.580888],[0.736883,0.608754],[0.692414,0.635288],[0.659688,0.641464],[0.632916,0.630504],[0.625401,0.61585],[0.63897,0.606405]],[[0.760724,0.544102],[0.734286,0.510126],[0.697138,0.485462],[0.662614,0.478672],[0.634602,0.488664],[0.624816,0.502031],[0.642024,0.511444]]]]]

def add_lower_fittings(builder,lod):
    count=12 if lod else 24
    for side,(cx,cz),radius,curves in FITTINGS:
        V=[];F=[]
        for y,r in [(-.049,radius*.86),(-.045,radius),(-.018,radius)]:
            for j in range(count):
                a=2*pi*j/count;V.append((cx+r*cos(a),y,cz+r*sin(a)))
        F=[tuple(range(count)),tuple(reversed(range(2*count,3*count)))]
        for ring in range(2):
            for j in range(count):F.append((ring*count+(j+1)%count,ring*count+j,(ring+1)*count+j,(ring+1)*count+(j+1)%count))
        builder.add(V,F,'Gate frame iron',side+' central round boss')
        for i,pts in enumerate(curves):
            # Sweep the visible curved stem as a metal strip on the front of each leaf.
            verts=[];faces=[];halfwidth=.0065
            for k,(x,z) in enumerate(pts):
                a=pts[max(k-1,0)];b=pts[min(k+1,len(pts)-1)];dx=b[0]-a[0];dz=b[1]-a[1];d=hypot(dx,dz)
                nx=-dz*halfwidth/d;nz=dx*halfwidth/d
                verts.extend([(x-nx,-.038,z-nz),(x+nx,-.038,z+nz),(x+nx,-.021,z+nz),(x-nx,-.021,z-nz)])
            faces=[(0,1,2,3),tuple(reversed(range(len(verts)-4,len(verts))))]
            for k in range(len(pts)-1):
                for j in range(4):faces.append((k*4+(j+1)%4,k*4+j,(k+1)*4+j,(k+1)*4+(j+1)%4))
            builder.add(verts,faces,'Gate picket iron',side+' exposed scroll '+str(i+1))
