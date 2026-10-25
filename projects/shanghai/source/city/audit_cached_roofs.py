from pathlib import Path
import json,gzip,hashlib,collections,math,time
import argparse
parser=argparse.ArgumentParser(description='Audit roof attributes across the complete frozen raw archive.')
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[2]);parser.add_argument('--output',type=Path)
args=parser.parse_args();ROOT=args.project.resolve();OUT=args.output or ROOT/'data/roofs';OUT.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'data/fullcity-raw/manifest.json').read_text())
keys=['roof_shape','roof_height','roof_direction','roof_orientation','roof_material','roof_color','facade_material','facade_color','height','num_floors']
counts=collections.Counter();values={k:collections.Counter() for k in keys};districts={};candidates=[];seen=set();duplicates=[];n=0;renderable=0
start=time.monotonic()
def number(v):
 try:return None if isinstance(v,bool) or v is None else float(v)
 except (ValueError,TypeError):return None
def row():return {'total':0,'renderable':0,'fields':collections.Counter(),'nonflat_shape':0,'nonflat_with_positive_roof_height':0,'nonflat_with_roof_height_and_total_height':0,'nonflat_with_roof_height_and_direction_or_orientation':0,'shapes':collections.Counter()}
for tile in sorted((ROOT/'data/fullcity-raw/tiles').rglob('*.geojson.gz')):
 doc=json.loads(gzip.decompress(tile.read_bytes()))
 for feature in doc['features']:
  p=feature['properties'];ident=f"{p['source_layer']}:{p['id']}"
  if ident in seen:duplicates.append(ident)
  seen.add(ident);n+=1;renderable+=bool(p.get('renderable'))
  d=districts.setdefault(str(p['district_id']),row());d['name']=p['district_name'];d['total']+=1;d['renderable']+=bool(p.get('renderable'))
  for key in keys:
   value=p.get(key)
   if value is not None and value!='':counts[key]+=1;d['fields'][key]+=1;values[key][json.dumps(value,ensure_ascii=False,sort_keys=True)]+=1
  shape=p.get('roof_shape');rh=number(p.get('roof_height'));height=number(p.get('height'));orientation=p.get('roof_orientation');direction=number(p.get('roof_direction'))
  if shape:d['shapes'][str(shape)]+=1
  if shape and shape not in ('flat','unknown'):
   d['nonflat_shape']+=1
   if rh is not None and math.isfinite(rh) and rh>0:
    d['nonflat_with_positive_roof_height']+=1
    if height is not None and math.isfinite(height) and height>rh:d['nonflat_with_roof_height_and_total_height']+=1
    if orientation or direction is not None:d['nonflat_with_roof_height_and_direction_or_orientation']+=1
   f=dict(feature);f['properties']={**p,'audit_source_tile':str(tile.relative_to(ROOT))};candidates.append(f)
 assert n<=manifest['feature_count']
assert n==manifest['feature_count'] and not duplicates
report={'source_release':manifest['release'],'source_manifest_sha256':hashlib.sha256((ROOT/'data/fullcity-raw/manifest.json').read_bytes()).hexdigest(),'complete_source_scan':True,'features_scanned':n,'renderable_features':renderable,'duplicates':len(duplicates),'districts':districts,'fields_present':counts,'field_values':{k:v.most_common(50) for k,v in values.items()},'nonflat_candidates':len(candidates),'nonflat_renderable_candidates':sum(bool(f['properties'].get('renderable')) for f in candidates),'elapsed_seconds':round(time.monotonic()-start,2),'scope_note':'Counts apply to the preserved Overture source snapshot before detailed landmark replacement. A schema field or roof label does not itself establish a fully measured LoD2/LoD3 model.'}
(OUT/'cached-roof-statistics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'cached-roof-candidates.geojson').write_text(json.dumps({'type':'FeatureCollection','features':candidates},ensure_ascii=False,separators=(',',':'))+'\n')
print(json.dumps({k:report[k] for k in ['features_scanned','fields_present','nonflat_candidates','nonflat_renderable_candidates','elapsed_seconds']},ensure_ascii=False,indent=2))
