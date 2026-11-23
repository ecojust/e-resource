"""Model the entrance's raised wave, divided lintel and lobed central cartouche."""
from math import cos, pi, sin
from pathlib import Path
import json
import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import LineString, Polygon, box
from street_materials import CREAM, GREEN, LIME, SHADE

EVIDENCE=json.loads((Path(__file__).resolve().parents[1]/'measurements/portal-profile.json').read_text())
def add_portal(face,hole,lod):
    x0,z0,x1,head=hole.bounds
    # Two corners of the door head register the nearly frontal detail. The profile
    # heights are constrained by the adjacent full-height registered street view.
    def located(px,py):
        t=(px-407)/(631-407)
        return (x0+t*(x1-x0),head+(428-py)*.00533)
    def convert(path):
        return [located(u,v) for u,v in path]
    label='central entrance | '
    x,z=located(410,348);a,b=located(630,426)
    face.rect(x,a,b,z,.144,.183,CREAM,label+'decorated lintel')
    wave=EVIDENCE['wave_upper_profile_px']
    vx,vy=np.array(wave).T
    xx=np.linspace(vx.min(),vx.max(),32 if lod else 80)
    edge=convert(zip(xx,PchipInterpolator(vx,vy)(xx)))
    body=Polygon([*edge,(edge[-1][0],z-.014),(edge[0][0],z-.014)])
    face.solid(body,.145,.212,CREAM,label+'double wave crest')
    face.band(edge,.019,.207,.226,LIME,label+'raised wave bead')
    for u in [444,480,518,554,591]:
        x,v=located(u,350)
        face.rect(x-.007,x+.007,head+.045,v,.182,.194,LIME,label+'six lintel divisions')
    for u in [457,492,533,568]:
        for v in [370,396]:
            x,z=located(u,v)
            face.solid(Polygon([(x-.014,z),(x,z+.017),(x+.014,z),(x,z-.017)]),
                       .184,.200,LIME,label+'small diamond bosses')
    detail=convert(EVIDENCE['cartouche_outline_px'])
    face.band([*detail,detail[0]],.018,.154,.185,CREAM,label+'lobed medallion moulding')
    x,z=located(517,237)
    bud=[(x+.039*cos(a),z+.032*sin(a)) for a in np.linspace(0,2*pi,12 if lod else 24,endpoint=False)]
    face.solid(Polygon(bud),.154,.179,LIME,label+'central medallion bud')
    for u in [425,610]:
        x,z=located(u,385)
        ring=[(x+.033*cos(a),z+.038*sin(a)) for a in np.linspace(0,2*pi,12 if lod else 24)]
        face.band(ring,.012,.184,.198,LIME,label+'terminal discs')
    # The darker gate is slatted. Extra signs and electrical cabinets vary by date.
    mid=(x0+x1)/2
    for x in np.linspace(x0+.085,x1-.085,7 if lod else 14):
        face.rect(x-.009,x+.009,head*.45,head-.09,-.091,-.073,GREEN,label+'upper gate bars')
    for z in np.linspace(.12,head*.43,7 if lod else 12):
        face.rect(x0+.045,x1-.045,z-.012,z+.012,-.092,-.065,GREEN,label+'lower gate louvres')
