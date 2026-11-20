"""Verify binary and decoded preservation, the open arch and each of the five sculptures."""
from pathlib import Path
from hashlib import sha256
import argparse,json,math,runpy,subprocess,tempfile
import numpy as np
import shapely
from shapely.geometry import Polygon
from build_relief import chunks

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
HELPER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
DECODE=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
MODULE=PROJECT/'vendor/meshopt_decoder.module.js'
base=json.loads((HERE/'baseline.json').read_bytes())
frame=json.loads((HERE/'facade-frame.json').read_bytes())
api=runpy.run_path(str(HELPER))
tangent=np.array(frame['world_basis_u']);outward=-np.array(frame['world_basis_v'])
cx,cy=frame['front_center'];mid=tangent*(cx+frame['left_bay_center_u_m'])-outward*cy

def project(tri):
    local=tri.copy();en=tri[:,:,:2]-mid
    local[:,:,0]=en@tangent;local[:,:,1]=tri[:,:,2];local[:,:,2]=en@outward
    return local

def ray(tri,mat,x,z,labels):
    index,distance,point=api['first_hit'](tri,np.array([x,z,2.]),np.array([0.,0.,-1.]))
    return {'outward_m':None if not np.isfinite(distance) else float(2-distance),
            'material':None if not np.isfinite(distance) else labels[mat[index]]}

