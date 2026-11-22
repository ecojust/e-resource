"""Surveyed segmental brick hood, stepped central key and sill for Liang's courtyard window."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from window_photo import wall_coordinates

DATA = json.loads((Path(__file__).resolve().parents[1]/'measurements'/'brick-surround.json').read_text())
BED = 'Liang lime pointing'
OUTER = ('Liang dark fired red', 'Liang russet fired red', 'Liang rich ochre brick')
INNER = ('Liang rose clay', 'Liang warm terra cotta')
KEY = 'Liang shaped red clay'
STONE = 'Liang worn sill stone'
STONE_TOP = 'Liang sill upper surface'
STONE_EDGE = 'Liang sill bevel'
STAINS = ('Liang subdued ochre on sill', 'Liang olive-gray on sill', 'Liang reddish sill wear')
APRON = ('Liang lower red brick', 'Liang lower brown brick', 'Liang lower muted brick')
EXPOSED = 'Liang weathered lower substrate'

def pigment(rgb):
    c=np.asarray(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=.89)

PALETTE={BED:pigment([204,184,161]),KEY:pigment([167,82,60]),
         STONE:pigment([187,165,133]),STONE_TOP:pigment([165,150,125]),
         STONE_EDGE:pigment([173,149,122]),EXPOSED:pigment([137,119,98])}
for names,colors in ((OUTER,[(152,68,44),(162,75,48),(174,83,55)]),
                     (INNER,[(182,102,79),(193,115,86)]),
                     (APRON,[(166,79,60),(155,73,54),(176,85,65)]),
                     (STAINS,[(173,149,119),(142,139,103),(168,117,94)])):
    PALETTE.update({name:pigment(color) for name,color in zip(names,colors)})

def plane(x,z,outward):
    return (x,-outward,z)

def slab(builder, pixels, face, back, material, label, inset=0):
    if not isinstance(pixels,Polygon):
        pixels=Polygon(pixels)
    if inset:
        pixels=pixels.buffer(-inset,join_style='mitre')
    if pixels.is_empty or pixels.area<.1:
        return
    if pixels.geom_type=='MultiPolygon':
        for geometry in pixels.geoms:
            slab(builder,geometry,face,back,material,label)
        return
    def ring(coords):
        return wall_coordinates(np.asarray(coords),-face)
    polygon=Polygon(ring(pixels.exterior.coords),[ring(h.coords) for h in pixels.interiors])
    builder.prism(polygon,back,face,plane,material,label)

def stripe(top,bottom):
    return Polygon([*top,*reversed(bottom)])

def arc(builder):
    crest,middle,intrados=(DATA[k] for k in ('outer_curve','first_bed','intrados'))
    # End bed returns are preserved, including the separate block visible past each fan.
    top_strip=stripe(crest,middle)
    low_strip=stripe(middle,intrados)
    left_end=[(56.7,104.4),(79.1,103.4),(94.1,127.0),(73.1,130.3),(61.3,128.4)]
    right_end=[(426.1,101.7),(447.7,100.4),(445.3,125.7),(428.4,129.4),(416.5,126.5)]
    entire=unary_union([top_strip,low_strip,Polygon(left_end),Polygon(right_end)])
    slab(builder,entire,.014,-.012,BED,'Brick hood/pointed bed')
    for i,shape in enumerate((left_end,right_end)):
        slab(builder,shape,.052,.014,OUTER[i],f'Brick hood/end return {i+1}',.48)
    guide_x,guide_y=DATA['radial_guide_point']
    def at(x,y):
        ref=69.+.00157*(x-251.5)**2
        return x+(guide_x-x)*(y-ref)/(guide_y-ref)
    def wedge(a,b):
        return Polygon([(at(a,46),46),(at(b,46),46),(at(b,163),163),(at(a,163),163)])
    # The lower ring is clipped to the photographed drooping returns. Some joints
    # disappear into the surrounding white brick even though the outer ring continues.
    for hand,guides in zip(('L','R'),DATA['radial_lines_x_at_strip']):
        for index,(lo,hi) in enumerate(zip(guides,guides[1:])):
            clip=wedge(lo,hi)
            for ring,region,palette,face in [('archivolt',top_strip,OUTER,.066),('inner fan',low_strip,INNER,.037)]:
                shape=region.intersection(clip)
                if shape.geom_type in ('Polygon','MultiPolygon'):
                    slab(builder,shape,face,.014,palette[(index*5+index//4)%len(palette)],f'Hood {hand}/{ring} {index+1:02d}',.48)
    upper=np.asarray(DATA['key_upper_joints']);lower=np.asarray(DATA['key_lower_joints'])
    key=stripe(upper,lower)
    slab(builder,key,.073,.013,BED,'Hood key/mortar field')
    for i,(u0,u1,b0,b1) in enumerate(zip(upper,upper[1:],lower,lower[1:])):
        stations=[0,*[(v-u0[1])/(b0[1]-u0[1]) for v in DATA['key_bed_levels'][i]],1]
        for j,(a,b) in enumerate(zip(stations,stations[1:])):
            quad=[u0+(b0-u0)*a,u1+(b1-u1)*a,u1+(b1-u1)*b,u0+(b0-u0)*b]
            slab(builder,quad,.084,.073,KEY,f'Hood key/strip {i+1} block {j+1}',.49)
    cap=[(224.1,31),(284.1,30.4),(282.2,42.2),(225.1,43.3)]
    slab(builder,cap,.111,.032,BED,'Hood key/cap joints')
    divisions=[0,.328,.590,1]
    t0,t1,b1,b0=np.asarray(cap)
    for i,(a,b) in enumerate(zip(divisions,divisions[1:])):
        slab(builder,[t0+(t1-t0)*a,t0+(t1-t0)*b,b0+(b1-b0)*b,b0+(b1-b0)*a],
             .118,.106,KEY,f'Hood key/header {i+1}',.43)
    slab(builder,[(227,42.4),(280.5,41.8),(278.5,52.2),(228.6,53.4)],.099,.026,OUTER[1],'Hood key/lower fascia')
    slab(builder,[(229.3,50.3),(278.0,49.7),(277.8,52.7),(229.7,53.3)],.108,.085,INNER[0],'Hood key/lower moulding')
    slab(builder,[(233.4,30.5),(252.6,17.7),(271.7,30.1)],.094,.024,INNER[0],'Hood key/triangular cap')
    slab(builder,[(224.4,30.4),(283.7,29.8),(284.1,31.4),(224.1,32.3)],.124,.106,OUTER[1],'Hood key/upper lip')

def sill(builder,lod):
    survey=DATA['sill']
    profile=[('upper_rear',.013),('upper_nose',.123),('lower_nose',.130),('lower_bevel',.105)]
    rows=[]
    for key,out in profile:
        xy=wall_coordinates(survey[key],-out)
        rows.append([(x,-out,z) for x,z in xy])
    xy=wall_coordinates(survey['lower_bevel'],-.105)
    rows.append([(x,.013,z) for x,z in xy])
    for i,material in enumerate((STONE_TOP,STONE,STONE_EDGE,STONE_EDGE,STONE)):
        j=(i+1)%len(rows)
        builder.add([rows[i][0],rows[i][1],rows[j][1],rows[j][0]],[(3,2,1,0)],material,
                    'Stone sill/'+('sloping top','weathered face','lower bevel','soffit','back')[i])
    for side in (0,1):
        verts=[row[side] for row in rows]
        face=tuple(range(len(verts)))
        builder.add(verts,[face[::-1] if side==0 else face],STONE_EDGE,f'Stone sill/end {side+1}')

    # The photograph shows discontinuous mineral, green-gray and red-brown
    # weathering on the sill. Use small, original geometric patches following the
    # inclined stone face. No pixels or imagery are embedded in the model.
    if not lod:
        islands=[(.075,.18,.051,.13,0),(.17,.17,.037,.16,1),(.22,.46,.036,.13,0),
                 (.27,.17,.046,.12,1),(.41,.77,.034,.12,0),(.45,.30,.032,.16,1),
                 (.49,.17,.069,.14,1),(.54,.33,.042,.20,1),(.63,.47,.039,.19,2),
                 (.68,.16,.034,.15,0),(.73,.55,.038,.10,2),(.79,.26,.024,.16,0),
                 (.85,.68,.039,.16,2),(.91,.35,.035,.19,2),(.95,.61,.035,.20,2)]
        edge=[(-1,.06),(-.72,-.59),(-.21,-.92),(.14,-.62),(.34,-1),(.74,-.48),
              (1,-.18),(.69,.24),(.82,.60),(.38,.72),(.08,1),(-.29,.62),(-.74,.83)]
        a,b=np.array(rows[1]);d,c=np.array(rows[2])
        for number,(u,v,rx,ry,tone) in enumerate(islands,1):
            verts=[]
            for dx,dy in edge:
                U,V=u+rx*dx,v+ry*dy
                pt=(1-V)*((1-U)*a+U*b)+V*((1-U)*d+U*c)
                pt[1]-=.0006
                verts.append(pt)
            from shapely import constrained_delaunay_triangles
            shape=Polygon([(p[0],p[2]) for p in verts])
            coords=np.asarray([(p[0],p[2]) for p in verts])
            faces=[]
            for piece in constrained_delaunay_triangles(shape).geoms:
                idx=[int(np.argmin(abs(coords-q).sum(axis=1))) for q in piece.exterior.coords[:-1]]
                face=np.asarray(verts)[idx]
                if np.cross(face[1]-face[0],face[2]-face[0])[1]>0:idx.reverse()
                faces.append(idx)
            builder.add(verts,faces,STAINS[tone],f'Stone sill/subtle mineral patch {number:02d}')

def apron(builder):
    left,right=DATA['apron_left'],DATA['apron_right']
    boundary=Polygon([*left,*reversed(right)])
    slab(builder,boundary,.018,-.015,BED,'Sill apron/bedding')
    beds=DATA['apron_beds']
    for line,(top,bottom,joints) in enumerate(zip(beds,beds[1:],DATA['apron_head_joints'])):
        def y(x,bed):
            return bed[0]+(bed[1]-bed[0])*(x-120)/284
        for j,(x0,x1) in enumerate(zip([115,*joints],[*joints,411])):
            poly=Polygon([(x0,y(x0,top)),(x1,y(x1,top)),(x1,y(x1,bottom)),(x0,y(x0,bottom))]).intersection(boundary)
            if poly.geom_type=='Polygon':
                slab(builder,poly,.03,.018,APRON[(j*7+line*3+j//3)%3],
                     f'Sill apron/course {line+1} brick {j+1}',.56)
    # Sunken, weathered areas expose render on the lower courses. These are
    # variations in the surviving face, not openings through the masonry.
    losses=[[(151,679.5),(152,669),(157,664),(166,661),(176,664),(179,671),(180,679.5)],
            [(186,679.5),(186,672),(193,667),(210,665),(212,660),(222,654),(227,654),(228,659),(223,664),(224,673),(233,678),(233,679.5)],
            [(236,679.5),(237,673),(242,666),(240,660),(240,655),(244,650),(251,649),(255,652),(260,654),(264,653),(265,660),(259,665),(257,670),(259,679.5)],
            [(274,679.5),(277,672),(282,669),(284,664),(279,656),(271,655),(269,651),(277,650),(285,652),(291,650),(298,647),(302,650),(303,657),(301,665),(305,670),(305,679.5)]]
    for i,p in enumerate(losses):
        slab(builder,p,.0314,.0301,EXPOSED,f'Sill apron/exposed substrate {i+1}')

def add_brick_surround(builder,lod=False):
    arc(builder)
    sill(builder,lod)
    apron(builder)
