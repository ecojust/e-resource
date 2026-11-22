"""Painted window surrounds, transoms and sashes on the south street wall."""
import json
from math import hypot
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

SURVEY = Path(__file__).resolve().parents[1]/'measurements/upper-sashes-and-street-sign-line.json'
STONE = 'Hengchang windows | white stucco'
BEAD = 'Hengchang windows | pale moulded lip'
KEY = 'Hengchang windows | weathered keystone'
OCHRE = 'Hengchang windows | ochre lunette'
FILL = 'Hengchang windows | light side infill'
TIMBER = 'Hengchang windows | dark painted sash'
PAINT = 'Hengchang windows | light painted frame'
MIDSHADE = 'Hengchang windows | shaded frame rebate'
GLASS = 'Hengchang windows | muted green glass'
GLASS_LIGHT = 'Hengchang windows | pale reflected glass'
GLASS_DARK = 'Hengchang windows | shaded transom glass'
BLIND = 'Hengchang windows | lowered shutter'
SLAT = 'Hengchang windows | blind slat edge'
GREEN = 'Hengchang windows | blue green sheet'
GREEN_EDGE = 'Hengchang windows | dark sheet edge'
RED = 'Hengchang windows | red brown upper backing'
IRON = 'Hengchang windows | oxidised narrow metal'
BRASS = 'Hengchang windows | worn metal latch'


def paint(rgb, roughness, metallic=0.):
    def linear(value):
        c=value/255.
        return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    return {'color':[linear(v) for v in rgb],'roughness':roughness,'metallic':metallic}


PALETTE={
    STONE:paint((220,216,205),.91),BEAD:paint((237,233,217),.83),
    KEY:paint((209,204,189),.9),OCHRE:paint((179,151,110),.89),
    FILL:paint((198,200,192),.88),TIMBER:paint((71,64,55),.64),
    PAINT:paint((208,211,201),.64),MIDSHADE:paint((104,105,96),.7),
    GLASS:paint((110,128,125),.31,.15),GLASS_LIGHT:paint((137,151,147),.32,.14),
    GLASS_DARK:paint((76,90,90),.32,.14),BLIND:paint((106,108,94),.84),
    SLAT:paint((136,136,121),.76),GREEN:paint((46,98,98),.6,.13),
    GREEN_EDGE:paint((53,77,74),.72,.1),RED:paint((120,69,59),.82),
    IRON:paint((71,73,68),.68,.25),BRASS:paint((156,146,112),.57,.29)}


def _rectify(xy,H):
    uv=np.atleast_2d(np.asarray(xy,dtype=float))
    q=np.column_stack((uv,np.ones(len(uv)))) @ np.asarray(H).T
    return q[:,:2]/q[:,2,None]


def _polygon(uv,H):
    return Polygon(_rectify(uv,H))


def _profile(trace,H,coarse=False):
    points=_rectify(trace['upper'],H)
    curved=[]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        prev=points[max(0,i-1)]
        nxt=points[min(len(points)-1,i+2)]
        for t in np.linspace(0,1,3 if coarse else 6,endpoint=False):
            curved.append(.5*((2*a)+(-prev+b)*t+(2*prev-5*a+4*b-nxt)*t*t+(-prev+3*a-3*b+nxt)*t**3))
    return Polygon([*curved,points[-1],*_rectify(trace['bottom_right_then_left'],H)])


def _windows():
    return json.loads(SURVEY.read_bytes())['windows']


def _recent_window():
    survey=json.loads((SURVEY.parent/'refurbished-tower-window.json').read_bytes())
    left,sill,right,head=survey['bounds_xz']
    return np.array([[left,head],[right,head],[right,sill],[left,sill]]),survey['mullions']


def _old(layout):
    return str(layout.get('period','2022')).startswith('2018')


def opening_faces(layout):
    return {name:win['face'] for name,win in _windows().items()}


def opening_profiles(layout):
    result={}
    for name,w in _windows().items():
        H=layout['native_to_xz'][w['face']]
        if name=='tower' and not _old(layout):
            result[name]=Polygon(_recent_window()[0])
        else:
            result[name]=_profile(w['inner'],H)
    return result


