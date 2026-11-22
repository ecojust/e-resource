"""Cast bronze script, six steel members and the eight separate lights of the 2022 corner entrance."""
import json
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

DATA=Path(__file__).resolve().parents[1]/'measurements'
BRONZE='Brushed bronze 2022 script'
BRONZE_EDGE='Bronze letter edges'
STEEL='Dark steel fanlight'
GLASS='Smoky front glazing'
STONE='Grey stone reeded archivolt'


def pigment(rgb,roughness,metallic=0.,alpha=None):
    srgb=np.asarray(rgb,dtype=float)/255.
    values=np.where(srgb<.04045,srgb/12.92,((srgb+.055)/1.055)**2.4)
    result=dict(color=values.tolist(),roughness=roughness,metallic=metallic)
    if alpha is not None:result['alpha']=alpha
    return result


PALETTE={BRONZE:pigment([167,139,102],.55,.49),
         BRONZE_EDGE:pigment([130,103,77],.66,.38),
         STEEL:pigment([52,53,52],.66,.34),
         GLASS:pigment([93,103,102],.30,.10,.76),
         STONE:pigment([157,149,138],.9)}


def pieces(shape):
    if shape.is_empty:return []
    if shape.geom_type=='Polygon':return [shape]
    return [p for g in shape.geoms for p in pieces(g)]


def read(name):
    return json.loads((DATA/name).read_bytes())


def steel_members():
    records=read('2022-fanlight-members.json')['members']
    shapes=[]
    rail=LineString(records[-1]['centreline'])
    def meet_rail(edge,end):
        tip=np.asarray(edge[end],float)
        direction=tip-np.asarray(edge[4 if end==0 else -5])
        direction/=np.linalg.norm(direction)
        path=LineString([tip,tip+direction*90.])
        hit=rail.intersection(path)
        if hit.geom_type=='Point' and not hit.is_empty:
            joint=list(hit.coords[0])
            return [joint,*edge] if end==0 else [*edge,joint]
        return edge
    for rec in records:
        a,b=rec['edge_a'],rec['edge_b']
        if rec['member']=='inner arch':
            # The photographed strip disappears into the sill rebate at both
            # springs. Continue the last visible millimetres to the joint.
            a,b=meet_rail(meet_rail(a,0),-1),meet_rail(meet_rail(b,0),-1)
        if 'spoke' in rec['member']:
            a,b=meet_rail(a,0),meet_rail(b,0)
        shape=Polygon(a+b[::-1]).buffer(0)
        shapes.append((rec['member'],shape))
    return records,shapes


def fanlight_aperture():
    """Outline to subtract from the main masonry face, in upright original pixels."""
    records,_=steel_members()
    return Polygon(records[0]['edge_b']).buffer(0)


def on_plane(shape,position,depth):
    def to_wall(ring):
        return [position(u,v,depth)[[0,2]]for u,v in ring.coords]
    return orient(Polygon(to_wall(shape.exterior),[to_wall(h)for h in shape.interiors]),sign=1.)


def cast(builder,shape,position,front,back,material,label,lod,reference_y=None):
    # The measured front is projected independently at its visible depth. Each
    # shell has continuous sides and a solid back, including all stroke holes.
    for p in pieces(shape):
        if p.area<5:continue
        p=p.simplify(1.45 if lod else .52,preserve_topology=True)
        s=on_plane(p,position,front if reference_y is None else reference_y)
        if not s.is_valid:s=s.buffer(0)
        builder.prism(s,-back,-front,lambda x,z,d:(x,-d,z),material,label)



def cast_script(builder,shape,position,front,back,material,label,lod):
    # Both the face and the return stop at the photographed outline. The
    # hidden back follows the relevant rays to the plaque, keeping the small
    # photographed voids visible through the inferred letter thickness.
    for p in pieces(shape):
        if p.area<5:continue
        p=p.simplify(.95 if lod else .45,preserve_topology=True)
        up=orient(affinity.scale(p,xfact=1.,yfact=-1.,origin=(0,0)),sign=1.)
        builder.prism(up,-back,-front,lambda u,z,d:position(u,-z,-d),material,label)

def add_fanlight(builder,lod,position,frame_y,letter_wall_y):
    records,members=steel_members()
    # The three radial spokes are secured at a common hub. The two arcs,
    # spokes and spring rail retain their separate editable solid sections.
    depths=[.0,.004,.010,.012,.014,.008]
    for (name,shape),offset in zip(members,depths):
        cast(builder,shape,position,frame_y-offset,frame_y+.043,STEEL,'Fanlight '+name,lod)

    # Each pane extends inside the steel rebate. Its cut edge stops a few
    # millimetres short of the steel centreline. The visible daylight outline
    # remains the dark frame, including when viewed square-on or obliquely.
    opening=Polygon(records[0]['centreline']).buffer(0)
    separators=[]
    for member in records[1:]:
        points=np.array(member['centreline'])
        start=points[0]-points[3];start/=np.linalg.norm(start)
        end=points[-1]-points[-4];end/=np.linalg.norm(end)
        # Extend the hidden intersections into the sill, hub and outer arch.
        length=28.
        extended=np.vstack((points[0]+length*start,points,points[-1]+length*end))
        separators.append(LineString(extended).buffer(1.1,cap_style='flat'))
    panes=sorted((p for p in pieces(opening.difference(unary_union(separators)))if p.area>2000.),
                 key=lambda p:(int(p.centroid.y//300),p.centroid.x))
    if len(panes)!=8:raise ValueError(f'Expected eight separate lights, found {len(panes)}')
    for i,pane in enumerate(panes,1):
        cast(builder,pane,position,frame_y+.021,frame_y+.030,GLASS,
             'Fanlight individual pane '+str(i),lod,reference_y=frame_y)

    for record in read('2022-raised-sign.json')['letters']:
        letter=record['character']
        for i,part in enumerate(record['components'],1):
            p=Polygon(part['shell'],part['holes'])
            prefix='Corner sign '+letter+' '+str(i)
            cast_script(builder,p,position,letter_wall_y-.027,letter_wall_y+.001,BRONZE_EDGE,prefix+' edge',lod)
            cast_script(builder,p,position,letter_wall_y-.0285,letter_wall_y-.0268,BRONZE,prefix+' face',lod)
