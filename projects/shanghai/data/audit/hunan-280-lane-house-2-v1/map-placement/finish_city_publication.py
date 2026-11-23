"""Construct the registered candidate descriptor and bind the independently tested city assets."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def publish(w,project):
    s=project/'measurements'
    f=w/'final/placement';d=w/'city-clearance'
    identifier='xuhui-hunan-280-lane-house-2'
    slug='hunan-280-lane-house-2'
    prefix='assets/models/candidates/'+identifier+'/'
    survey=read(s/'house-cameras.json');src=d/'rebuilt'
    geo=read(f/'map-triangle-footprint.json')
    bounds=read(src/'full-city-source.geometry.json')['bounds_glb']
    assets={}
    for level,name in [('full','web'),('lod','lod')]:
        glb=f/f'map-front-{name}.glb';geometry=read(src/f'{level}-city-source.geometry.json');closure=read(src/f'{level}-city-source.clearance.json')
        assert sha(src/f'{level}-city-source.glb')==sha(d/f'meshes/{level}-city-source.glb')==closure['model_sha256']
        assets[name]={'file':prefix+glb.name,'bytes':glb.stat().st_size,'sha256':sha(glb),'triangles':geometry['triangles']}
        shutil.copyfile(src/f'{level}-city-source.clearance.json',f/f'{level}-closed-relief.json')
    name='湖南路280弄2号五层窗墙、弧窗与院门'
    note='以八个已登记机位和两处补充东侧观测定位。东墙与原城716号户相邻，城市模型在两处相接线边缘保留2厘米余量。'
    loc={'id':identifier,'lng':survey['origin_wgs'][0],'lat':survey['origin_wgs'][1],'heading':(survey['x_azimuth_deg']-90)%360,'scale':1,'altitude':0,'placement':{'status':'estimated','note':note},
         'navigation':{'listed':False},'collision_geometry':geo['projection_wgs84'],'replacement_geometry':None}
    write(f/'placement.json',loc)
    row={'id':identifier,'name':name,'kind':'building','candidate_id':identifier,'detail_level':'architectural','districtId':'310104','district_name':'徐汇区','architecture_style':'五层临街转角住宅',
         **{k:v for k,v in loc.items()if k not in ['id','navigation']},'height_m':bounds['max'][1],'height_estimated':True,'bounds_glb':bounds,'assets':assets,
         'model':assets['web']['file'],'lod_model':assets['lod']['file'],'web_bytes':assets['web']['bytes'],'web_sha256':assets['web']['sha256'],'lod_bytes':assets['lod']['bytes'],'lod_sha256':assets['lod']['sha256'],
         'triangles':assets['web']['triangles'],'lod_triangles':assets['lod']['triangles'],'individual_page':slug+'.html','minDistance':0,'maxDistance':840,'lod_switch_in_m':130,'lod_switch_out_m':180,
         'partial_model':True,'model_scope':'湖南路南立面、弄内斜墙、四层弧窗、2号院门和东侧三樘小窗。','source_feature_ids':{'building':[],'building_part':[]},'detail_note':note,'complete_photo_reconstruction_accepted':False}
    write(f/'candidate-row.json',row)
    for path in (d/'source').glob('*'):
        if path.suffix in ['.py','.json']:shutil.copyfile(path,f/path.name)
    for name in ['old-city-sections.json','actual-seams-full-source.json','actual-seams-lod-source.json','original-vs-new-surfaces.json','city-only-vs-original-neighbors.json','web-city-vs-original-neighbors.json']:
        shutil.copyfile(w/'placement/ordinary'/name,f/name)
    data={'subject':identifier,'frame_extent':'five-storey photographed exterior and eave bands; no inferred complete roof','position':{k:v for k,v in loc.items()if k in ('lng','lat','heading','scale','altitude')},
          'original_city':{'macro':'14-13718-6695','retained_ids':[716,1629,369],'replacements':[],'source_footprint_comparison':'The minimum overlapping site-model coping Z18.1759 exceeds the old extruded 18 m block. Actual near tile has independent projecting edges; real mesh intersection test is authoritative.',
               'private_case_before':{'full':26,'lod':26,'conditions':'original near roof and window-reveal relief, exact triangle intersections'},
               'city_after':{'near_and_far_source_and_decoded_intersections':0,'contact_xy_safety_margin_m':.02,'contact_z_safety_margin_m':.02,'actual_source_comparisons':6,'actual_decoded_comparisons':6}},
          'per_lod':{},'standalone_original':{'full':sha(w/'whole/rounded-street-end/full-source.glb'),'lod':sha(w/'whole/rounded-street-end/lod-source.glb'),'individual_page':slug+'.html'},
          'inputs_and_outputs':{}}
    for level,role in [('full','web'),('lod','lod')]:
        closure=read(f/f'{level}-closed-relief.json');a=read(f/f'{level}-eastern-26.json');b=read(f/f'{level}-side-windows.json')
        data['per_lod'][level]={**assets[role],'source_sha256':closure['model_sha256'],'decoded_sha256':sha(f/f'decoded-{level}.glb'),'closed_components':closure['changes']['closure']['total'],
                               'untouched_components':closure['changes']['closure']['untouched'],'independent_east_observations':[a['matched'],a['total']],'side_observations':[b['exact'],b['total']],
                               'cut_cubic_metres':{k:closure['changes'][k]['removed_volume_m3']for k in ('eave','base')}}
    for path in sorted(f.iterdir()):
        if path.name=='publication.json' or path.name.startswith('decoded-'):continue
        if path.is_file():data['inputs_and_outputs'][path.name]={'bytes':path.stat().st_size,'sha256':sha(path)}
    write(f/'publication.json',data)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('working',type=Path);parser.add_argument('project',type=Path);args=parser.parse_args()
    publish(args.working,args.project)
