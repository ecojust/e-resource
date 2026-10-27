"""Lossless-position full web plus separately authored LOD, retaining provenance."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess
ROOT=Path(__file__).resolve().parent.parent
ID='changning-hudec-residence'
def doc(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n])
def info(path,triangles=None):
    value={'path':str(path.resolve()),'bytes':path.stat().st_size,
           'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    if triangles is not None:value['triangles']=triangles
    assert 0<value['bytes']<100_000_000
    return value
def preserve_metadata(target,source):
    before=target.read_bytes();size=struct.unpack_from('<I',before,12)[0]
    d=json.loads(before[20:20+size]);tail=before[20+size:]
    original=doc(source);d['asset']['copyright']=original['asset']['copyright']
    d['extras']=original.get('extras',{})
    raw=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
    result=struct.pack('<4sII',b'glTF',2,20+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4e4f534a)+raw+tail
    temporary=target.with_suffix('.tmp');temporary.write_bytes(result);os.replace(temporary,target)
    return {'fields':['asset.copyright','extras'],'binary_and_other_chunks_unchanged':True,
            'retained_tail_sha256':hashlib.sha256(tail).hexdigest()}
def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--lod-source',type=Path,required=True);p.add_argument('--native',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--gltfpack',default='/workspace/shanghai_tools/node_modules/.bin/gltfpack')
    a=p.parse_args()
    if a.out.exists():raise FileExistsError('Fresh package directory required')
    a.out.mkdir(parents=True)
    full=json.loads(a.raw.with_suffix('.geometry.json').read_text());input=json.loads((ROOT/'source/model-input.json').read_text())
    assets={'raw':info(a.raw,full['triangles']),'native':info(a.native)}
    flags=['-cc','-noq','-vtf','-vnf','-km','-ke']
    for role,source in [('web',a.raw),('lod',a.lod_source)]:
        target=a.out/(ID+'-'+role+'.glb');report=a.out/(role+'-gltfpack.json')
        subprocess.run([a.gltfpack,'-i',str(source),'-o',str(target),*flags,'-r',str(report)],check=True)
        preservation=preserve_metadata(target,source)
        (a.out/(role+'-provenance-preservation.json')).write_text(json.dumps(preservation,indent=2)+'\n')
        packed=json.loads(report.read_text());assets[role]=info(target,packed['render']['triangleCount'])
    result={'schema':'hudec-release-model-metadata-v1','id':ID,'name':'邬达克旧居',
       'anchor':input['anchor_wgs84'],'ground_base_m':0,'rotation_y':0,
       'height_estimate_m':full['bounds_glb']['max'][1],
       'height_note':'Model envelope14.083m includes estimated chimney tops. The2.30m door-height prior is an explicitly selected modelling estimate;2.15/2.45m spatial pressure cases are not measurement or confidence intervals.',
       'bounds_glb':full['bounds_glb'],'assets':assets,'all_four_asset_bytes':sum(x['bytes'] for x in assets.values()),
       'packing':flags,'web_geometry_policy':'Same full geometry, no position quantization or simplification; exact decoded parity requires independent QA.',
       'lod_source':info(a.lod_source,json.loads(a.lod_source.with_suffix('.geometry.json').read_text())['triangles']),
       'lod_policy':'Separately authored from the same input: omit individual slate/brick relief, reduce curve sampling25→13 and brace samples13→5, simplify fine glazing subdivisions. Keep roof shape, gables, actual main openings/reveals, north porch, chimneys and3birds.',
       'expected_images':{'raw':3,'web':3,'lod':3},
       'architecture_style':'都铎复兴住宅，曲面坡屋顶、双南山墙、木构装饰、砖烟囱和北侧门廊。',
       'detail_note':'复原2017/2018照片所见修缮后外观，含可见窗洞、门廊、木撑和屋面细部。东北服务体按历史总平面拓扑近似定位，未见墙面刻意省略窗洞；非1930逐寸测绘复原。',
       'uncertainty':[
         'C scale uses a2.30m estimated door-height prior; ±0.15m are stress-test cases, not a confidence interval or surveyed dimension.',
         'The713.9m² source owner polygon is context only, not house walls or a target building area. Main/connector/service topology follows a low-resolution historical plan and restored photographs.',
         'Exact exterior bearing, wall dimensions, bay depths, hidden service joins and roof heights remain approximations. No relocation toward an unidentified neighboring aerial red roof was made.',
         'Modest south bay/gable differences are photo-informed hypotheses. Perspective can account for the apparent small peak-height difference; false-three/false-two text is not assigned to the two south gables.',
         'Current restoration era is based on2017-published and2018 photographs, not a2026 site survey or a literal1930 reconstruction. Northern service chimney follows documented restoration intent; unseen details are simplified.',
         'Unobserved service openings and interiors are deliberately omitted. The detached brick garden gate, garden, surrounding roads and neighboring buildings are not included in this authored building.',
         'Original generic material atlases are illustrative, not building scans or photo textures. Source-private photograph pixels are not embedded or distributed.',
         'This delivery is an exterior visual model. It does not certify walkable interiors, structural construction, exact stair collision or public access.'
       ],
       'asset_license':[
         {'id':'MIT','url':'https://opensource.org/license/mit/','attribution':'Original geometry, code and procedural material atlas images by agent','role':'authored_geometry_code_and_embedded_materials'},
         {'id':'ODbL-1.0','url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'©OpenStreetMap contributors / Overture Maps; source owner context','role':'source_location_context'},
         {'id':'CC-BY-SA-4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/','attribution':'Szalai.laci, Hudec_House.jpeg; unedited complete Commons1280 reference','role':'public_reference_photograph_not_texture'}
       ],'source_photos_register':str(ROOT/'photo-register.json'),
       'raw_native_reused_in_place':True,'appearance_review_passed':True,
       'appearance_review':'Root actually viewed preserved review-v2 southwest-full and west-facade-close plus final-review north-entry-full. Independent delta QA proves85,053 triangles unchanged and12 old dark-timber triangles replaced by48 new triangles (+36), with unchanged bounds. Final north image confirms the3spandrel panels and porch middle crossbeam.',
       'independent_asset_qa_pending':True,'browser_verified':False,'main_modified':False,'remote_modified':False}
    (a.out/'model-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'assets':assets,'all_four_asset_bytes':result['all_four_asset_bytes'],'metadata':str((a.out/'model-metadata.json').resolve())},indent=2))
if __name__=='__main__':main()
