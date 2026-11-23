"""The two glazed upper winter gardens, their projecting soffits and plaster parapets."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from central_front import PLASTER, COPING, FRAME, PIPE, RAILING, material

MEASURE = Path(__file__).resolve().parents[1]/'measurements'
GLASS = 'Winter gardens | cool reflected glazing'
HINGE = 'Winter gardens | slightly brighter casement metal'
PALETTE = {GLASS:{**material((116,133,137),.25,.09),'alpha':.70},
           HINGE:material((73,76,68),.50,.26)}

def winter_garden_layout():
    garden=json.loads((MEASURE/'garden-cameras.json').read_bytes())
    windows=json.loads((MEASURE/'winter-garden-glazing.json').read_bytes())
    return garden,windows

def arc_xy(cx,radius,angle):
    a=np.radians(angle)
    return (cx+radius*np.sin(a),-radius*np.cos(a))

def local_radius(radius,angle,returns):
    if not returns:
        return radius
    knots,offsets=zip(*returns)
    return radius+np.interp(angle,knots,offsets,left=0,right=0)

def arc_polygon(cx,outer,start,stop,segments,inner=0,returns=()):
    count=max(1,round(segments*(stop-start)/180))
    angles=np.linspace(start,stop,count+1)
    if returns:
        angles=np.unique(np.r_[angles,[v[0] for v in returns if start<v[0]<stop]])
    points=[arc_xy(cx,local_radius(outer,a,returns),a) for a in angles]
    if inner:
        points.extend(arc_xy(cx,local_radius(inner,a,returns),a) for a in angles[::-1])
    elif stop-start<179.99:
        points.append((cx,0))
    return Polygon(points)

def open_sash(face,lo,hi,sill,transom,angle,lod):
    width=hi-lo
    hinge=face.point(lo,0,0)
    far=hinge+(face.t*np.cos(np.radians(angle))+face.n*np.sin(np.radians(angle)))*width
    sash=Facade(face.builder,hinge[:2],far[:2],face.label+'/outward left casement')
    rect=box(-width/2,sill,width/2,transom)
    pane=rect.buffer(-.026,join_style=2)
    sash.prism(rect.difference(pane),-.018,.014,HINGE,'thin opening iron frame')
    sash.prism(pane,-.014,-.007,GLASS,'tilted light')
    if not lod:
        for height in (sill+.10,transom-.10):
            face.builder.tube([face.point(lo,height-.035,.011),face.point(lo,height+.035,.011)],.009,FRAME,8,face.label+'/hinge')

def glazing(b,cx,radius,angles,sill,head,opening,title,lod,returns):
    start,stop=angles
    wall=Facade(b,arc_xy(cx,local_radius(radius,start,returns),start),arc_xy(cx,local_radius(radius,stop,returns),stop),title)
    half=wall.length/2
    border=.040 if not lod else .044
    inner=box(-half+border,sill+border,half-border,head-border)
    transom=sill+.765*(head-sill)
    bars=[box(-half,transom-.018,half,transom+.018),
          box(-.018,sill, .018,transom)]
    openings=inner.difference(unary_union(bars))
    frames=box(-half,sill,half,head).difference(openings)
    wall.prism(frames,-.025,.016,FRAME,'transom jambs and meeting stile')
    for light in openings.geoms:
        centre=light.centroid
        if opening and centre.x<0 and centre.y<transom:
            open_sash(wall,-half+border,-.018,sill+border,transom-.018,60,lod)
        else:
            wall.prism(light,-.028,-.020,GLASS,'fixed light')

def add_winter_gardens(b,lod=False):
    for name,specification in PALETTE.items():
        b.palette.setdefault(name,specification)
    garden,windows=winter_garden_layout()
    for side in ('SW','NE'):
        cx=garden['centres_m'][side]
        eave=garden['outer_radii_m'][side]
        lower=garden['midfloor_radii_m'][side]
        radius=windows['radii_m'][side]
        apron=eave-garden['window_recess_m']
        roof=eave-garden['crown_recess_m']
        soffit=garden['middle_slab_underside_z']
        eavez=garden['eave_soffit_z']
        parapetz=garden['upper_parapet_z']
        sillz=garden['window_sill_z']
        openings=windows['aperture_angles_deg'][side]
        z0,z1=windows['sill_z'],windows['head_z']
        prefix=side+' winter garden | '
        n=26 if lod else 72
        returns=windows['western_jamb_returns_m'].get(side,())
        def band(outer,inner,bottom,top,material,label,start=-90,stop=90,cut=None,profile=()):
            shape=arc_polygon(cx,outer,start,stop,n,inner,profile)
            if cut is not None:
                shape=shape.difference(cut)
            b.plan_prism(shape,bottom,top,material,prefix+label)
        # Adjacent gallery slabs occupy the rectangle between the two arc centers.
        # Trim the half-discs at that polygon so the undersides have one exterior skin.
        between=box(garden['centres_m']['SW'],-3.065,garden['centres_m']['NE'],.91)
        band(lower,0,soffit,soffit+.15,COPING,'lower cantilever soffit',cut=between)
        band(apron,apron-.16,soffit+.15,sillz-.067,PLASTER,'solid apron below glazing')
        band(apron+.025,apron-.18,sillz-.067,sillz,COPING,'round apron coping')
        band(radius+.050,radius-.15,sillz,z0,PLASTER,'sill below flat glazing',profile=returns)
        band(radius+.050,radius-.15,z1,eavez,PLASTER,'roughcast spandrel over glazing',profile=returns)
        begin=-90.
        for i,(start,stop) in enumerate(openings):
            band(radius+.050,radius-.15,z0,z1,PLASTER,'masonry pier '+str(i+1),begin,start,profile=returns)
            glazing(b,cx,radius,[start,stop],z0,z1,side=='SW' and i==1,prefix+'window '+str(i+1),lod,returns)
            begin=stop
        band(radius+.050,radius-.15,z0,z1,PLASTER,'last masonry pier',begin,90.,profile=returns)
        band(eave,0,eavez,eavez+.195,COPING,'projecting upper slab')
        band(roof,roof-.185,eavez+.195,parapetz-.032,PLASTER,'roof parapet')
        band(roof+.012,roof-.19,parapetz-.032,parapetz,COPING,'roof parapet coping')
        # A thin dark crown is visible against the plants and main wall in both views.
        angles=np.linspace(-89.6,89.6,21 if lod else 69)
        pts=[[*arc_xy(cx,roof-.075,v),parapetz+.026] for v in angles]
        b.tube(pts,.017,RAILING,6 if lod else 9,prefix+'dark top bead')
        # Both opposite views show the black rainwater leader beside the glazing.
        a=49.5 if side=='SW' else -42.25
        x,y=arc_xy(cx,local_radius(radius+.078,a,returns),a)
        b.tube([(x,y,sillz+.025),(x,y,eavez-.012)],.034,PIPE,6 if lod else 10,prefix+'cast iron downpipe')
    return garden,windows
