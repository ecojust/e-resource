"""Verify the dated stone field, the clipped return, and all nine symbols on an unfiltered glTF mesh."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon,Point
from shapely.ops import polylabel

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
import dated_cartouche as plaque
from glb_triangles import SerialScene


def probes():
    j=json.loads(plaque.MEASUREMENTS.read_bytes());front=Polygon(j['face']);outer=Polygon(j['backing'])
    samples=[]
    def add(x,z,material,label):
        samples.append(dict(position=[round(x,7),round(z,7)],expected=material,feature=label))
    for row in j['glyphs']:
        p=Polygon(row['outline'],row['counters']);name=f"{row['position']} {row['character']}"
        add(*polylabel(p,.0002).coords[0],plaque.INK,name+' central stroke')
        x0,z0,x1,z1=p.bounds
        stable=[]
        for z in np.linspace(z0,z1,15):
            for x in np.linspace(x0,x1,16):
                q=Point(x,z)
                if p.contains(q) and q.distance(p.boundary)>.0026: stable.append((q.distance(p.boundary),x,z))
        chosen=[]
        for _,x,z in sorted(stable,reverse=True):
            if any(np.hypot((x-c)*5,z-d)<.11 for c,d in chosen):continue
            chosen.append((x,z));add(x,z,plaque.INK,name+' stroke')
            if len(chosen)==4:break
        for hole in row['counters']:
            q=polylabel(Polygon(hole),.0001)
            add(*q.coords[0],plaque.FIELD,name+' open counter')
    # Sample both shoulders of all four corner cuts and the four long edges.
    rim=outer.difference(front)
    for angle in np.linspace(0,2*np.pi,32,endpoint=False):
        ux,uz=np.cos(angle),np.sin(angle)
        inside=[]
        for r in np.linspace(.35,.72,210):
            pt=Point(r*ux,r*uz)
            if rim.contains(pt):inside.append((pt.distance(rim.boundary),pt))
        if inside:
            q=max(inside,key=lambda item:item[0])
            if q[0]>.0016:add(*q[1].coords[0],plaque.CARRIER,'dark perimeter')
    for x in np.linspace(-.408,.408,7):
        for v in [-.325,.33]:
            if front.contains(Point(x,v)):add(x,v,plaque.FIELD,'clear stone field')
    return samples


def check(asset,layout):
    width,_,point=plaque.reference_frame(layout)
    scene=SerialScene(asset);rows=[]
    for sample in probes():
        u,z=sample['position'];origin=point(u,z,.12)
        hit=scene.ray(origin,[0.,1.,0.],.23*width)
        material=hit['material'] if hit else None
        rows.append(dict(**sample,first_material=material,first_m=hit['point_enu_m']if hit else None,passed=material==sample['expected']))
    return dict(passed=all(r['passed']for r in rows),checks=len(rows),rows=rows,
                asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
                independently_checked_source='The second published exposure was sampled at the nine symbol locations; contrast is recorded in dated-cartouche-tracings.json.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('model',type=Path);parser.add_argument('report',type=Path);parser.add_argument('--layout',type=Path)
    args=parser.parse_args();report=check(args.model,json.loads(args.layout.read_bytes())if args.layout else None)
    args.report.write_text(json.dumps(report,indent=1,ensure_ascii=False)+'\n');bad=[a for a in report['rows']if not a['passed']]
    print(report['checks'],len(bad),bad[:1]);raise SystemExit(not report['passed'])
