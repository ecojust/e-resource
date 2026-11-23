"""Measure which faces the public overview can see with the retained city buildings present."""
from pathlib import Path
import argparse,gzip,json,math,runpy
import numpy as np
from shapely.geometry import shape,Point
from shapely.affinity import translate,scale
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2]
SRC=PROJECT/'source/precise/huangpu-american-oriental-bank-rounded-corner/source'
shared=runpy.run_path(HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py')
review=runpy.run_path(HERE.parent/'somekh-building-street-corner-v1/verify-export.py')
read=lambda p:json.loads(p.read_bytes())
sha=review['sha']

def targets(mesh):
    tri,ids,names,info=review['load'](mesh)
    attrs=(tri,tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],tri.min(axis=1),tri.max(axis=1))
    reg=read(SRC/'frontage-registration.json')
    cen=np.array(reg['arc_center_m']);r=reg['arc_radius_m'];length=r*math.radians(reg['corner_sweep_deg'])
    features=[]
    for label,s,z in [('Ningbo glass',-2.81,8.87),('Ningbo shop name',.18,2.44),
                     ('west shoulder window',.17,6.10),('west brick strip',1.51,6.79),
                     ('west rounded sash',3.08,8.77),('paired condensers',6.08,4.28),
                     ('corner door',6.92,1.46),('weathered board',6.82,2.87),
                     ('wide steel window',6.85,9.23),('east window',10.23,8.83),
                     ('east shoulder',12.02,12.23),('lifted parapet',6.91,15.07),
                     ('Henan straight sash',15.01,6.05)]:
        for ds in (-.16,0,.16):
            for dz in (-.11,0,.11):
                if label=='lifted parapet':dz*=.4
                if label=='weathered board':dz*=.6
                if label=='Ningbo shop name':dz*=.7
                station=s+ds
                a=-math.pi/2+min(length,max(0,station))/r;n=np.array([math.cos(a),math.sin(a)])
                xy=cen+(r+3)*n
                if station<0:xy+=np.array([station,0])
                if station>length:xy+=np.array(reg['east_street_direction'])*(station-length)
                features.append((label,[*xy,z+dz],[*-n,0]))
    probes=[]
    for name,start,d in features:
        o=np.array(start);d=np.array(d);hit=review['first'](*attrs,o,d)
        assert hit,(name,o)
        i,distance=hit;point=o+d*distance
        probes.append((name,point,names[ids[i]]))
    return info,attrs,probes

def candidate(path,raw,table,out,search):
    place=read(path);reg=read(SRC/'frontage-registration.json');info,attrs,probes=targets(raw)
    lat=place['lat'];lng=place['lng'];mn=math.pi/180*shared['EARTH'];me=mn*math.cos(math.radians(lat))
    h=math.radians(reg['runtime_heading_deg']);c,s=math.cos(h),math.sin(h)
    local_to_enu=lambda x,y:(c*x+s*y,-s*x+c*y)
    en_to_local=lambda e,n:(c*e-s*n,s*e+c*n)
    features=[(name,*map(float,local_to_enu(*p[:2])),float(p[2]))for name,p,_ in probes]
    meters=lambda polygon:scale(translate(polygon,-lng,-lat),xfact=me,yfact=mn,origin=(0,0))
    mask=meters(shape(place['replacement_geometry']));neighbors=[];self_outline=None
    for f in json.loads(gzip.decompress(table.read_bytes()))['features']:
        if not f.get('geometry'):continue
        poly=shape(f['geometry'])
        if poly.distance(Point(lng,lat))>.0020:continue
        poly=meters(poly)
        if poly.distance(Point(0,0))>150:continue
        if f['localId']==2839:self_outline=poly
        else:neighbors.append((f['localId'],poly,f['height']))
    assert self_outline and mask and len(neighbors)>20
    neighbors.append(('2839 retained volume',self_outline.difference(mask),12.8))
    pairs=[(place['overviewBearing'],place['overviewPitch'])]
    if search:pairs += [(b,p)for b in [-25,-35,-45,-55]for p in [52,60,68]]
    else:pairs += [(-7,42),(-53,56),(-78,40)]
    results=[]
    for bearing,pitch in dict.fromkeys(pairs):
        cases=[]
        for screen,width,height,padding in shared['VIEWS']:
            viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],padding)))
            row=shared['evaluate']({**place,'overviewBearing':bearing,'overviewPitch':pitch},viewport,screen,neighbors,lng,lat,me,mn,features)
            eye=np.r_[en_to_local(*row['camera_enu'][:2]),row['camera_enu'][2]]
            for rp,(_,p,material) in zip(row['probes'],probes):
                direction=p-eye;dist=np.linalg.norm(direction);hit=review['first'](*attrs,eye,direction/dist)
                gap=dist-hit[1]if hit else None
                rp.update(mesh_target_material=material,mesh_obstruction_m=None if gap is None else round(float(gap),4),
                          visible=bool(rp['clear'] and gap is not None and abs(gap)<.03))
            groups={}
            for probe in row['probes']:
                groups.setdefault(probe['feature'],[]).append(probe['visible'])
            row['visible_samples']={k:sum(v)for k,v in groups.items()}
            assert all(len(v)==9 for v in groups.values())
            row['visible']=sum(count>=3 for count in row['visible_samples'].values())
            cases.append(row)
        results.append(dict(bearing=bearing,pitch=pitch,views=cases))
    results.sort(key=lambda result:(min(r['visible']for r in result['views']),sum(r['visible']for r in result['views'])),reverse=True)
    out.write_text(json.dumps(dict(raw=info,source_sha256=sha(table),camera_module_sha256=sha(PROJECT/'src/candidate-overview-camera.js'),retained_volumes=len(neighbors),results=results),ensure_ascii=False,indent=2)+'\n')
    print([(r['bearing'],r['pitch'],[v['visible']for v in r['views']])for r in results[:7]])
if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('place',type=Path);args.add_argument('raw',type=Path);args.add_argument('source_table',type=Path);args.add_argument('out',type=Path);args.add_argument('--search',action='store_true');a=args.parse_args();candidate(a.place,a.raw,a.source_table,a.out,a.search)
