"""Measure which faces the public overview can see with the retained city buildings present."""
from pathlib import Path
import argparse,gzip,json,math,runpy
import numpy as np
from shapely.geometry import shape,Point
from shapely.affinity import translate,scale
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2]
SRC=PROJECT/'source/precise/huangpu-central-trust-beijing-front/source'
shared=runpy.run_path(HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py')
review=runpy.run_path(HERE/'verify-export.py')
read=lambda p:json.loads(p.read_bytes())
sha=review['sha']

def targets(mesh):
    tri,ids,names,info=review['load'](mesh)
    attrs=(tri,tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],tri.min(axis=1),tri.max(axis=1))
    center=read(SRC/'plan-registration.json')['south_width_m']/2
    features=[]
    for label,x,z in [
        ('west outer window',-8.55+.16,8.3),('west wide sash',-6.70+.16,16.80),
        ('west ground bank window',-6.70+.18,2.71),('east ground side door',6.70+.18,2.71),
        ('east outer window',8.55+.18,12.50),('east carved spandrel',6.70+.11,15.052),
        ('west main column',-1.55,2.6),('east main column',1.55,2.6),('entrance fascia',.53,5.48),
        ('glazed main door',.463,1.47),('original fifth-floor cornice',.77,24.28),
        ('upper added windows',.16,28.20)]:
        features.append((label,[center+x,-4,z],[0,1,0]))
    probes=[]
    for name,start,d in features:
        o=np.array(start);d=np.array(d);hit=review['first'](*attrs,o,d)
        assert hit,(name,o)
        i,distance=hit;point=o+d*distance
        probes.append((name,point,names[ids[i]]))
    return info,attrs,probes

def candidate(path,raw,table,out,search):
    place=read(path);reg=read(SRC/'plan-registration.json');info,attrs,probes=targets(raw)
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
        if f['localId']==1082:self_outline=poly
        else:neighbors.append((f['localId'],poly,f['height']))
    assert self_outline and mask and len(neighbors)>20
    cuts=[meters(shape(x['geometry']))for x in place['display_height_clips']]
    upper_retained=self_outline.difference(mask)
    for cut in cuts:upper_retained=upper_retained.difference(cut)
    # The original courtyard volume below 8.8 m and the retained rear remain opaque.
    neighbors.append(('1082 retained',upper_retained,16.0))
    for i,cut in enumerate(cuts):neighbors.append(('1082 lightwell lower block '+str(i+1),self_outline.intersection(cut).difference(mask),8.8))
    pairs=[(place['overviewBearing'],place['overviewPitch'])]
    if search:pairs += [(b,p)for b in [-26,-13,0,13,26]for p in [30,40,50,56,62]]
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
            row['visible']=sum(probe['visible']for probe in row['probes']);cases.append(row)
        results.append(dict(bearing=bearing,pitch=pitch,views=cases))
    results.sort(key=lambda result:(min(r['visible']for r in result['views']),sum(r['visible']for r in result['views'])),reverse=True)
    out.write_text(json.dumps(dict(raw=info,source_sha256=sha(table),camera_module_sha256=sha(PROJECT/'src/candidate-overview-camera.js'),retained_volumes=len(neighbors),results=results),ensure_ascii=False,indent=2)+'\n')
    print([(r['bearing'],r['pitch'],[v['visible']for v in r['views']])for r in results[:7]])
if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('place',type=Path);args.add_argument('raw',type=Path);args.add_argument('source_table',type=Path);args.add_argument('out',type=Path);args.add_argument('--search',action='store_true');a=args.parse_args();candidate(a.place,a.raw,a.source_table,a.out,a.search)
