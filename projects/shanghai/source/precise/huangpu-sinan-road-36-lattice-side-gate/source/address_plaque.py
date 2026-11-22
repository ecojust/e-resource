"""Project measured enamel corners and their seven photographed paint groups."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Point,Polygon,box
from shapely.ops import transform
from photo_architecture import Facade
from photo_plane import original_to_crop,position,homography

GREEN='Deep green enamel'
WHITE='Light address paint'
FINE='Weathered paint highlights'
EDGE='Rolled enamel rim'
PLATE_Y=-.207
DATA=Path(__file__).resolve().parents[1]/'measurements/plaque-strokes.json'
def registration():
    d=json.loads(DATA.read_bytes())
    coords=[position(*original_to_crop(*px),PLATE_Y)[[0,2]]for px in d['enamel_corners_upright']]
    return d,homography([(*uv,*q)for uv,q in zip([(0,0),(1,0),(1,1),(0,1)],coords)])
def project_poly(poly,H):
    def project(u,v):
        u=np.atleast_1d(u);v=np.atleast_1d(v)
        vec=H@np.stack([u,v,np.ones_like(u)])
        return vec[0]/vec[2],vec[1]/vec[2]
    return transform(project,poly)
def add_plaque(b,lod):
    data,H=registration();f=Facade(b,(-4,0),(4,0),'Address')
    cut=box(.045,.045,.955,.955).buffer(.045,quad_segs=5 if lod else 10)
    outline=project_poly(cut,H);f.prism(outline,.181,-PLATE_Y,EDGE,'green enamel folded edge')
    face=project_poly(cut.buffer(-.008),H)
    f.prism(face,-PLATE_Y,-PLATE_Y+.0015,GREEN,'green vitreous enamel')
    names={'3':'three','6':'six','思':'si','南':'nan','路':'lu','边':'bian','门':'men'}
    for name,groups in data['groups'].items():
        for i,g in enumerate(groups):
            poly=Polygon(g['shell'],g['holes']).buffer(0)
            if lod:poly=poly.simplify(.0015,preserve_topology=True)
            f.prism(project_poly(poly,H),-PLATE_Y+.0015,-PLATE_Y+.0022,WHITE,names[name]+' photo stroke '+str(i+1))
    # A second narrow colour separates illuminated strokes inside five small
    # glyphs. It does not change the outline or turn the lettering into holes.
    for name,thresholds in data['fine_pigment_contours'].items():
        for i,g in enumerate(thresholds['0.82']):
            poly=Polygon(g['shell'],g['holes']).buffer(0)
            if lod:poly=poly.simplify(.0023,preserve_topology=True)
            if poly.area>.00004:
                f.prism(project_poly(poly,H),-PLATE_Y+.0022,-PLATE_Y+.0025,FINE,names[name]+' retained highlight '+str(i+1))
