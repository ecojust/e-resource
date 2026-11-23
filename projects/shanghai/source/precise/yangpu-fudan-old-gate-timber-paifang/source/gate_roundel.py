"""Construct the two halves of the gate medallion and the readable relief traces on its back."""
import json
from pathlib import Path
from shapely.geometry import Point,box,LineString
HERE=Path(__file__).resolve().parents[1]/'measurements'
BRONZE='Fudan | warm bronze relief'
DARK='Fudan | dark eave timber'
def add_roundel(b,lod):
    data=json.loads((HERE/'reverse-door-roundel.json').read_bytes())['central_disc']
    radius=.305;height=1.192
    # The disc is separately fastened to the two leaves, with a visible meeting line.
    circle=Point(0,height).buffer(radius,quad_segs=12 if lod else 22)
    for side in (-1,1):
        clip=box(-radius-.01,height-radius-.01,-.003,height+radius+.01) if side<0 else box(.003,height-radius-.01,radius+.01,height+radius+.01)
        poly=circle.intersection(clip)
        for name,y,orient in [('front',-.054,-1),('reverse',.151,1)]:
            def map_point(u,z,d):return -orient*u,y+orient*d,z
            b.prism(poly,0,.027,map_point,DARK,name+' / independent medallion half')
            ring=circle.difference(circle.buffer(-.076)).intersection(clip)
            b.prism(ring,.027,.037,map_point,BRONZE,name+' / cast medallion rim')
    def xyz(u,v):return ((u-413.5)*radius/24.5,height-(v-439)*radius/24.)
    def expose(u,z,d):return -u,.151+d,z
    for k in ('left_visible_runs_uv','right_visible_runs_uv'):
        for j,line in enumerate(data[k]):
            path=LineString([xyz(*p) for p in line]).buffer(.008,quad_segs=2,cap_style=1)
            b.prism(path,.027,.038,expose,BRONZE,'reverse / measured medallion relief '+k[:4]+str(j))
