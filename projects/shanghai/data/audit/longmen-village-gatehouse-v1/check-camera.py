"""Project real gate details into the two public viewports with both original city macros retained."""
import argparse,gzip,json,math,runpy
from pathlib import Path
import numpy as np
from shapely.affinity import scale,translate
from shapely.geometry import Point,shape
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
    for folder,doc in [(args.work,review),(args.work/review['adjacent_macro']['frozen_macro'],review['adjacent_macro'])]:
        inp=folder/'feature-table.json.gz';data=inp.read_bytes();digest=sha(data)
        assert digest==next(r['sha256']for r in doc['frozen_bindings'] if r['repository_path'].endswith('/feature-table.json.gz'))
        tables[doc['frozen_macro']]=digest
        for f in json.loads(gzip.decompress(data))['features']:
            polygon=shape(f['geometry'])
            if polygon.distance(origin)>.00165:continue
            polygon=scale(translate(polygon,-lon,-lat),xfact=me,yfact=mn,origin=(0,0))
            if polygon.distance(Point(0,0))<140:
                volumes.append((doc['frozen_macro']+'/'+str(f['localId']),polygon,f['height']))
    surfaces=read(args.surfaces)['role_checks']['raw']
    tri=next(row for row in read(args.work/'delivered-decode.json')if row['variant']=='raw')
    assert tri['sha256']==surfaces['sha256']==place['model_geometry_sha256']['raw']
    mesh=np.fromfile(tri['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
    probes=surfaces['rays']
    def sample(name,n=0):
        row=[r for r in probes if r['detail']==name][n]
        assert row['passed'] and row['distance_m'] is not None
        return (np.array(row['origin_m'])+np.array(row['direction'])*row['distance_m']).tolist()
    targets={name:sample(feature,n) for name,feature,n in [
        ('西门柱','dressed street piers',0),('东门柱','dressed street piers',3),('拱券','light cut arch ring',3),
        ('阴刻东字','incised oxblood character 龍',0),('阴刻西字','incised oxblood character 邨',0),
        ('西侧红砖','running bond inside stone recess',3),('东侧红砖','running bond inside stone recess',10),
        ('西红窗扇','repainted open wood leaf',0),('东红窗扇','repainted open wood leaf',1),
        ('上部百叶','sloped louvre 12',0),('纪年','raised date 9',0),
        ('高檐脊','high moulded ridge',0),('西檐脊','west moulded ridge',0),('东檐脊','east moulded ridge',0)]}
    heading=math.radians(place['heading']);c,s=math.cos(heading),math.sin(heading)
    en=[(name,x*c+y*s,-x*s+y*c,z)for name,(x,y,z)in targets.items()]
    cases={}
    for label,bearing,pitch in [('delivered',place['overviewBearing'],place['overviewPitch']),
            ('front_high',place['heading'],34),('front_mid',place['heading'],46),
            ('street_oblique_west',place['heading']+14,48),('street_oblique_east',place['heading']-14,48),
            ('street_low',place['heading'],64)]:
        cameras=[]
        for screen,width,height,padding in shared['VIEWS']:
            viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],padding)))
            row=shared['evaluate']({**place,'overviewBearing':bearing,'overviewPitch':pitch},viewport,screen,volumes,lon,lat,me,mn,en)
            e,n,z=row['camera_enu'];eye=[e*c-n*s,e*s+n*c,z]
            for p in row['probes']:
                delta=equipped_sightline(mesh,eye,targets[p['feature']])
                p['nearest_mesh_in_front_m']=delta
                # The known point is on a real surface. 25 mm allows for ray hits on bevel edges.
                p['visible_on_gate']=delta is not None and delta<.025
                p['visible']=p['clear'] and p['visible_on_gate']
            row['visible_count']=sum(p['visible']for p in row['probes']);cameras.append(row)
        cases[label]=cameras
    out={'id':place['id'],'contract_sha256':sha(args.contract.read_bytes()),'source_tables':tables,'retained_buildings':len(volumes),
         'mesh_sha256':tri['sha256'],'camera_module_sha256':sha((PROJECT/'src/candidate-overview-camera.js').read_bytes()),'cases':cases}
    args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print({k:[(r['clear_count'],r['visible_count'])for r in rows]for k,rows in cases.items()})
    assert all(r['visible_count']==len(targets) for r in cases['delivered'])

if __name__=='__main__':main()
