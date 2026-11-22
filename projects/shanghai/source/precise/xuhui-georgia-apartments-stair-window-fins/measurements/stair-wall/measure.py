"""Compare four calibrated stair openings with the two signed Hengshan street-wall meshes."""
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import file_digest
from urllib.request import urlopen
import gzip, json, math, os, runpy, shutil, subprocess
import numpy as np

def read(path):
    return json.loads(path.read_bytes())

def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream,'sha256').hexdigest()

def verified_copy(source, expected, destination, revision, repo_path):
    if source.is_file() and digest(source)==expected:
        shutil.copyfile(source,destination)
    else:
        url=f'https://raw.githubusercontent.com/ecojust/e-resource/{revision}/projects/shanghai/{repo_path}'
        with urlopen(url,timeout=35) as remote, destination.open('wb') as out:
            shutil.copyfileobj(remote,out)
    assert digest(destination)==expected,repo_path

def wall_samples(tris, normal, along, sample_positions):
    data=np.fromfile(tris,np.float64).reshape(-1,3,3)
    centers=data.mean(axis=1)
    near=data[(np.abs(centers[:,0])<30)&(np.abs(centers[:,1])<30)]
    e1=near[:,1]-near[:,0]
    e2=near[:,2]-near[:,0]
    direction=-normal
    crossed=np.cross(direction,e2)
    det=(e1*crossed).sum(axis=1)
    valid=np.abs(det)>1e-7
    inv=np.divide(1,det,out=np.zeros_like(det),where=valid)
    results=[]
    for x,z in sample_positions:
        origin=along*x+normal*3+[0,0,z]
        delta=origin-near[:,0]
        cross=np.cross(delta,e1)
        u=(delta*crossed).sum(axis=1)*inv
        v=(cross*direction).sum(axis=1)*inv
        d=(e2*cross).sum(axis=1)*inv
        hits=d[valid&(u>=0)&(v>=0)&(u+v<=1)&(d>=0)&(d<7)]
        results.append(round(float(3-hits.min()),6) if len(hits) else None)
    return results

def main():
    args=ArgumentParser()
    args.add_argument('--project',type=Path,default=Path('.'))
    args.add_argument('--city-dir',type=Path,help='Optional local directory with the signed original meshes')
    args.add_argument('--output',type=Path,required=True)
    cfg=args.parse_args()
    project=cfg.project.resolve()
    here=Path(__file__).resolve().parent
    author=here.parents[1]
    uid=author.name
    signed=read(here/'signed-files.json')
    plan=read(author/'printed-plan-axes.json')
    fitted=read(author/'cross-date-window-elevations.json')
    manifest=signed['model']
    decoder=project/'data/audit/postal-office-v1/map-decode-source.mjs'
    meshdecode=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    serial=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
    angle=math.radians(plan['street_normal_deg']-90)
    along=np.array([math.sin(angle),math.cos(angle),0])
    normal=np.array([along[1],-along[0],0])
    base_z=fitted['model_base_above_grade_m']
    positions=[(x,base_z+z) for z in (0.2,.48,.75,1.06,1.48,1.97,2.28,2.81,3.15,3.43,3.75,4.08,4.45,4.86,5.13,5.38,5.63) for x in (-1.10,-.82,-.69,-.55,-.41,-.18,0,.18,.41,.55,.69,.82,1.10)]
    rows=[]
    with TemporaryDirectory() as temp:
        work=Path(temp)
        for alias,item in signed['city_inputs'].items():
            file=cfg.city_dir/alias if cfg.city_dir else project/item['path']
            verified_copy(file,item['sha256'],work/alias,signed['city_revision'],item['path'])
        (work/'context-features.json').write_text(json.dumps([{'localId':4081}]))
        (work/'initial-local-frame.json').write_text(json.dumps({'anchor':dict(zip(('lng','lat'),plan['center']))}))
        env={**os.environ,'POSTAL_REPO':str(project.parents[1]),'POSTAL_MAPPING_WORK':str(work),
             'NODE_OPTIONS':'--require='+str(project/'data/audit/mitsui-bussan-pediment-front-v1/decode-texture.cjs')}
        subprocess.run(['node',decoder],env=env,stdout=subprocess.DEVNULL,check=True)
        surfaces={v:wall_samples(work/('baseline-'+v+'-triangles.f64'),normal,along,positions) for v in ('near','far')}
        for role,meta in manifest.items():
            if role not in ('raw','full','lod'):continue
            path='assets/models/candidates/'+uid+'/'+meta['file']
            local=work/(role+'.glb')
            verified_copy(project/path,meta['sha256'],local,signed['model_revision'],path)
            if role!='raw':
                decoded=work/(role+'-decoded.glb')
                subprocess.run(['node',meshdecode,local,decoded,project/'vendor/meshopt_decoder.module.js'],stdout=subprocess.DEVNULL,check=True)
                local=decoded
            solid=serial(local)
            for idx,(x,z) in enumerate(positions):
                hit=solid.ray([x,-1,z-base_z],[0,1,0],2)
                front=round(1-hit['distance_m'],6) if hit else None
                rows.append(dict(role=role,x=round(x,6),z=round(z,6),material=hit['material'] if hit else None,model_front_m=front,
                                 near_wall_m=surfaces['near'][idx],far_wall_m=surfaces['far'][idx]))
    comparisons={}
    for role in ('raw','full','lod'):
        comparisons[role]={}
        for level in ('near','far'):
            field=level+'_wall_m'
            glass=[round(row[field]-row['model_front_m'],6) for row in rows if row['role']==role and row['material'] in ('shaded glass','slate grey glass') and row[field] is not None]
            fins=[round(row[field]-row['model_front_m'],6) for row in rows if row['role']==role and row['material']=='pale cast cement' and row[field] is not None]
            assert glass and fins
            comparisons[role][level]=dict(glazed_samples=len(glass),glass_behind_existing_wall=sum(q>0 for q in glass),original_minus_glass_m=[min(glass),max(glass)],cast_cement_samples=len(fins),original_minus_cement_m=[min(fins),max(fins)])
    cfg.output.parent.mkdir(parents=True,exist_ok=True)
    rays=cfg.output.with_name('wall-and-window-samples.json.gz')
    rays.write_bytes(gzip.compress((json.dumps(rows,separators=(',',':'))+'\n').encode(),mtime=0))
    cfg.output.write_text(json.dumps(dict(order=377,model=uid,original_owner=4081,points_per_model=len(positions),total_records=len(rows),total_original_model_pairs=len(rows)*2,model_base_above_grade_m=base_z,comparisons=comparisons,samples_sha256=digest(rays),signed_inputs_sha256=digest(here/'signed-files.json')),indent=2)+'\n')

if __name__=='__main__':
    main()
