"""The four pierced panels of the Cheng family's historic street balcony.

This exterior fragment follows the four X motifs in the period photograph.
The upper surface of the projecting sill is Z0. Positive Y is into the house.
"""
import json
from pathlib import Path
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon

MEASUREMENTS = Path(__file__).resolve().parents[1]/'measurements'
SURVEY = json.loads((MEASUREMENTS/'historic-balcony-cameras.json').read_text())
PATH = np.array(SURVEY['balcony_upper_plan_m'])
PREFIX = 'Cheng historic balcony | '
FACE = PREFIX+'painted cement fretwork'
CUT = PREFIX+'sheltered stone returns'
FINISH = PREFIX+'worn stone coping'
PLINTH = PREFIX+'grey projecting slab'
BEAD = PREFIX+'raised fillets'
DECK = PREFIX+'weathered cement deck'
PIER = PREFIX+'shallow warm plaster piers'

def pigment(rgb, roughness):
    v = np.array(rgb)/255
    linear = np.where(v<=.04045, v/12.92, ((v+.055)/1.055)**2.4)
    return dict(color=linear.tolist(),roughness=roughness)

PALETTE = {FACE:pigment((181,177,162),.88), CUT:pigment((155,151,137),.88),
           FINISH:pigment((188,185,172),.84), PLINTH:pigment((151,149,138),.90),
           BEAD:pigment((191,188,173),.82), DECK:pigment((148,144,131),.92),
           PIER:pigment((188,181,162),.88)}
PALETTE[FACE] = dict(color=[1.,1.,1.],roughness=.87,texture=str(Path(__file__).parent/'historic-balcony-plaster.jpg'))
TANGENTS = np.diff(PATH,axis=0)
LENGTH = np.linalg.norm(TANGENTS,axis=1)
TANGENTS /= LENGTH[:,None]
INWARD = TANGENTS[:,[1,0]]*[-1,1]
MITER = [INWARD[0]]
for before,after in zip(INWARD,INWARD[1:]):
    MITER.append((before+after)/(1+before@after))
MITER = np.array([*MITER,INWARD[-1]])

# Centre readings from four physically rectified current exterior panels and
# separately checked against the vehicle-era photograph. The returns contain
# one motif each. The broad front face contains two individual motifs.
MOTIFS = [(0,.672,.502), (1,.724,.504), (1,1.676,.502), (2,.545,.507)]
# Outline of the top light. The other three rotate about the centre boss.
# Coordinates describe the actual through-opening, including the clipped corners.
PETAL = np.array([[-.112,.286],[.106,.286],[.165,.227],[.030,.073],[-.021,.073],[-.166,.227]])
BOSS = np.array([[-.078,-.012],[-.012,-.077],[.012,-.077],[.078,-.012],
                 [.078,.012],[.012,.077],[-.012,.077],[-.078,.012]])
FRONT_INSET = .055
SCREEN_DEPTH = .050


def loc(face,u,depth):
    # Only the solid ends of each bay are mitred. The openings and the fronts of
    # their diagonal bars are normal extrusions of the surveyed photographic plane.
    left=max(0.,1-u/.12)
    right=max(0.,1-(LENGTH[face]-u)/.12)
    offset=INWARD[face]+left*(MITER[face]-INWARD[face])+right*(MITER[face+1]-INWARD[face])
    return PATH[face]+u*TANGENTS[face]+depth*offset


def mapper(face):
    def position(u,z,outward):
        x,y=loc(face,u,-outward)
        return x,y,z
    return position


def band(builder,face,lo,hi,material,label):
    rings=[]
    for u in (0.,LENGTH[face]):
        rings.append([(*loc(face,u,d),z) for d,z in
                      [(lo[1],lo[0]),(lo[2],lo[0]),(hi[2],hi[0]),(hi[1],hi[0])]])
    faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    builder.add(np.concatenate(rings),faces,material,PREFIX+label)


def section(builder,face,levels,name,low):
    for i,(lower,upper) in enumerate(zip(levels,levels[1:])):
        band(builder,face,lower[:3],upper[:3],upper[3],f'{name} face {face+1}, profile {i+1}')



def bevelled_screen(builder,face,width,holes):
    # The thin chamfer around each visible opening meets a perpendicular reveal.
    # Build both skins and their mitred rings as one closed, editable stone panel.
    outer=np.array([[0.,.065],[width,.065],[width,.892],[0.,.892]])
    expanded=[]
    for loop in holes:
        delta=np.roll(loop,-1,axis=0)-loop
        delta/=np.linalg.norm(delta,axis=1)[:,None]
        # Hole loops are clockwise; their left normal points away from the aperture.
        outward=delta[:,[1,0]]*[-1,1]
        previous=np.roll(outward,1,axis=0)
        expanded.append(loop+.0055*(previous+outward)/(1+(previous*outward).sum(1))[:,None])
    back=-FRONT_INSET-SCREEN_DEPTH
    lip=-FRONT_INSET
    start_bevel=lip-.008
    vertices,faces,registry=[],[],{}
    pos=mapper(face)
    def index(pt,depth):
        u,z=pt
        key=(round(float(u),8),round(float(z),8),round(depth,6))
        if key not in registry:
            registry[key]=len(vertices)
            vertices.append(pos(u,z,depth))
        return registry[key]
    def side(loop_a,z_a,loop_b,z_b):
        for i,p in enumerate(loop_a):
            j=(i+1)%len(loop_a)
            faces.append((index(p,z_a),index(loop_a[j],z_a),index(loop_b[j],z_b),index(loop_b[i],z_b)))
    for contours,depth,front in [(holes,back,False),(expanded,lip,True)]:
        skin=Polygon(outer,contours)
        for tri in constrained_delaunay_triangles(skin).geoms:
            coords=np.asarray(tri.exterior.coords)[:3]
            x,z=coords[1]-coords[0]
            u,v=coords[2]-coords[0]
            ids=[index(pt,depth) for pt in coords]
            faces.append(ids if ((x*v-z*u)>0)==front else ids[::-1])
    side(outer,back,outer,lip)
    for nominal,wide in zip(holes,expanded):
        side(nominal,back,nominal,start_bevel)
        side(nominal,start_bevel,wide,lip)
    builder.add(vertices,faces,FACE,PREFIX+f'bevelled open X screen {face+1}')


