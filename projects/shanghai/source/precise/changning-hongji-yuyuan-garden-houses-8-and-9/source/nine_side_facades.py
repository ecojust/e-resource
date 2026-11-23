"""The three projecting south gables, their connectors and the lawn-facing brass 9."""
from math import cos, pi, sin
from pathlib import Path
import json

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from garden_fabric import BOARD, BRASS, GLASS, LEDGE, METAL, PLINTH, STONE, TREAD, face
from house_nine_sashes import BEAD, EDGE, GLASS as SASH_GLASS, MOUNT, PLASTER, WOOD
from photo_architecture import opening

MEASURE = Path(__file__).resolve().parents[1] / 'measurements'


def arrangements():
    return json.loads((MEASURE/'nine-south-openings.json').read_bytes())


def south_openings():
    data = arrangements()
    faces = []
    for win in data['upper_windows']:
        l,r,lo,hi=win['window_y_min_y_max_z_min_z_max']
        faces.append((win['label'],win['outer_x'],box(l,lo,r,hi)))
    far=data['far_arch']
    arch=opening(far['center_y'],far['ground_z']-.015,far['outer_width'],far['outer_crown']+.015,
                 far['outer_crown']-far['spring_z'],32)
    faces.append(('far arched garden entrance',far['rake_x'],arch))
    slot=data['connector_slots']
    for j,(l,r,lo,hi) in enumerate(slot['runs_y_z'],1):
        faces.append(('connector '+str(j),slot['outer_x'],box(l,lo,r,hi)))
    return faces


def side(b,poly,x,front,back,material,label):
    b.prism(poly,x+front,x+back,lambda y,z,d:(d,y,z),material,'9 | '+label)


def south_window(b,lod,label,x,outline,connector):
    l,lo,r,hi=outline.bounds
    inside=outline.buffer(-.048,join_style=2)
    side(b,outline.difference(inside),x,.046,.154,WOOD,label+' frame')
    n=5 if connector else 2
    bottom,top=lo+.048,hi-.048
    for j in range(n):
        a=l+.048+(r-l-.096)*j/n;c=l+.048+(r-l-.096)*(j+1)/n
        if j:
            side(b,box(a-.026,bottom,a+.026,top),x,.073,.15,WOOD,label+' vertical bar')
        panel=box(a+(.026 if j else 0),bottom,c-(.026 if j<n-1 else 0),top)
        glass=SASH_GLASS[j%3] if not connector or j in (0,1,n-1) else PLINTH
        side(b,panel,x,.15,.169,glass,label+' light '+str(j+1))
        if not connector:
            for ratio in (.35,.68):
                z=bottom+(top-bottom)*ratio
                side(b,box(a,z-.011,c,z+.011),x,.100,.15,BEAD,label+' glazing bar')
    side(b,box(l-.045,lo-.105,r+.045,lo-.008),x,-.10,.020,PLASTER,label+' apron')
    if not connector:
        side(b,box(l-.09,hi+.006,r+.09,hi+.10),x,-.063,.018,PLASTER,label+' head')
        side(b,box(l-.13,hi+.10,r+.13,hi+.157),x,-.121,.020,EDGE,label+' head lip')
        mid=(l+r)/2
        side(b,box(mid-.041,hi+.157,mid+.041,hi+.225),x,-.067,-.008,MOUNT,label+' top fixing')
    side(b,box(l-.075,lo-.047,r+.075,lo-.003),x,-.12,.021,EDGE,label+' sill')


def brass_nine(b,lod):
    l,r,y,lo,hi=json.loads((MEASURE/'nine-brass-number-plaque.json').read_bytes())['placement_m']
    face(b,box(l,lo,r,hi),y,y+.068,BOARD,'9 | square number plaque')
    # The photographed open counter and the turned-up lower tail are independent
    # from the painted backing. The numeral occupies under half its width.
    x=(l+r)/2-.006;z=lo+.49*(hi-lo)
    rect_width=.427;rect_height=.587
    curves=[((.10,.28),(.16,-.02),(.69,-.18),(.89,.25)),
            ((.89,.25),(1.00,.46),(1.00,.72),(.90,.83)),
            ((.90,.83),(.75,1.08),(.35,1.07),(.15,.90)),
            ((.15,.90),(-.10,.66),(.04,.35),(.34,.33)),
            ((.34,.33),(.55,.29),(.70,.37),(.77,.47)),
            ((.77,.47),(.75,.21),(.57,.03),(.39,.12)),
            ((.39,.12),(.30,.14),(.24,.23),(.23,.27))]
    def local(t):
        return x+(t[0]-.5)*rect_width,z+(t[1]-.5)*rect_height
    edge=[]
    for q in curves:
        a,c,d,e=map(np.array,q)
        for t in np.linspace(0,1,5 if lod else 10,endpoint=False):
            edge.append(local((1-t)**3*a+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*e))
    edge.append(local(curves[-1][-1]))
    hole=[local((.491+.241*cos(a),.657+.180*sin(a)))for a in np.linspace(0,2*pi,20 if lod else 42,endpoint=False)]
    digit=Polygon(edge,[hole])
    face(b,digit,y-.043,y-.005,BRASS,'9 | raised brass numeral with counter')
    for zc in (z-.14,z+.13):
        face(b,box(x+.118,zc-.011,x+.154,zc+.012),y-.010,y+.002,METAL,'9 | number mounting stud')


def add_facades(b,lod,layout):
    for label,x,ap in south_openings():
        if 'arched' not in label:
            south_window(b,lod,label,x,ap,label.startswith('connector'))
            continue
        clear=ap.buffer(-.135,join_style=2)
        side(b,ap.difference(clear),x,-.073,.135,STONE,'far arch stone surround')
        rim=clear.buffer(-.048,join_style=2)
        side(b,clear.difference(rim),x,.084,.169,METAL,'far arch dark frame')
        side(b,rim,x,.168,.187,GLASS,'far arch recessed glazing')
        l,lo,r,hi=rim.bounds;mid=(l+r)/2
        for y in (mid-.40,mid+.40):
            side(b,rim.intersection(box(y-.029,lo,y+.029,hi)),x,.096,.165,METAL,'far arch meeting rail')
        side(b,rim.intersection(box(l,1.14,r,1.20)),x,.087,.161,METAL,'far arch horizontal bar')
    brass_nine(b,lod)