def _parts(shape):
    if shape.is_empty:
        return []
    if shape.geom_type=='Polygon':
        return [shape] if shape.area>1.e-7 else []
    return [p for g in getattr(shape,'geoms',()) for p in _parts(g)]


def _line(a,b,half_width):
    return LineString([a,b]).buffer(half_width,cap_style=2,join_style=2)


def _band_between(quad,frac):
    top_l,top_r,bottom_r,bottom_l=quad
    return (1-frac)*top_l+frac*top_r,(1-frac)*bottom_l+frac*bottom_r


def _openings_in_frame(draw,field,bars,material,opening_mats,label,face_front):
    # The rebate, face and glass all share the same outer profile. Only the
    # visible glass fields are backed, so no second full sheet crosses the rails.
    rails=unary_union(bars)
    panes=sorted(_parts(field.difference(rails)),key=lambda p:(round(p.centroid.x,2),p.centroid.y))
    frame=set_precision(field.difference(unary_union(panes)),.00002).simplify(.000009,preserve_topology=True)
    draw(frame,face_front,face_front+.048,material,label+' frame and bars')
    for i,shape in enumerate(panes):
        draw(shape,face_front+.048,face_front+.061,opening_mats[i%len(opening_mats)],label+f' pane {i+1}')


def _square(draw,name,w,H,quad,lod,recent=False):
    field=Polygon(quad)
    is_tower=name=='tower'
    horizontal=.050 if is_tower else .061
    rails=[field.difference(field.buffer(-horizontal,join_style=2))]
    positions=w['mullions']
    for f in positions:
        a,b=_band_between(quad,f)
        rails.append(_line(a,b,.032 if is_tower else .039))
    if is_tower and recent:
        a,b=_band_between(quad,positions[1]+.023)
        rails.append(_line(a,b,.014))
    material=PAINT if is_tower else TIMBER
    face_front=.045
    _openings_in_frame(draw,field,rails,material,[GLASS_LIGHT,GLASS_DARK,GLASS,GLASS_LIGHT],name,face_front)
    if is_tower:
        if not recent:
            a,b=_band_between(quad,positions[0])
            c,d=_band_between(quad,positions[1])
            blind=Polygon([a,c,d,b]).buffer(-.047,join_style=2)
            left,bottom,right,top=blind.bounds
            draw(blind,.080,.091,BLIND,'tower second bay lowered blind')
            for z in np.linspace(bottom+.024,top-.025,17 if lod else 48):
                draw(blind.intersection(box(left,z,right,z+.005)),.073,.080,SLAT,'tower blind slat')
            cx=left+.022
            z=.5*(bottom+top)
            draw(box(cx-.012,z-.055,cx+.012,z+.055),.052,.080,BRASS,'tower blind catch')
        return
    # The small iron curls occur only in the first rectangular light.
    a,b=_band_between(quad,.06)
    c,d=_band_between(quad,positions[0]-.042)
    grill=Polygon([a,c,d,b]).buffer(-.035,join_style=2)
    x0,z0,x1,z1=grill.bounds
    Ht=z1-z0
    strokes=[]
    for f in (.18,.53,.86):
        x=x0+(x1-x0)*f
        strokes.append(_line((x,z0),(x,z1),.006))
    for f in (.18,.54,.80):
        z=z0+f*Ht
        r=(x1-x0)*.15
        for sign in (-1,1):
            cx=(x0+x1)*.5
            pts=[]
            for t in np.linspace(0,1,12 if lod else 22):
                pts.append((cx+sign*(r*(1-np.cos(t*1.65*np.pi))),z+r*np.sin(t*1.65*np.pi)))
            strokes.append(LineString(pts).buffer(.006,cap_style=2))
    draw(grill.intersection(unary_union(strokes)),.020,.037,IRON,'east-1 left light metal grille')


