"""Measure the pierced screen, separate round panes, street arcade and raised entrance in each decoded GLB."""
import argparse
import json
import math
from pathlib import Path
import runpy

import numpy as np
from shapely.geometry import Polygon

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/hongkou-1933-slaughterhouse-west-concrete-screen/source'
lib=runpy.run_path(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py')
CAST='West front cast concrete'
DRESS='Warm limestone-grey coping'
P=json.loads((SOURCE/'dimensions.json').read_bytes())
theta=-math.radians(P['front_axis_bearing_deg'])
ROT=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])


def cases():
    probes=[]
    def check(name,u,z,x,sign,limit,mat=None,interval=None):
        xy=ROT@[x,-u];d=ROT@[sign,0]
        probes.append(dict(name=name,origin=[*xy,z],direction=[*d,0.],length=limit,allowed=mat,range_m=interval))
    def street(name,u,z,mat=None,interval=None):
        check(name,u,z,-1.,1.,1.65,mat,interval)
    extent=P['facade_width'];centre=P['centre_bay'];span=(extent-centre)/8
    edges=[-extent/2+j*span for j in range(5)]+[centre/2+j*span for j in range(5)]
    for j,(a,b) in enumerate(zip(edges,edges[1:])):
        central=j==4;mid=(a+b)/2
        pitch=P['central_pitch'] if central else P['screen_pitch']
        sill=P['central_sill'] if central else P['ordinary_sill']
        sep=P['centre_ring_separation'] if central else P['pair_axis']
        for leaf in (-1,1):
            axis=mid+leaf*sep/2
            for row in range(13 if central else 12):
                z=sill+(row+.5)*pitch
                name=f'Bay {j+1}, leaf {leaf:+}, ring {row+1}'
                glass='Lower circular glazing' if row<4 else 'Grey-green glazing' if row<8 else 'Upper blue-grey glazing'
                street(name+' recessed pane',axis+.012,z+.009,glass,[1.374,1.380])
                street(name+' front annulus',axis+.401*pitch,z+.013*pitch,CAST,[1.142,1.148])
                check(name+' back annulus',axis+.401*pitch,z+.013*pitch,.74,-1.,1.,CAST,[.380,.386])
                check(name+' open concrete corner',axis+.372*pitch,z+.391*pitch,-1.,1.,1.49)
                if not central and row%4==3:
                    street(name+' floor slab beyond ventilation hole',axis+.372*pitch,z+.391*pitch,'Worn concrete paving',[1.567,1.573])
                if not central:
                    s=-1 if (row+j)%2 else 1
                    street(name+' open side vent',axis+s*.676*pitch,z+.25*pitch)
                    street(name+' side crossbar',axis+s*.676*pitch,z,CAST,[1.142,1.148])
        if central:continue
        for x in (-1.32,1.32):
            check(f'Arcade {j+1} glazed shop background {x}',mid+x,1.81,-1.,1.,4.40,'Shadowed shop glazing',[4.11,4.13])
        street(f'Arcade {j+1} medallion',mid,P['ordinary_sill']-.99,'Subdued facade medallions',[.943,.952])
        street(f'Roof {j+1} fan',mid+.10,sill+12*pitch+.60,CAST,[.788,.799])
    for u in (-3.31,-1.67,0.,1.67,3.31):
        street(f'Raised entrance pier {u}',u,11.24,CAST,[.582,.598])
    for u in (-.99,0.,.99):
        check('Entrance open passage '+str(u),u,1.72,-1.,1.,4.12)
    for idx,group in enumerate(json.loads((SOURCE/'entrance-letters.json').read_bytes())[:3]):
        largest=max((Polygon(exterior,holes)for exterior,*holes in group['polygons']),key=lambda part:part.area)
        pos=largest.representative_point()
        street('Three-dimensional lettering '+str(idx+1),pos.x,P['arcade_impost']+.24+.15+pos.y,'Pale cast letters',[.577,.584])
    return probes


def inspect(path,probes):
    tri,mi,names,asset=lib['load_triangles'](path)
    look=lib['material_appearance'](path)['materials']
    glass={name:spec['baseColorFactor'][3]for name,spec in look.items()if spec['alphaMode']=='BLEND' and spec['doubleSided']}
    assert set(glass)=={'Lower circular glazing','Grey-green glazing','Upper blue-grey glazing'} and all(.15<a<.30 for a in glass.values())
    lows,highs=tri.min(axis=1),tri.max(axis=1)
    subsets={};checks=[]
    for p in probes:
        o=np.array(p['origin']);d=np.array(p['direction']);end=o+p['length']*d
        lo=np.minimum(o,end)-1.e-6;hi=np.maximum(o,end)+1.e-6
        key=(math.floor(lo[1]/2),math.floor(hi[1]/2),math.floor(lo[2]/2))
        if key not in subsets:
            a,b,c=key
            subsets[key]=np.flatnonzero((highs[:,1]>=2*a)&(lows[:,1]<2*b+2)&(highs[:,2]>=2*c)&(lows[:,2]<2*c+2))
        ids=subsets[key]
        ids=ids[np.all(highs[ids]>=lo,axis=1)&np.all(lows[ids]<=hi,axis=1)]
        hit=None
        if len(ids):
            j,dist,pos=lib['first_hit'](tri[ids],o,d)
            if np.isfinite(dist) and dist<=p['length']:
                k=ids[j];hit=dict(material=names[mi[k]],distance_m=float(dist),point_enu_m=pos.tolist(),triangle_index=int(k))
        ok=hit is None if p['allowed'] is None else hit and hit['material']==p['allowed']
        if ok and hit and p['range_m']:ok=p['range_m'][0]<=hit['distance_m']<=p['range_m'][1]
        checks.append({**p,'first_hit':hit,'passed':bool(ok)})
    return dict(asset=asset,triangles=len(tri),glazing_alpha=glass,passed=all(c['passed']for c in checks),cases=checks)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for role in ('raw','full','lod','output'):parser.add_argument(role,type=Path)
    args=parser.parse_args()
    result={role:inspect(getattr(args,role),cases())for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    for name,s in result.items():print(name,len(s['cases']),[(t['name'],t['first_hit']) for t in s['cases'] if not t['passed']][:15])
    raise SystemExit(int(not all(s['passed']for s in result.values())))