def sha(p):return sha256(p.read_bytes()).hexdigest()

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('prior',type=Path);cli.add_argument('revised',type=Path);cli.add_argument('report',type=Path)
    args=cli.parse_args();result={}
    with tempfile.TemporaryDirectory()as work:
        for role in ['raw','web','lod']:
            old=args.prior/(role+'.glb');new=args.revised/(role+'.glb')
            assert sha(old)==base['assets'][role]['sha256']
            od,obin=chunks(old);nd,nbin=chunks(new)
            assert nbin[:len(obin)]==obin
            for key in ['asset','materials','images','textures','samplers','extensionsRequired','extensionsUsed','extensions']:
                assert nd.get(key)==od.get(key),key
            for key in ['bufferViews','accessors','meshes','nodes']:
                assert nd[key][:len(od[key])]==od[key]
            assert nd['scenes'][0]['nodes'][:len(od['scenes'][0]['nodes'])]==od['scenes'][0]['nodes']
            assert len(nd['nodes'])==len(od['nodes'])+5
            paths=[]
            for which,file in [('before',old),('after',new)]:
                path=file
                if role!='raw':
                    path=Path(work)/(role+'-'+which+'.glb')
                    subprocess.run(['node',DECODE,file,path,MODULE],check=True,stdout=subprocess.DEVNULL)
                paths.append(path)
            ot,om,names,_=api['load_triangles'](paths[0]);nt,nm,names2,_=api['load_triangles'](paths[1])
            assert names==names2 and len(names)==10
            assert np.array_equal(ot,nt[:len(ot)]) and np.array_equal(om,nm[:len(ot)])
            assert np.array_equal(ot.min((0,1)),nt.min((0,1))) and np.array_equal(ot.max((0,1)),nt.max((0,1)))
            extra=project(nt[len(ot):]);assert np.isfinite(extra).all();lo,hi=extra.min((0,1)),extra.max((0,1))
            assert lo[0]>-3.12 and hi[0]<3.12 and lo[1]>9.55 and hi[1]<11.41,(lo,hi)
            assert {names[i]for i in nm[len(om):]}=={'Carved limestone and capitals'}
            src=project(ot);keep=(src[:,:,0].max(1)>-3.3)&(src[:,:,0].min(1)<3.3)&(src[:,:,1].max(1)>8.0)&(src[:,:,1].min(1)<11.52)&(src[:,:,2].min(1)<1.20)
            old_local=src[keep];old_mats=om[keep]
            # The structural source has a 24-segment window arch. Check the
            # analytic, slightly larger opening, including its full lower rectangle.
            r=frame['opening_width_m']/2;spring=frame['opening_spring_m']
            opening=Polygon([(-r,5.2),(r,5.2),*[(r*math.cos(a),spring+r*math.sin(a))for a in np.linspace(0,math.pi,241)]])
            s1=extra[:,1,:2]-extra[:,0,:2];s2=extra[:,2,:2]-extra[:,0,:2]
            area=abs(s1[:,0]*s2[:,1]-s1[:,1]*s2[:,0])
            polygons=shapely.polygons(np.concatenate((extra[area>1e-10,:,:2],extra[area>1e-10,:1,:2]),axis=1))
            overlap=float(np.sum(shapely.area(shapely.intersection(polygons,opening))))
            assert overlap<1e-8,overlap
            alltri=np.concatenate((old_local,extra));allmat=np.concatenate((old_mats,nm[len(om):]))
            checks=[]
            for sign in [-1,1]:
                # These positions are written independently in metres in the front-elevation frame.
                for label,position in [('head',(-2.045,10.982)),('cheek',(-1.991,10.952)),
                                       ('forearm',(-1.946,10.59)),('bent knee',(-2.49,10.408)),
                                       ('wing',(-2.40,10.86)),('inner leaf',(-1.500,10.93)),
                                       ('lower scroll',(-2.60,9.925))]:
                    x,z=position;x*=sign
                    before=ray(old_local,old_mats,x,z,names);after=ray(alltri,allmat,x,z,names)
                    checks.append({'part':label,'side':sign,'u_m':x,'z_m':z,'before':before,'after':after})
            for label,x,z in [('beast brow',.108,11.027),('muzzle',.005,10.92),('open-jaw rim',.09,10.733)]:
                checks.append({'part':label,'side':0,'u_m':x,'z_m':z,'before':ray(old_local,old_mats,x,z,names),'after':ray(alltri,allmat,x,z,names)})
            for row in checks:
                first=row['before']['outward_m'];second=row['after']['outward_m']
                row['changed']=first is not None and second is not None and second-first>.016 and row['after']['material']=='Carved limestone and capitals'
            controls=[]
            for bay,center in [('south',0),('middle',6.0625),('north',12.125)]:
                nearby=(src[:,:,0].max(1)>center-3.3)&(src[:,:,0].min(1)<center+3.3)&(src[:,:,1].max(1)>8.3)&(src[:,:,1].min(1)<11.52)
                before_tri=src[nearby];before_mat=om[nearby]
                after_tri=np.concatenate((before_tri,extra));after_mat=np.concatenate((before_mat,nm[len(om):]))
                samples=[('central frame',0,8.85),('recessed glazing',.44,9.25)]
                if bay!='south':
                    samples.extend([('inherited arch key',0,10.55),('inherited spandrel',2.36,10.87)])
                for name,offset,z in samples:
                    x=center+offset
                    before=ray(before_tri,before_mat,x,z,names)
                    after=ray(after_tri,after_mat,x,z,names)
                    assert before==after and before['material'] is not None,(bay,name,before,after)
                    controls.append({'bay':bay,'position':name,'u_m':x,'z_m':z,'before':before,'after':after})
            result[role]={'source_sha256':sha(old),'sha256':sha(new),'bytes':new.stat().st_size,
                          'original_payload_sha256':sha256(obin).hexdigest(),'original_triangles_verified_in_order':len(ot),
                          'total_scene_triangles':len(nt),'added_triangles':len(extra),'bounding_box_unchanged':True,
                          'all_ten_materials_identical':True,'original_window_openings':96,
                          'added_geom_overlap_with_analytic_arch_m2':overlap,'extent_from_left_bay_center_height_outward_m':[lo.tolist(),hi.tolist()],
                          'probes':checks,'untouched_opening_and_adjacent_bay_probes':controls}
    args.report.write_text(json.dumps({'variants':result,'source_frame_sha256':sha(HERE/'facade-frame.json'),
        'helper_sha256':sha(HELPER),'decoder_sha256':sha(DECODE),'meshopt_sha256':sha(MODULE),'script_sha256':sha(Path(__file__))},indent=2)+'\n')
    for role,rec in result.items():
        print(role,rec['added_triangles'],[r['part']for r in rec['probes']if not r['changed']])
    assert all(all(r['changed'] for r in rec['probes'])for rec in result.values())

if __name__=='__main__':main()
