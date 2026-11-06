"""Independent rays over serialized postal-building surfaces.

No author geometry/probe modules are imported. Expected families come from the
reviewed photographs and separately frozen site/height contract. This report
covers actual triangle geometry; visual/native/browser checks are separate.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from shapely.geometry import shape,Point
from shapely.geometry.polygon import orient
import importlib.util
HELPER=Path(__file__).with_name('independent-glb-review-helpers.py')
SPEC=importlib.util.spec_from_file_location('postal_independent_glb_review',HELPER)
MOD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)
SerialScene,material_appearance=MOD.SerialScene,MOD.material_appearance


def inspect(path,contract):
    s=SerialScene(path);checks={'finite_nondegenerate':bool(np.isfinite(s.tri).all() and s.areas.min()>1e-12)}
    # The final wall lies 0.85m inside the exterior source envelope. The court
    # mouth uses its separate U-plan; these are authored dimensions, not surveys.
    body=orient(shape(contract['main_u_footprint_local_enu']).intersection(shape(contract['author_envelope_local_enu']).buffer(-.85,join_style=2)),sign=1.)
    vertices=list(body.exterior.coords);perimeter=[];roof=[]
    for edge,(a,b) in enumerate(zip(vertices,vertices[1:])):
        a=np.array(a);b=np.array(b);v=b-a;length=np.linalg.norm(v)
        if length<2:continue
        n=np.array([v[1],-v[0]])/length
        for fraction in [.17,.41,.73]:
            p=a+v*fraction
            for z in [1.2,4.8,8.3,13.2,18.0,19.35]:
                hit=s.ray([*(p+n*.95),z],[-n[0],-n[1],0],3.6)
                perimeter.append({'edge':edge,'fraction':fraction,'height_m':z,'hit':hit,'passed':hit is not None})
            for inset in [.08,.30,.50]:
                p2=p-n*inset
                if not body.contains(Point(p2)):continue
                hit=s.ray([*p2,19.85],[0,0,-1],1.0)
                roof.append({'edge':edge,'fraction':fraction,'inset_m':inset,'hit':hit,'passed':hit is not None and hit['point_enu_m'][2]>19.05})
    glass=[r for r in perimeter if r['hit'] and r['hit']['material']=='recessed glass']
    checks['perimeter_backstops_exist']=all(r['passed'] for r in perimeter)
    checks['window_backing_is_recessed']=len(glass)>=10 and all(r['hit']['distance_m']>1.05 for r in glass)
    checks['continuous_roof_wall_seams']=all(r['passed'] for r in roof)
    frame=contract['facade_uv_frame'];o=np.asarray(frame['origin_enu_m']);t=np.asarray(frame['u_axis_enu']);v=np.asarray(frame['v_axis_enu'])
    src=np.asarray(contract['source_geometry_local_enu']['coordinates'][0][:-1]);a,b=src[0],src[6];tt=(b-a)/np.linalg.norm(b-a);nn=np.array([tt[1],-tt[0]])
    # Registered author's tower position is a separate explicit test input.
    center=np.array([43.0151853324771,-6.141230763948351]);tower_t=np.array([.4819097604926674,.8762208527203059]);tower_n=np.array([tower_t[1],-tower_t[0]])
    opening=[];ceiling=[]
    for axis,label in [(tower_t,'tangent'),(tower_n,'normal')]:
        for sign in [-1,1]:
            p=center+axis*6*sign;direction=-axis*sign
            hit=s.ray([*p,37.25],[*direction,0],12)
            opening.append({'axis':label,'side':sign,'origin_enu_m':[*p,37.25],'hit':hit,'passed':hit is None})
    for u in [-2,0,2]:
        for vv in [-2,0,2]:
            p=center+tower_t*u+tower_n*vv;hit=s.ray([*p,41.05],[0,0,1],1.2)
            ceiling.append({'u_m':u,'v_m':vv,'hit':hit,'passed':hit is not None and 41.5<hit['point_enu_m'][2]<42.01})
    checks['tower_four_true_through_openings']=all(r['passed'] for r in opening)
    checks['tower_ceiling_closes_colonnade']=all(r['passed'] for r in ceiling)
    clock_ids=[i for i,n in enumerate(s.materials) if n=='ivory clock face'];clock=s.tri[np.isin(s.mi,clock_ids)].reshape(-1,3)
    if len(clock):
        normal=(clock[:,:2]-center)@tower_n;across=(clock[:,:2]-center)@tower_t
        clock_detail={'vertices':len(clock),'normal_bounds_m':[float(normal.min()),float(normal.max())],'tangent_bounds_m':[float(across.min()),float(across.max())],'height_bounds_m':[float(clock[:,2].min()),float(clock[:,2].max())]}
        checks['single_front_clock_only']=normal.min()>4.55 and normal.max()<4.65 and abs(across).max()<1.86 and clock[:,2].min()>23.9 and clock[:,2].max()<27.8
    else:clock_detail={};checks['single_front_clock_only']=False
    # Two photographed narrow side panels must be the first visible surface,
    # not a dark solid buried behind the sandstone curved shoulder.
    side_windows=[]
    for side in [-1,1]:
        for height in [24.75,25.0,25.3]:
            p=center+tower_t*(8*side)+tower_n*.8;direction=-tower_t*side
            hit=s.ray([*p,height],[*direction,0],3)
            passed=hit is not None and hit['material']=='dark bronze'
            side_windows.append({'side':side,'height_m':height,'origin_enu_m':[*p,height],'direction_enu':[*direction,0],'hit':hit,'passed':passed})
    checks['curved_shoulder_side_windows_are_visible']=all(row['passed'] for row in side_windows)
    canopy=[];ends=[]
    for u in [0,20,40,65]:
        for vv in [22,27,32,37,42]:
            p=o+t*u+v*vv;hit=s.ray([*p,24.0],[0,0,-1],5.)
            canopy.append({'u_m':u,'v_m':vv,'hit':hit,'passed':hit is not None and hit['material'] in ['court glazing','court gold steel'] and 19.4<hit['point_enu_m'][2]<23.1})
    # The photographed east terminal has a vertical gridded glazing closure.
    # An end-cap check catches a bare arch opening below the curved roof.
    for vv in [27,32,37]:
        p=o+t*72.7+v*vv;hit=s.ray([*p,20.5],[-t[0],-t[1],0],1.2)
        ends.append({'end':'east','v_m':vv,'hit':hit,'passed':hit is not None and hit['material'] in ['court glazing','court gold steel']})
    checks['canopy_top_is_continuous_curved_grid']=all(r['passed'] for r in canopy)
    checks['canopy_east_glazed_end_closed']=all(r['passed'] for r in ends)
    checks={key:bool(value) for key,value in checks.items()}
    return {'asset':s.asset,'triangles':len(s.tri),'minimum_triangle_area_m2':float(s.areas.min()),'bounds_enu_m':[s.tri.min((0,1)).tolist(),s.tri.max((0,1)).tolist()],'checks':checks,'passed':all(checks.values()),'perimeter_probe_count':len(perimeter),'perimeter_failures':[r for r in perimeter if not r['passed']],'recessed_glass_sample_count':len(glass),'recessed_glass_sample_details':glass[:24],'roof_seam_probe_count':len(roof),'roof_seam_failures':[r for r in roof if not r['passed']],'tower_openings':opening,'tower_ceilings':ceiling,'clock':clock_detail,'side_windows':side_windows,'canopy_top':canopy,'canopy_ends':ends},s


def compare_materials(raw,web):
    def shader_factors(data):
        converted=json.loads(json.dumps(data))
        for material in converted['materials'].values():
            for key in ['baseColorFactor','emissiveFactor']:
                material[key]=np.asarray(material[key],dtype='<f4').tolist()
            for key in ['metallicFactor','roughnessFactor','alphaCutoff']:
                material[key]=float(np.float32(material[key]))
        return converted
    delta=0.
    for name,a in raw['materials'].items():
        if name not in web['materials']:continue
        b=web['materials'][name]
        for key in ['baseColorFactor','emissiveFactor','metallicFactor','roughnessFactor','alphaCutoff']:
            delta=max(delta,float(np.max(np.abs(np.asarray(a[key])-np.asarray(b[key])))))
    return {'original_json_numerical_factors_exactly_equal':raw==web,'gpu_float32_appearance_exactly_equal':shader_factors(raw)==shader_factors(web),'maximum_original_decimal_factor_difference':delta,'method':'Compare shader numerical factors after exact FLOAT32 conversion; alpha modes, sidedness, textures and extensions remain exact. No arbitrary tolerance and no model mutation.'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--web-decoded',type=Path);ap.add_argument('--web-original',type=Path);ap.add_argument('--lod-decoded',type=Path);ap.add_argument('--lod-original',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    contract=json.loads(a.contract.read_text());result={'schema':'postal-independent-geometry-v1','model_id':'hongkou-general-post-office','variants':{},'mode':'all_final_variants' if a.web_decoded and a.lod_decoded else 'draft_raw_only','scope':'Independent direct rays on serialized transformed triangles; no author geometry or author probe imports. Main body/clock dimensions are authored estimates, not a measured survey.'};scenes={}
    for name,path,original in [('raw',a.raw,a.raw),('web',a.web_decoded,a.web_original),('lod',a.lod_decoded,a.lod_original)]:
        if path is None:continue
        row,s=inspect(path,contract);scenes[name]=s
        row['material_appearance']=material_appearance(path)
        if original is not None:row['production_asset']={'file':original.name,'bytes':original.stat().st_size,'sha256':hashlib.sha256(original.read_bytes()).hexdigest()}
        result['variants'][name]=row;print(name,json.dumps({'checks':len(row['checks']),'failed':[k for k,v in row['checks'].items() if not v],'triangles':row['triangles']}),flush=True)
    if 'web' in scenes:
        raw,web=scenes['raw'].surface_digest(),scenes['web'].surface_digest();result['raw_web_oriented_float32_material_surfaces_identical']=raw==web;result['material_surface_digests']={'raw':raw,'web':web}
        result['material_comparison']=compare_materials(result['variants']['raw']['material_appearance'],result['variants']['web']['material_appearance'])
        result['raw_web_material_appearance_float32_identical']=result['material_comparison']['gpu_float32_appearance_exactly_equal']
    result['bindings']=[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [Path(__file__),HELPER,a.contract]]
    result['passed']=all(r['passed'] for r in result['variants'].values()) and result.get('raw_web_oriented_float32_material_surfaces_identical',True) and result.get('raw_web_material_appearance_float32_identical',True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