def add_street_balcony(builder,lod=False):
    low = lod is True or lod in ('low','lod','distant')
    first_part=len(builder.parts)
    for face in range(3):
        width=LENGTH[face]
        opening_polygons=[]
        pos=mapper(face)
        for index,(where,centre,z0) in enumerate(MOTIFS):
            if where!=face:
                continue
            # Rectangular fretwork cut through the parapet. Rotating the one
            # six-corner template retains the four solid diagonal arms of the X.
            for turn in range(4):
                angle=turn*np.pi/2
                rot=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
                opening_polygons.append(PETAL@rot.T+[centre,z0])
            patch=Polygon((np.array([[-.078,0.],[0.,-.077],[.078,0.],[0.,.077]]) if low else BOSS)+[centre,z0])
            builder.prism(patch,-FRONT_INSET-.002,-FRONT_INSET+.019,pos,
                          FACE,label=PREFIX+f'chamfered central boss {index+1}')
        wall = Polygon([(0.,.065),(width,.065),(width,.892),(0.,.892)],opening_polygons)
        assert wall.is_valid
        if low:
            builder.prism(wall,-FRONT_INSET-SCREEN_DEPTH,-FRONT_INSET,pos,FACE,
                          label=PREFIX+f'open X screen {face+1}')
        else:
            bevelled_screen(builder,face,width,opening_polygons)
        # Each pierced field sits slightly behind plain end and intermediate piers.
        # Shadowed vertical edges are visible on the central panel pairs in 2018.
        centres=[u for f,u,z in MOTIFS if f==face]
        stops=[0.]
        for c in centres:
            stops.extend([c-.338,c+.338])
        stops.append(width)
        for i,(lo,hi) in enumerate(zip(stops[::2],stops[1::2])):
            shell=Polygon([(lo,.067),(hi,.067),(hi,.885),(lo,.885)])
            builder.prism(shell,-FRONT_INSET-.003,-FRONT_INSET+.021,pos,PIER,
                          label=PREFIX+f'plain pier of panel {face+1}.{i+1}')
        # A shallow drop below the stone sill follows the three measured facets.
        slab=[(-.210,.105,.25,CUT),(-.184,.102,.25,CUT),(-.154,.050,.25,FINISH),
              (-.129,.005,.25,BEAD),(-.108,-.010,.25,FINISH),(-.023,-.011,.25,PLINTH),
              (0.,.001,.25,BEAD),(.052,.023,.230,FINISH),(.071,.044,.211,BEAD)]
        if low:slab=[slab[i] for i in (0,2,4,5,6,8)]
        section(builder,face,slab,'projecting balcony sill',low)
        cap=[(.875,.051,.183,FACE),(.888,.037,.198,BEAD),(.899,.015,.216,FINISH),
             (.914,0.,.224,BEAD),(.949,0.,.224,FINISH),(.960,.013,.213,FINISH)]
        if low:cap=[cap[i] for i in (0,2,3,4,5)]
        section(builder,face,cap,'continuous coping',low)
    # The railing ends are attached to the facade. Close the visible walkable slab
    # up to that wall and leave the lower storey and modern entrance outside the model.
    inner=PATH+MITER*.185
    left=inner[0]+(inner[1]-inner[0])*(-inner[0,1]/(inner[1,1]-inner[0,1]))
    right=inner[-1]+(inner[-2]-inner[-1])*(-inner[-1,1]/(inner[-2,1]-inner[-1,1]))
    plan=np.vstack([left,inner[1:-1],right])
    deck=Polygon(plan)
    assert deck.is_valid
    builder.prism(deck,-.150,.003,lambda x,y,z:(x,y,z),DECK,label=PREFIX+'balcony floor')
    # A slightly oblique mapping also gives the deep edges of the four openings
    # nonzero UV area. All UVs stay inside the one original cement-grain image.
    for part in builder.parts[first_part:]:
        if part['material']==FACE:
            x,y,z=np.array(part['vertices']).T
            part['texcoords']=np.column_stack(((x+.40*y+.21*z+2.8)/5.6,
                                               (.13*x-.65*y-.65*z+1.05)/2.1)).tolist()
