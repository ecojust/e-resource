#!/usr/bin/env python3
"""Read metadata and exercise question transformations, not mesh/contact queries."""
from pathlib import Path
import ast,copy,inspect,json,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import rebind_requests as r
import run_area_seating_v3 as area

results=[]
def ok(name,condition):
 assert condition,name
 results.append({'control':name,'observed_expected':True})
def reject(name,call):
 try:call()
 except (ValueError,KeyError,FileNotFoundError):results.append({'control':name,'observed_expected':True,'expected':'reject'})
 else:raise AssertionError(name)

original=[r.read(r.OLD/(name+'.requests.json'))for name in r.GROUPS]
proof=r.read(r.V11/'independent-museum-review/checker-v2/run-geometry-v2/actual-raw-structure.json')
groups,mapping=r.transform(original,proof['part_results'])
ok('metadata-only explicit6102 to6114 accounting',len(mapping)==6102 and sum(map(len,groups))==6114)
ok('exact group counts',list(map(len,groups))==[50,5114,11,568,364,7])
ok('all5114 original pane ids and left selectors preserved',[(q['id'],q['left_selectors'])for q in original[1]['checks']]==[(q['id'],q['left_selectors'])for q in groups[1]])
changed=[(a,b)for a,b in zip(original[1]['checks'],groups[1])if a!=b]
ok('exactly seven pane support replacements',len(changed)==7 and all(a['left_selectors']==b['left_selectors']for a,b in changed))
ok('entire50 slot and364 louvre questions byte-equivalent',groups[0]==original[0]['checks'] and groups[4]==original[4]['checks'])
ok('all48 old panel sample selections preserved',groups[2][2:]==original[2]['checks'][1:])
ok('five split questions mapped and all other original ids accounted',sum(len(x['new_ids'])==2 for x in mapping)==5 and len({x['original_id']for x in mapping})==6102)
ok('new support chains exact seven local pairs',len(groups[-1])==7 and all(q['contact_mode']=='positive_volume' and q['minimum_embed_m']==1e-6 for q in groups[-1]))
bad=copy.deepcopy(original);bad[0]['checks'].pop();reject('missing original question',lambda:r.transform(bad,proof['part_results']))
reject('missing current part metadata',lambda:r.transform(original,proof['part_results'][:-1]))
badparts=copy.deepcopy(proof['part_results']);badparts[-1]['label']=badparts[0]['label'];reject('duplicate current semantic label',lambda:r.transform(original,badparts))
reject('absent preservation report cannot prepare ready questions',lambda:r.validate_context(r.V11/'auto-museum/run-geometry-v2/raw/jiading-shanghai-auto-museum-raw.glb',r.V11/'independent-museum-review/checker-v2/run-geometry-v2/actual-raw-structure.json',HERE/'nonexistent-proof.json'))
old=r.V11/'independent-museum-review/checker-v2/audit_pane_area_seating_v2.py'
ok('area mathematics imported directly from original frozen module',Path(inspect.getfile(area.pair_seat)).resolve()==old and Path(inspect.getfile(area.SmallFacetCache)).resolve()==old)
def loop_tree(p):
 tree=ast.parse(p.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
 return ast.dump(next(n for n in main.body if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='question'),include_attributes=False)
ok('actual5114 area evaluation loop exact original AST',loop_tree(old)==loop_tree(HERE/'run_area_seating_v3.py'))
ok('area constants retain all original values',area.MINIMUM_CELL_AREA_M2==1e-5 and area.MINIMUM_EMBED_M==1e-6 and area.MINIMUM_END_EXTENSION_M==1e-6 and area.MINIMUM_FACING_VERTICAL_COSINE==.5 and area.MAXIMUM_OPPOSITE_PLANE_SEPARATION_M==1e-9 and area.MAXIMUM_ENDPOINT_ARITHMETIC_ERROR_M==1e-7 and area.MAXIMUM_CELLS_PER_PAIR==20000)
report={'schema':'museum-v2-request-area-adaptation-controls-v1','preparation_controls_passed':True,'controls':results,'control_count':len(results),
 'actual_structure_metadata_only':r.desc(r.V11/'independent-museum-review/checker-v2/run-geometry-v2/actual-raw-structure.json'),
 'actual_mesh_or_area_queries_executed':False,'ready_requests_created':False,'model_accepted':False,'native_accepted':False,'browser_accepted':False}
with(HERE/'preparation-control-results.json').open('x')as stream:stream.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({'preparation_controls':len(results),'passed':True,'actual_model_checks':False}))