def _arched(draw,name,w,H,field):
    trans=_rectify(w['transom'],H)
    bottom=_rectify(w['sill'],H)
    x0,z0,x1,z1=field.bounds
    delta=trans[1]-trans[0]
    direction=delta/max(hypot(*delta),1e-7)
    start=trans[0]-direction*2
    end=trans[1]+direction*2
    upper=field.intersection(Polygon([start,end,end+[0,10],start+[0,10]]))
    lower=field.difference(upper)
    white=w['style']=='arched-white'
    mat=PAINT if white else TIMBER
    for panel,stiles,rows,label in [(upper,w['upper_stiles'],w['upper_rails'],'upper light'),(lower,w['lower_stiles'],w['lower_rails'],'lower lights')]:
        if panel.is_empty:continue
        bars=[panel.difference(panel.buffer(-(.048 if white else .042),join_style=2))]
        for f in stiles:
            a=(1-f)*trans[0]+f*trans[1]
            b=(1-f)*bottom[0]+f*bottom[1]
            v=b-a
            v/=np.linalg.norm(v)
            bars.append(_line(a-5*v,b+5*v,.024 if white else .018))
        for f in rows:
            if label=='upper light':
                h=(z1-np.mean(trans[:,1]))*f
                a,b=start+[0,h],end+[0,h]
            else:
                a=(1-f)*trans[0]+f*bottom[0]-direction
                b=(1-f)*trans[1]+f*bottom[1]+direction
            bars.append(_line(a,b,.023 if white else .019))
        glass=[GLASS,GLASS_LIGHT] if white else [GLASS_DARK,GLASS]
        _openings_in_frame(draw,panel,bars,mat,glass,name+' '+label,.05)
    draw(field.intersection(_line(start,end,.051 if white else .046)),.028,.05,mat,name+' principal transom')


def add_sashes(b,lod,layout):
    for name,w in _windows().items():
        face=w['face']
        H=layout['native_to_xz'][face]
        front=layout['front_y'][face]
        def draw(poly,near,far,mat,label):
            for part in _parts(poly):
                b.prism(part,-far,-near,lambda u,z,d:(float(u),float(front-d),float(z)),mat,label)
        recent=name=='tower' and not _old(layout)
        inner=_profile(w['inner'],H,lod)
        outer=_profile(w['outer'],H,lod)
        if not recent:
            frame=outer.difference(inner)
            draw(frame,-.055,.016,STONE,name+' moulded arch')
            edge=outer.difference(outer.buffer(-.022,join_style=2))
            draw(edge.intersection(frame),-.073,-.055,BEAD,name+' outer raised bead')
            lip=inner.buffer(.036,join_style=2).difference(inner)
            draw(lip.intersection(frame),-.086,-.055,BEAD,name+' inner bead')
            key=_polygon(w['key'],H).intersection(outer.buffer(.035))
            draw(key,-.110,-.055,KEY,name+' crown keystone')
        if 'sash_quad' in w:
            quad=_rectify(w['sash_quad'],H)
            if recent:
                quad,positions=_recent_window()
                w={**w,'mullions':positions}
            field=Polygon(quad)
            if not recent:
                filled=inner.difference(field)
                if name=='tower':
                    skirt=_polygon([[135,914],[1400,987],[1400,1375],[135,1375]],H)
                    for poly,mat in [(filled.intersection(skirt),FILL),(filled.difference(skirt),OCHRE)]:
                        draw(poly,.072,.137,mat,name+' side and lunette infill')
                    patch=_polygon(w['upper_red_patch'],H).intersection(filled)
                    draw(patch,.061,.072,RED,'tower reddish board above canopy')
                    camera=np.asarray(layout['native_camera'],dtype=float)
                    def projected_facet(uv,depth):
                        plane=camera[:,[0,2,3]].copy()
                        plane[:,2]+=camera[:,1]*(front+depth)
                        return _polygon(uv,np.linalg.inv(plane))
                    draw(projected_facet(w['awning_top'],-.235),-.235,-.025,GREEN,'tower folded green canopy')
                    draw(projected_facet(w['awning_front'],-.245),-.245,-.235,GREEN_EDGE,'tower canopy fascia')
                else:
                    draw(filled,.070,.136,FILL,name+' opaque arch head')
            _square(draw,name,w,H,quad,lod,recent)
        else:
            _arched(draw,name,w,H,inner)
