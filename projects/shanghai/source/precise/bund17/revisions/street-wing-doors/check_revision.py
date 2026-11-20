"""Compare all original V4.4 scene triangles and independently probe both new door installations."""
import argparse,json,struct,runpy
from hashlib import sha256
from pathlib import Path
from collections import Counter
import numpy as np


def glb(path):
    b=path.read_bytes();length=struct.unpack_from('<I',b,12)[0]
    return json.loads(b[20:20+length]),b[28+length:]


def main():
    ap=argparse.ArgumentParser()
    for key in ('source','prior','revised','decoded','helper','report'):ap.add_argument(key,type=Path)
    opt=ap.parse_args();api=runpy.run_path(str(opt.helper));load=api['load_triangles'];hit=api['first_hit']
    src=json.loads((opt.source/'news-footprint.json').read_bytes());a,b=np.array(src['polygon_local_east_north'])[2:4]
    mid=(a+b)/2;t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);basis=np.stack([t,n],axis=1);width=np.linalg.norm(b-a)/2-1.775
    def local(tri):
        coords=tri.copy();coords[:,:,:2]=(coords[:,:,:2]-mid)@basis
        return coords
    report={}
    for role in ('raw','web','lod'):
        prev=opt.prior/(role+'.glb');new=opt.revised/(role+'.glb')
        past,oldb=glb(prev);now,newb=glb(new)
        assert newb[:len(oldb)]==oldb
        assert past.keys()==now.keys()
        for k,v in past.items():
            if k in ('meshes','materials','bufferViews','nodes','accessors'):
                assert now[k][:len(v)]==v and len(now[k])>len(v),k
            elif k=='buffers':assert now[k][1:]==v[1:]
            elif k=='scenes':assert now[k][0]['nodes'][:len(v[0]['nodes'])]==v[0]['nodes']
            else:assert now[k]==v,k
        prevmesh=prev if role=='raw'else opt.decoded/'prior'/(role+'.glb')
        newmesh=new if role=='raw'else opt.decoded/'output'/(role+'.glb')
        before,om,o_labels,_=load(prevmesh);after,nm,n_labels,_=load(newmesh)
        assert np.array_equal(before,after[:len(before)]) and np.array_equal(om,nm[:len(om)])
        assert n_labels[:len(o_labels)]==o_labels
        assert np.array_equal(before.min((0,1)),after.min((0,1))) and np.array_equal(before.max((0,1)),after.max((0,1)))
        tri=local(after);samples=[]
        for sign,side in [(-1,'south'),(1,'north')]:
            axis=sign*width
            mask=(tri[:,:,0].max(1)>axis-1.15)&(tri[:,:,0].min(1)<axis+1.15)&(tri[:,:,2].min(1)<4.0)&(tri[:,:,2].max(1)>.15)&(tri[:,:,1].max(1)>-.4)
            subset=tri[mask];mats=nm[mask];old_subset=tri[:len(before)][mask[:len(before)]];oldmat=om[mask[:len(before)]]
            def ray(points,material,u,h):
                index,d,_=hit(points,[axis+u,.8,h],[0,-1,0])
                if not np.isfinite(d):return None,None
                return n_labels[material[index]],round(float(.8-d),5)
            previous=[];new_fields=[]
            for h in (.72,1.05,1.44,1.82,2.20,2.58):
                for x in (-.77,-.49,-.22,-.045,.045,.22,.49,.77):
                    m,d=ray(old_subset,oldmat,x,h);previous.append((m,d))
                    m,d=ray(subset,mats,x,h);new_fields.append((m,d))
            assert all(m=='recessed blue grey glazing' and abs(d+.24)<.001 for m,d in previous)
            assert all(m!='recessed blue grey glazing' and d>-.237 for m,d in new_fields)
            legacy_bars=[]
            for x in (-.375,.375):
                for z in (.74,1.12,1.48,1.88,2.29,2.87,3.16):
                    old_m,old_d=ray(old_subset,oldmat,x,z)
                    new_m,new_d=ray(subset,mats,x,z)
                    assert old_m=='painted window frames' and new_m!=old_m and new_d>old_d+.006, (role,side,x,z,old_m,new_m,old_d,new_d)
                    legacy_bars.append({'u':x,'z':z,'old':old_m,'new':new_m,'old_depth_m':old_d,'new_depth_m':new_d})
            for z in (.15+(8.5-.15)/7,.15+2*(8.5-.15)/7):
                for x in (-.8,-.3,.3,.8):
                    old_m,old_d=ray(old_subset,oldmat,x,z)
                    new_m,new_d=ray(subset,mats,x,z)
                    assert old_m=='painted window frames' and old_m!=new_m and new_d>old_d+.006,(role,side,x,z,old_m,new_m)
                    legacy_bars.append({'u':x,'z':z,'old':old_m,'new':new_m,'old_depth_m':old_d,'new_depth_m':new_d})
            case=[('left and right gold meeting strips',dx,1.46,'Warm gilt bronze')for dx in (-.081,.081)]
            case+= [('side leaf black panel',dx,.72,'Recessed black door field')for dx in (-.60,.60)]
            case+= [('each central gold drop',dx,1.31,'Warm gilt bronze')for dx in (-.5,.5)]
            case+= [('each medallion above the drop',dx,2.122,'Warm gilt bronze')for dx in (-.5,.5)]
            case+= [('dark transom',.20,3.1,'Recessed black door field'),('gilt head rail',.47,2.597,'Warm gilt bronze'),
                     ('outer dark jamb',1.04,2.13,'Patinated black bronze'),('address numeral 1',-.05,3.58,'Shadowed address numerals'),
                     ('address numeral 7',.054,3.621,'Shadowed address numerals')]
            witnesses=[]
            for label,x,z,expected in case:
                m,d=ray(subset,mats,x,z);assert m==expected,(role,side,label,x,z,m,d,expected)
                witnesses.append({'part':label,'facade_u_from_door_axis_m':x,'z_m':z,'material':m,'outward_m':d})
            # Check geometry attachment after restricting to the actual added faces.
            additions=tri[len(before):];specific=additions[np.mean(additions[:,:,0],axis=1)*sign>0]
            assert np.max(abs(specific[:,:,0]-axis))<1.097 and np.max(specific[:,:,1])<.128
            assert np.min(specific[:,:,2])>.20 and np.max(specific[:,:,2])<3.65
            samples.append({'side':side,'previous_48_rays':{str(k):v for k,v in Counter(previous).items()},
               'new_materials_at_preexisting_samples':dict(Counter(m for m,d in new_fields)),'covered_archived_mullion_witnesses':legacy_bars,'specific_witnesses':witnesses})
        photos=[]
        for img in now.get('images',[]):
            view=now['bufferViews'][img['bufferView']];off=view.get('byteOffset',0)
            photos.append(sha256(newb[off:off+view['byteLength']]).hexdigest())
        assert photos==([]if role=='lod'else['0a7efe74f0c8acd24f115123c70f538793a07249a44cc430028c85ced58cd7b7'])
        report[role]={'old_triangles':len(before),'unchanged_triangles_in_order':len(before),'total_scene_triangles':len(after),
             'added_triangles':len(after)-len(before),'all_original_materials_and_bounds_unchanged':True,
             'original_binary_payload_sha256':sha256(oldb).hexdigest(),'embedded_images':photos,
             'sha256':sha256(new.read_bytes()).hexdigest(),'bytes':new.stat().st_size,'street_doors':samples}
    opt.report.write_text(json.dumps({'variants':report,'reader_sha256':sha256(opt.helper.read_bytes()).hexdigest()},indent=2)+'\n')
    print({k:v['total_scene_triangles']for k,v in report.items()})


if __name__=='__main__':main()
