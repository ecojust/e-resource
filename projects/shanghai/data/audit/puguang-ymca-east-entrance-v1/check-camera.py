"""Check the public camera against the delivered street facade, retained upper storeys and adjoining blocks."""
import argparse,gzip,json,math,runpy
from pathlib import Path
import numpy as np
import shapely as geo
from shapely.affinity import scale,translate
from shapely.geometry import Point,shape,LineString
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
shared=runpy.run_path(str(HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py'))
read=lambda p:json.loads(p.read_bytes())
sha=shared['digest']

def equipped_sightline(mesh,eye,point):
    origin=np.asarray(eye);endpoint=np.asarray(point);d=endpoint-origin;total=np.linalg.norm(d);d/=total
    a=mesh[:,1]-mesh[:,0];b=mesh[:,2]-mesh[:,0]
    h=np.cross(d,b);det=np.einsum('ij,ij->i',a,h);inv=np.divide(1,det,out=np.zeros_like(det),where=abs(det)>1e-9)
    s=origin-mesh[:,0];u=np.einsum('ij,ij->i',s,h)*inv
    q=np.cross(s,a);v=(q@d)*inv;t=np.einsum('ij,ij->i',b,q)*inv
    hit=t[(abs(det)>1e-9)&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1.00000001)&(t>1e-5)]
    gap=float(max(0,total-hit.min()))if len(hit)else None
    return gap

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract',type=Path,default=HERE/'final-placement-contract.json')
    parser.add_argument('--surfaces',type=Path,default=HERE/'visible-surfaces.json')
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE/'camera-sightlines.json')
    args=parser.parse_args()
    place=read(args.contract);review=read(PROJECT/'source/precise'/place['id']/'footprint-review.json')
    lon,lat=place['lng'],place['lat'];mn=math.radians(1)*shared['EARTH'];me=mn*math.cos(math.radians(lat))
    origin=Point(lon,lat);volumes=[];tables={}
    data=(args.work/'feature-table.json.gz').read_bytes();digest=sha(data)
    assert digest==next(r['sha256']for r in review['frozen_bindings']if r['repository_path'].endswith('/feature-table.json.gz'))
    tables[review['frozen_macro']]=digest
    heading=math.radians(place['heading']);cs,sn=math.cos(heading),math.sin(heading)
    def en(p):return scale(translate(p,-lon,-lat),xfact=me,yfact=mn,origin=(0,0))
    def local(xy):
        e,n=xy.T
        return np.column_stack([e*cs-n*sn,e*sn+n*cs])
    cuts=[geo.transform(en(shape(r['geometry'])),local)for r in place['display_height_clips']]
    for f in json.loads(gzip.decompress(data))['features']:
        polygon=shape(f['geometry'])
        if polygon.distance(origin)>.00165:continue
        polygon=en(polygon)
        if polygon.distance(Point(0,0))>140:continue
        if f['localId']==2382:
            native=geo.transform(polygon,local)
            own=[(native.difference(cuts[0]),-1.2,f['height']),
                 (native.intersection(cuts[0]).difference(cuts[1]),7.095,f['height']),
                 (native.intersection(cuts[1]),15.04,f['height'])]
        else:volumes.append((review['frozen_macro']+'/'+str(f['localId']),polygon,f['height']))
    surfaces=read(args.surfaces)['checks']['raw']
    tri=next(row for row in read(args.work/'delivered-decode.json')if row['variant']=='raw')
    assert tri['sha256']==surfaces['sha256']==place['model_geometry_sha256']['raw']
    mesh=np.fromfile(tri['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
    probes=surfaces['rays']
    targets={}
    for label,term,index in [('南铺横窗','south shop inset horizontal pane',0),('北铺卷帘','north shop corrugated closure',0),
                              ('南铺券顶','south shop keystone',0),('北铺券顶','north shop keystone',0),
                              ('南侧窗格','south recessed upper glass',0),('北侧上窗','north recessed upper glass',1),
                              ('檐下中央窗','entrance axis recessed upper glass',1),('南赭砖柱','column at split pediment',0),
                              ('北砖壁柱','rebated masonry course',1),('南断山花','raking stone under the broken apex',0),
                              ('北断山花','raking stone under the broken apex',1),('铭额','lintel G',0),('南铭额边','portal lettering surround',0),('钟面','clock ivory face',0),
                              ('中央门低窗','central extended sash behind top of English lintel',0)]:
        r=[i for i in probes if i['target']==term][index]
        targets[label]=[r['x'],-r['front_d_m'],r['z']]
    clock=next(r for r in probes if r['target']=='clock hub')
    targets['门上圆钟']=[clock['x'],-clock['front_d_m'],clock['z']]
    heading=math.radians(place['heading']);c,s=math.cos(heading),math.sin(heading)
    en=[(name,x*c+y*s,-x*s+y*c,z)for name,(x,y,z)in targets.items()]
    cases={}
    for label,bearing,pitch in [('delivered',place['overviewBearing'],place['overviewPitch']),
            ('high_street',place['heading'],27),('square_on',place['heading'],42),
            ('north_approach',place['heading']+17,34),('south_approach',place['heading']-17,34),
            ('street_low',place['heading'],64),('intermediate',place['heading'],48),('across_street',place['heading'],56)]:
        cameras=[]
        for screen,width,height,padding in shared['VIEWS']:
            viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],padding)))
            row=shared['evaluate']({**place,'overviewBearing':bearing,'overviewPitch':pitch},viewport,screen,volumes,lon,lat,me,mn,en)
            e,n,z=row['camera_enu'];eye=[e*c-n*s,e*s+n*c,z]
            for p in row['probes']:
                delta=equipped_sightline(mesh,eye,targets[p['feature']])
                target=np.asarray(targets[p['feature']]);line=LineString([target[:2],eye[:2]])
                retained=[]
                for part,lo,hi in own:
                    for section in geo.get_parts(line.intersection(part)):
                        if section.is_empty:continue
                        distances=[line.project(Point(coord))/line.length for coord in section.coords]
                        z=[target[2]+frac*(eye[2]-target[2])for frac in distances]
                        if max(z)>=lo and min(z)<=hi:retained.append([float(min(z)),float(max(z)),lo,hi])
                p['retained_owner_in_front']=retained
                p['nearest_mesh_in_front_m']=delta
                # The known point is on a real surface. 25 mm allows for ray hits on bevel edges.
                p['visible_on_gate']=delta is not None and delta<.025
                p['visible']=p['clear'] and p['visible_on_gate'] and not retained
            row['visible_count']=sum(p['visible']for p in row['probes']);cameras.append(row)
        cases[label]=cameras
    out={'id':place['id'],'contract_sha256':sha(args.contract.read_bytes()),'source_tables':tables,'retained_buildings':len(volumes),
         'mesh_sha256':tri['sha256'],'camera_module_sha256':sha((PROJECT/'src/candidate-overview-camera.js').read_bytes()),'cases':cases}
    args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print({k:[(r['clear_count'],r['visible_count'])for r in rows]for k,rows in cases.items()})
    assert all(r['visible_count']==len(targets) for r in cases['delivered']),[(p['feature'],p['obstructions'],p['nearest_mesh_in_front_m'],p['retained_owner_in_front']) for p in cases['delivered'][0]['probes'] if not p['visible']]

if __name__=='__main__':main()
