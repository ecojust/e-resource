#!/usr/bin/env python3
"""Finite roof-clearance rays against actual exported Fangta raw GLB triangles.

No builder import, mesh generation, renderer, model rewrite or whole-tower
collision traversal. Labels/ranges come from the raw-SHA-bound geometry sidecar.
"""
from pathlib import Path
from collections import defaultdict
import argparse,hashlib,json,math,struct,time
import numpy as np
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent

def need(ok,msg):
    if not ok: raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def metadata(path):
    b=path.read_bytes();return {'file':str(path),'bytes':len(b),'sha256':sha(b)}

def run(raw_path):
    start=time.monotonic();data=raw_path.read_bytes();raw_sha=sha(data)
    need(struct.unpack_from('<4sII',data)==(b'glTF',2,len(data)),'Invalid raw header')
    n,kind=struct.unpack_from('<II',data,12);need(kind==0x4e4f534a,'First chunk not JSON')
    doc=json.loads(data[20:20+n]);bn,bkind=struct.unpack_from('<II',data,20+n)
    need(bkind==0x004e4942 and 28+n+bn==len(data),'Invalid BIN chunk')
    binary=memoryview(data)[28+n:];geometry_path=raw_path.with_suffix('.geometry.json')
    side_bytes=geometry_path.read_bytes();side=json.loads(side_bytes)
    need(side['sha256']==raw_sha and side['bytes']==len(data),'Geometry sidecar not bound to raw')
    need(len(data)<100_000_000,'Raw exceeds file limit')
    need(doc.get('extras',{}).get('id')=='songjiang-fangta-pagoda','Wrong building')
    need(len(doc['meshes'])==1 and len(doc['nodes'])==1 and doc['nodes'][0].get('mesh')==0,'Unexpected raw scene')
    need(not any(k in doc['nodes'][0] for k in ['matrix','translation','rotation','scale']),'Transformed raw unsupported')
    need(len(doc['buffers'])==1 and 'uri' not in doc['buffers'][0],'External raw buffer')
    need(not doc.get('images') and not doc.get('textures'),'Unexpected photographic textures')
    for field,name in [('source_geometry_sha256','geometry-input.json'),('calibration_sha256','calibration.json')]:
        need(doc['extras'][field]==sha((ROOT/name).read_bytes()),'Actual raw/source binding mismatch: '+name)
    lock=json.loads((ROOT/'raw-source-freeze.json').read_text());locks={x['file']:x for x in lock['files']}
    for name in locks:
        b=(ROOT/name).read_bytes();need(len(b)==locks[name]['bytes'] and sha(b)==locks[name]['sha256'],'Frozen build input changed: '+name)
    prior=json.loads((HERE/'actual-raw-structure.json').read_text())
    need(prior['structure_passed'] is True and prior['raw']['sha256']==raw_sha,'Actual structure proof missing/different')
    def acc(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        need('sparse' not in a and not v.get('extensions') and not v.get('byteStride'),'Expected uncompressed tight raw accessor')
        width={'SCALAR':1,'VEC3':3}[a['type']];dt={5125:'<u4',5126:'<f4'}[a['componentType']]
        return np.frombuffer(binary,dtype=dt,offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*width).reshape(-1,width)
    by_mat=defaultdict(list)
    for row in side['part_summary']:by_mat[row['material']].append(row)
    labels={};total=0
    for primitive in doc['meshes'][0]['primitives']:
        need(primitive.get('mode',4)==4,'Nontriangle mesh')
        name=doc['materials'][primitive['material']]['name'];pos=acc(primitive['attributes']['POSITION']);tri=acc(primitive['indices']).ravel().reshape(-1,3);cursor=0
        for row in by_mat[name]:
            count=row['triangles'];label=row['label']
            if '/pan/' in label or '/cover/' in label or label.endswith('/continuous-curved-roof'):
                need(label not in labels,'Ambiguous selected part label')
                labels[label]=(pos,tri[cursor:cursor+count])
            cursor+=count
        need(cursor==len(tri),'Primitive/part ranges differ');total+=len(tri)
    need(total==side['triangles']==prior['triangles'],'Raw triangle counts differ')
    cache={};selected=set()
    def part(label):
        need(label in labels,'Missing actual raw part: '+label);selected.add(label)
        if label not in cache:
            pos,ids=labels[label]
            # Stored GLB is E,U,-N. Reorder actual FLOAT32 values to E,N,U.
            t=pos[ids].astype(np.float64);cache[label]=t[:,:,[0,2,1]]*np.array([1.,-1.,1.])
        return cache[label]
    def zsurface(t,xy,top=True):
        a=t[:,0,:2];b=t[:,1,:2]-a;c=t[:,2,:2]-a;d=np.asarray(xy)-a
        det=b[:,0]*c[:,1]-b[:,1]*c[:,0];idx=np.flatnonzero(det>1e-12 if top else det< -1e-12)
        b=b[idx];c=c[idx];d=d[idx];dd=det[idx];tt=t[idx]
        u=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/dd;v=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/dd
        keep=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
        vals=tt[:,0,2]+u*(tt[:,1,2]-tt[:,0,2])+v*(tt[:,2,2]-tt[:,0,2])
        need(keep.any(),'Sample ray missed actual part')
        return float(max(vals[keep]) if top else min(vals[keep]))
    geometry=json.loads((ROOT/'geometry-input.json').read_text());cal=json.loads((ROOT/'calibration.json').read_text())
    ring=np.asarray(doc['extras']['model_square_ring_enu'],float)
    if np.array_equal(ring[0],ring[-1]):ring=ring[:-1]
    need(len(ring)==4,'Expected independent square architectural core, not owner quadrilateral')
    frame=geometry['proposed_architecture_frame'];u=np.asarray(frame['axis_u_east_north']);vv=np.asarray(frame['axis_v_east_north']);half=cal['model_square_base_side_m']/2
    expected=np.asarray([half*u-half*vv,-half*u-half*vv,-half*u+half*vv,half*u+half*vv])
    need(np.allclose(ring,expected,rtol=0,atol=1e-12),'Architectural ring/source frame mismatch')
    def xy(v,e,s,t):
        inner=ring*(v['wall_scale']*.945 if v['level']<9 else .075);outer=ring*v['roof_scale']
        return (inner[e]*(1-s)+inner[(e+1)%4]*s)*(1-t)+(outer[e]*(1-s)+outer[(e+1)%4]*s)*t
    def counts(v,e):
        outer=np.linalg.norm((ring[(e+1)%4]-ring[e])*v['roof_scale']);radial=np.linalg.norm(xy(v,e,.5,1)-xy(v,e,.5,0))
        return max(8,round(outer/v['tile_lane_width_m'])),max(3,math.ceil(radial/v['tile_course_length_m']))
    summary={k:{'samples':0,'minimum_m':float('inf'),'maximum_m':-float('inf'),'nonpositive_samples':0,'worst_sample':None} for k in ['tile_bottom_minus_substrate_top','cover_bottom_minus_pan_top','upper_course_bottom_minus_lower_top']}
    samples=[];negative_controls={}
    def sample(kind,upper_label,lower_label,point,location):
        upper=part(upper_label);lower=part(lower_label);clear=zsurface(upper,point,False)-zsurface(lower,point,True)
        q=summary[kind];q['samples']+=1;q['nonpositive_samples']+=int(clear<=0);q['maximum_m']=max(q['maximum_m'],clear)
        item={'kind':kind,'upper':upper_label,'lower':lower_label,'xy_enu_m':point.tolist(),'clearance_m':clear,**location};samples.append(item)
        if clear<q['minimum_m']:q['minimum_m']=clear;q['worst_sample']=item
        if kind not in negative_controls:
            shifted=upper.copy();shifted[:,:,2]-=clear+.005
            bad=zsurface(shifted,point,False)-zsurface(lower,point,True)
            need(bad<-.0049,'Overlap negative control did not reject')
            negative_controls[kind]={'method':'In-memory copy of selected actual upper triangles shifted down by measured clearance plus5mm; disk assets unchanged','simulated_clearance_m':bad,'rejected':True}
    for v in cal['levels']:
        L=v['level'];roof=f'L{L}/continuous-curved-roof'
        for e in range(4):
            cols,rows=counts(v,e);overlap=min(.025,.10/rows)
            for col in sorted(set([0,cols//2,cols-2])):
                for row in sorted(set([0,rows//2,rows-1])):
                    pan=f'L{L}/pan/e{e}/c{col}/r{row}';cover=f'L{L}/cover/e{e}/c{col}/r{row}'
                    t0=row/rows;t1=min(1,(row+1)/rows+overlap);t=(t0+t1)/2
                    loc={'level':L,'edge':e,'column':col,'row':row}
                    for frac in [.15,.5,.85]:sample('tile_bottom_minus_substrate_top',pan,roof,xy(v,e,(col+.025+.95*frac)/cols,t),{**loc,'width_fraction':frac})
                    for frac in [.86,.90,.94,.97]:sample('cover_bottom_minus_pan_top',cover,pan,xy(v,e,(col+frac)/cols,t),{**loc,'cell_x':frac})
                for row in sorted(set([0,(rows-1)//2,rows-2])):
                    for kind in ['pan','cover']:
                        upper=f'L{L}/{kind}/e{e}/c{col}/r{row}';lower=f'L{L}/{kind}/e{e}/c{col}/r{row+1}'
                        for frac in [.2,.5,.8]:
                            s=(col+.5)/cols if kind=='pan' else (col+1)/cols;t=(row+1)/rows+overlap*frac
                            sample('upper_course_bottom_minus_lower_top',upper,lower,xy(v,e,s,t),{'level':L,'edge':e,'column':col,'row':row,'kind_of_tile':kind,'overlap_fraction':frac})
    need(all(q['samples']>0 for q in summary.values()),'No finite samples')
    passed=all(v['nonpositive_samples']==0 for v in summary.values())
    return {'schema':'fangta-actual-exported-raw-roof-pairs-v1','finite_sample_passed':passed,'actual_raw_sha256':raw_sha,'actual_raw_bytes':len(data),'actual_raw_triangles':total,'part_manifest':{'file':str(geometry_path),'sha256':sha(side_bytes)},'source_geometry':metadata(ROOT/'geometry-input.json'),'calibration':metadata(ROOT/'calibration.json'),'build_source_lock':metadata(ROOT/'raw-source-freeze.json'),'actual_structure_proof':metadata(HERE/'actual-raw-structure.json'),'elapsed_seconds':time.monotonic()-start,'selected_part_count':len(selected),'selected_labels':sorted(selected),'sampling':{'levels':list(range(1,10)),'model_edges':list(range(4)),'columns':'first, middle, penultimate','rows':'first, middle, last for substrate/lateral; first,middle,penultimate for course pairs','total_finite_samples':len(samples)},'summary':summary,'overlap_negative_controls':negative_controls,'samples':samples,'model_appearance_accepted':False,'whole_roof_collision_free_claim':False,'geometry_regenerated':False,'browser_or_Blender_run':False,'original_geometry_report_modified':False,'scope':'Vertical interpolation of actual exported FLOAT32 triangles, selected from raw-SHA-bound helper part ranges. All measured z values come from actual GLB, not analytic source heights. Source/calibration only choose XY ray locations. These are finite samples onall 4 model faces and 9 levels, not all roof tiles, continuous collision proof, tile contact/support proof, native visual approval or browser acceptance.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();output=a.output.resolve()
    need(output.is_relative_to(HERE) and not output.exists(),'Use a new output inside independent-review')
    report=run(a.raw.resolve());encoded=json.dumps(report,ensure_ascii=False,indent=2)+'\n';need(len(encoded.encode())<3_000_000,'Report exceeds bounded size');output.write_text(encoded)
    print(json.dumps({k:report[k] for k in ['finite_sample_passed','actual_raw_sha256','elapsed_seconds','selected_part_count','summary']},indent=2));raise SystemExit(0 if report['finite_sample_passed'] else 1)
if __name__=='__main__':main()
