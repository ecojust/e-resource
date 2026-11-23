"""Trace both default cameras to the twelve street fixtures through near and far city triangles."""
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
import runpy,sys
import numpy as np
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2];sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha

def check(contract,sightlines,macro,output):
    c=read(contract);ref=read(PROJECT/'source/precise'/c['id']/'footprint-review.json')
    grouping=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    ray=runpy.run_path(str(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'))['first_hit']
    cam=read(sightlines);assert cam['contract_sha256']==sha(contract);variants={}
    with TemporaryDirectory()as work:
        path=Path(work)
        for b in ref['frozen_bindings']:
            f=macro/Path(b['repository_path']).name;assert sha(f)==b['sha256'];(path/f.name).symlink_to(f.resolve())
        site=PlacementMeshes(PROJECT,path,ref)
        for group in ref['sightline_groups']:
            for key,tri,owners,ties in grouping(site,group):
                tested=[]
                for view in cam['views']:
                    eye=np.array(view['camera_enu']);eye[:2]=eye[:2]@site.axes.T
                    rows=[]
                    for probe in view['probes']:
                        target=np.array(probe['target_enu']);target[:2]=target[:2]@site.axes.T
                        direction=target-eye;span=np.linalg.norm(direction)
                        i,t,hit=ray(tri,eye,direction/span);detail=None if not np.isfinite(t)else{'owner':int(owners[i]),'distance_m':round(float(t),4)}
                        clear=not np.isfinite(t) or t>span+.006
                        rows.append({'feature':probe['feature'],'clear':bool(clear),'target_distance_m':round(float(span),4),'first_city_intersection':detail})
                    tested.append({'view':view['view'],'rows':rows})
                variants[group['id']+'/'+key]={'triangles':len(tri),'tests':tested}
    result={'contract_sha256':sha(contract),'camera_sha256':sha(sightlines),'groups':variants,'inspected_owners':ref['sightline_candidate_owners']}
    result['passed']=all(r['clear'] for g in variants.values() for view in g['tests']for r in view['rows'])
    write(output,result)
    if not result['passed']:
        print([(k,v['view'],t['feature'],t['first_city_intersection'])for k,g in variants.items()for v in g['tests']for t in v['rows']if not t['clear']])
        raise ValueError('A currently retained source masks a named facade feature')
if __name__=='__main__':
    a=ArgumentParser(description=__doc__)
    for name in ('contract','sightlines','macro','out'):a.add_argument('--'+name,type=Path,required=True)
    args=a.parse_args();check(args.contract,args.sightlines,args.macro,args.out)
