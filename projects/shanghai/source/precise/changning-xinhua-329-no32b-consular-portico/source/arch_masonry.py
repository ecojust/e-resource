"""Radial masonry reconstructed around the photographed stone doorway."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon


def arch_course(builder,lod,point,plate,wall,stone,mortar,clays):
    book=json.loads(Path(__file__).with_name('arch-course-readings.json').read_bytes())
    cx,cy=book['native_centre']
    inner=np.array(book['inner_radii'])
    outer=np.array(book['outer_radii'])

    def arc(radii,start,end,y,count):
        angles=np.deg2rad(np.linspace(start,end,count))
        return [point((cx+radii[0]*np.cos(a))*537/1280,(cy-radii[1]*np.sin(a))*805/1919,y)[[0,2]] for a in angles]

    def sector(a,b,y,left,right):
        samples=max(3,int((b-a)/7)+1) if lod else max(4,int((b-a)/3)+1)
        return Polygon(arc(right,a,b,y,samples)+list(reversed(arc(left,a,b,y,samples))))

    # These surfaces coincide with separate joint endpoints, including the
    # lighter central key plainly visible in both the portrait and the court view.
    background=sector(0,180,wall-.005,inner-.8,outer+1)
    plate(builder,background,wall-.005,wall+.010,mortar,'arch/continuous mortar bed')
    for i,(a,b) in enumerate(zip(book['angles_deg'],book['angles_deg'][1:])):
        key=a==85 and b==95
        front=wall-(.041 if key else .022)
        # Bed joints are explicit gaps through the outer, independent brick prisms.
        face=sector(a+.16,b-.16,front,inner,outer)
        plate(builder,face,front,wall-.002,stone if key else clays[i%len(clays)],
              'arch/central stone key' if key else f'arch/radial fired brick {i+1:02}')
    y=wall-.075
    rim=arc(inner,0,180,y,25 if lod else 65)
    bottom=point(275,632,wall)[2]
    return Polygon([*rim,(rim[-1][0],bottom),(rim[0][0],bottom)])
