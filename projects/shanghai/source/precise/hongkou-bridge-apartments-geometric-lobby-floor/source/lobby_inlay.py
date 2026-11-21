"""Hand-drawn planar mineral inlays based on the December 2013 photograph of the Bridge Apartments lobby."""
from functools import lru_cache
from pathlib import Path
from random import Random
import numpy as np
from PIL import Image
from shapely.affinity import rotate,scale
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

GOLD='Warm ochre mineral field'
BORDER='Amber interior border'
BLACK='Charcoal geometric inlay'
RED='Terracotta square and pencil rules'
INNER='Light ochre matrix between charcoal bands'
PALE='Buff surrounding lobby floor'
JOINT='Dark perimeter joint'
EDGE='Section through aggregate bed'
PALETTE={label:{'color':rgb,'roughness':rough} for label,rgb,rough in [
 (GOLD,[.78,.59,.295],.84),(BORDER,[.69,.47,.232],.84),(BLACK,[.043,.047,.053],.74),
 (INNER,[.785,.607,.33],.84),(RED,[.55,.245,.115],.8),(PALE,[.72,.68,.49],.83),(JOINT,[.12,.115,.092],.9),(EDGE,[.33,.30,.248],.94)]}
C=(196,202)
S=.0045
Z=.066

def texture(path):
    rng=np.random.default_rng(399)
    # Neutral aggregate under all material colors. No pixels are sampled from the photograph.
    n=560
    fine=rng.normal(0,7,(n,n));flecks=rng.random((n,n))
    fine[flecks<.019]-=rng.uniform(29,53,size=np.sum(flecks<.019))
    fine[flecks>.982]+=rng.uniform(7,17,size=np.sum(flecks>.982))
    v=np.clip(231+fine,156,253).astype('uint8')
    Image.fromarray(np.repeat(v[:,:,None],3,axis=2)).save(path)

def rotate4(shape):
    return unary_union([rotate(shape,90*i,origin=C) for i in range(4)])

@lru_cache(maxsize=2)
def plan(detailed):
    # Pixel coordinates refer to the rectified reference plane. The four corners
    # turn clockwise, and the center has two offset, connected square registers.
    bounds=box(-18,-18,418,418)
    field=box(0,0,400,400)
    inner_border=box(48,53,344,351)
    outer_rule=box(76,82,316,322).difference(box(82,88,310,316))
    center=box(156,162,236,242)
    center_line=box(148,154,244,250).difference(center)
    arm=unary_union([
      box(120,127,272,141),box(163,113,260,137),
      box(203,85,219,162),box(259,129,273,181)])
    corner=unary_union([
      box(76,82,132,110),box(76,92,88,193),box(78,180,119,194),
      box(76,13,83,88),box(91,13,99,88),box(107,13,115,88)])
    black=unary_union([center_line,rotate4(arm),rotate4(corner)])
    # Very slightly softened inlay corners on close inspection, recorded on
    # the same plane as the matrix rather than represented by a raised plate.
    if detailed:
        black=black.buffer(.34,quad_segs=3,join_style='round').buffer(-.34,quad_segs=3,join_style='round')
    else:
        black=black.buffer(.34,quad_segs=1,join_style='round').buffer(-.34,quad_segs=1,join_style='round')
    perimeter=field.difference(field.buffer(-2.2,join_style='mitre'))
    red=unary_union([outer_rule,center]).difference(black)
    areas=[('Charcoal four-corner ribbons and offset cross bands',BLACK,black),
           ('Terracotta center and narrow square surround',RED,red),
           ('Dark joint enclosing the square panel',JOINT,perimeter)]
    used=unary_union([black,red,perimeter])
    inside=box(82,88,310,316).difference(used)
    areas.append(('Pale matrix between the inner bands',INNER,inside))
    used=unary_union([used,inside])
    ochre=inner_border.difference(used)
    areas.extend([('Amber border and inner field',BORDER,ochre),
                  ('Outer ochre band',GOLD,field.difference(unary_union([used,ochre]))),
                  ('Pale floor returned beyond the panel',PALE,bounds.difference(field))])
    assert abs(sum(s.area for _,_,s in areas)-bounds.area)<1e-5, (sum(s.area for _,_,s in areas)-bounds.area,black.bounds,perimeter.intersection(black).area,perimeter.intersection(red).area)
    return areas

def world(u,v):
    return ((u-200)*S,(200-v)*S)

def add_building(b,lod):
    tex=str(Path(__file__).with_name('original-aggregate.png'))
    for name in (PALE,BORDER,GOLD,BLACK,RED,JOINT,INNER):b.palette[name]['texture']=tex
    b.box((0,0,.025),(436*S,436*S,.05),EDGE,label='Neutral cut edge of the floor sample')
    for label,mat,region in plan(not lod):
        polys=list(region.geoms) if region.geom_type=='MultiPolygon' else [region]
        for idx,g in enumerate(polys):
            if g.area<1e-4:continue
            b.prism(scale(g,yfact=-1,origin=(0,0)),.05,Z,lambda u,v,z: (*world(u,-v),z),mat,label)
    for part in b.parts:
        if part['material']!=EDGE:
            part['texcoords']=[[(x+1.0)/2.,(1.-y)/2.] for x,y,z in part['vertices']]
