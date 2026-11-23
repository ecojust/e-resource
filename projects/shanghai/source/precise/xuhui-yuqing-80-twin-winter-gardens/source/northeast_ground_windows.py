"""The five faceted, glazed ground-floor openings below the northeast sunroom."""
from math import ceil, cos, radians, sin
from pathlib import Path
import json

import numpy as np
from shapely.geometry import Polygon, box
from central_front import PLASTER, COPING, FRAME, GLASS, PANEL, TERRACE, RAILING, PALETTE

HERE = Path(__file__).resolve().parent
SURVEY = HERE.parent / 'measurements' / 'northeast-ground-controls.json'


def radial(center, r, angle):
    a = radians(angle)
    return np.array([center[0]+r*sin(a), center[1]-r*cos(a)])


def shell(b, center, r, thickness, a, c, bottom, top, material, name, lod):
    angles = np.linspace(a, c, max(2,ceil((c-a)/(8 if lod else 3.2))+1))
    outer = [radial(center, r, t) for t in angles]
    inner = [radial(center, r-thickness, t) for t in reversed(angles)]
    b.prism(Polygon(outer+inner), bottom, top, lambda x,y,z:(x,y,z), material, name)


def window(b, center, r, start, end, low, high, meeting, panel, label):
    # A flat rolled-steel pair sits just behind its chord's two rendered jambs.
    left = radial(center,r,start)
    right = radial(center,r,end)
    axis = (right-left)/np.linalg.norm(right-left)
    outward = np.array([axis[1],-axis[0]])
    length = np.linalg.norm(right-left)
    def place(u,z,d):
        p=left+axis*u+outward*d
        return p[0],p[1],z
    def part(shape,back,front,mat,name):
        b.prism(shape,back,front,place,mat,'NE garden room | '+label+' | '+name)
    frame = box(0,low,length,high).difference(box(.034,low+.036,length-.034,high-.036))
    part(frame,-.095,-.033,FRAME,'rolled perimeter')
    # A curtain and painted bottom infill obscure the interior in both photographs.
    part(box(.025,low+.027,length-.025,high-.027),-.104,-.098,GLASS,'glazed pair')
    h=high-low
    part(box(.033,low+.032,length-.033,low+panel*h),-.093,-.076,PANEL,'opaque lower panels')
    part(box(length*meeting-.014,low+.022,length*meeting+.014,high-.018),-.073,-.034,FRAME,'centre meeting stiles')
    for i,f in enumerate((panel,.491,.690,.865)):
        z=low+h*f
        part(box(.020,z-.012,length-.020,z+.012),-.075,-.040,FRAME,
             ('panel head','lower glazing bar','upper glazing bar','opening transom')[i])


def forecourt(b, spec, lod):
    gate=spec['terrace']
    # The arc meets the existing straight garden run with its original rail heights.
    x0,y0=gate['junction_xy']
    rx,ry=gate['radii_m']
    def plan(t,d=0.0):
        a=radians(t)
        return np.array([x0+(rx+d)*sin(a), y0+ry-(ry+d)*cos(a)])
    def height(theta):
        # Small survey residual on the low edge: a common nominal height avoids a tapered coping.
        return gate['coping_z']
    angles=np.linspace(0,gate['end_angle_deg'],18 if lod else 44)
    path=[plan(a) for a in angles]
    backwards=[plan(a,-.22) for a in reversed(angles)]
    p=Polygon(path+backwards)
    b.prism(p,-.38,gate['coping_z']-.035,lambda x,y,z:(x,y,z),PLASTER,'NE forecourt | curved retaining wall')
    cap=Polygon([plan(a,.025) for a in angles]+[plan(a,-.245)for a in reversed(angles)])
    b.prism(cap,gate['coping_z']-.035,gate['coping_z'],lambda x,y,z:(x,y,z),COPING,'NE forecourt | pale coping')
    # Only the deck outside the solarium is exposed, the inner boundary ends behind its wall.
    deck=Polygon(backwards+[(x0,.85),(float(path[-1][0])-.22,max(.85,float(path[-1][1])))])
    if deck.is_valid and deck.area>.01:
        b.prism(deck,-.13,-.005,lambda x,y,z:(x,y,z),TERRACE,'NE forecourt | terrace at sill')
    for i,z in enumerate(gate['rails_z']):
        line=[(*plan(a,-.095),z) for a in angles]
        b.tube(line,.024 if i==3 else .015,RAILING,6 if lod else 10,'NE forecourt | tubular rail '+str(i+1))
    for i,a in enumerate((3,16,31.4,48,64.8,80,gate['end_angle_deg'])):
        x,y=plan(a,-.095)
        b.tube([(x,y,height(a)),(x,y,1.014)],.023,RAILING,6 if lod else 10,'NE forecourt | upright '+str(i+1))
    # Three staggered rows of short uprights are clear in the high-resolution crop.
    for level,(z0,z1) in enumerate(zip(gate['rails_z'],gate['rails_z'][1:])):
        for i,a in enumerate(np.arange(5+(level%2)*4.6,gate['end_angle_deg']-2,9.3)):
            x,y=plan(a,-.094)
            b.tube([(x,y,z0),(x,y,z1)],.010,RAILING,5 if lod else 8,'NE forecourt | staggered rail tie')


def add_northeast_ground(b,lod=False,layout=None):
    s=json.loads(SURVEY.read_bytes())
    c=s['solarium'];center=c['centre_xy'];r=c['radius_m'];h=c['head_z']
    common=json.loads((HERE.parent/'measurements/garden-cameras.json').read_bytes())
    top=common['middle_slab_underside_z']; low=c['sill_z'];last=-90
    for i,(a,z) in enumerate(c['opening_endpoint_angles_deg'],1):
        shell(b,center,r,.175,last,a,-.01,top,PLASTER,'NE garden room | rendered pier '+str(i),lod)
        shell(b,center,r,.175,a,z,h,top,PLASTER,'NE garden room | rendered lintel '+str(i),lod)
        shell(b,center,r,.175,a,z,-.01,low,COPING,'NE garden room | low threshold '+str(i),lod)
        window(b,center,r,a,z,low,h,c['meeting_stile_fraction'][i-1],c['panel_fraction'][i-1],'bay '+str(i))
        last=z
    shell(b,center,r,.175,last,90,-.01,top,PLASTER,'NE garden room | eastern return pier',lod)
    forecourt(b,s,lod)
    return {'openings': len(c['opening_endpoint_angles_deg']), 'slab_underside':top}
