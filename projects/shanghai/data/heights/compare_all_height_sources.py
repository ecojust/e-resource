"""Source agreement checks; none of these data are independent ground truth."""
from pathlib import Path
import argparse,json,csv,math,collections,time
import numpy as np
from shapely.geometry import shape
from building_height_sampler import CMABHeightMatcher
from raster_height_sampler import RasterHeightSampler
from sample_heights import GHSLHeightSampler
ROOT=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--neighborhoods',type=Path,default=ROOT.parent/'neighborhoods')
 ap.add_argument('--cmab',type=Path,default=ROOT/'cmab/shards')
 ap.add_argument('--cnbh',type=Path,default=ROOT/'alternatives/cnbh_2020_shanghai_core_dm.tif')
 ap.add_argument('--ghsl',type=Path,default=ROOT/'shanghai_ghsl_anbh_2018_3arcsec.tif')
 ap.add_argument('--output-dir',type=Path,default=ROOT/'rebuilt/comparison')
 args=ap.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
 NEIGHBORHOODS=args.neighborhoods
 manifest=json.loads((NEIGHBORHOODS/'manifest.json').read_text())
 cmab=CMABHeightMatcher(args.cmab);raster=RasterHeightSampler(cnbh_path=args.cnbh,ghsl_path=args.ghsl);ghsl=GHSLHeightSampler(args.ghsl)
 rows=[];coverage=[];start=time.time()
 def positive(v):
  try:v=float(v);return v if math.isfinite(v) and v>0 else None
  except (ValueError,TypeError):return None
 for district in manifest['samples']:
  fc=json.loads((NEIGHBORHOODS/district['file']).read_text());counts=collections.Counter();height_estimates=[]
  for f in fc['features']:
   p=f['properties'];g=shape(f['geometry']);match=cmab.sample_geometry(g);r=raster.sample_geometry(g)
   counts['cmab_matched' if match else 'cmab_rejected_or_missing']+=1
   if match:height_estimates.append(match['height_m'])
   counts[r['height_quality'] if r else 'raster_missing']+=1
   h=positive(p.get('height'));floors=positive(p.get('num_floors'))
   if h is None and floors is None:continue
   reference=h if h is not None else floors*3.2;pt=g.representative_point()
   c=r['height_m'] if r and r['height_quality']=='cnbh_estimate_10m' else None
   values={'cmab':match['height_m'] if match else None,'cnbh':c,'ghsl':ghsl.height_at(pt.x,pt.y)}
   row={'district_id':district['district_id'],'district_name':district['district_name'],'id':p.get('id'),'name':p.get('@name'),
     'reference_m':reference,'reference_kind':'reported_height' if h is not None else 'floors_times_3.2m',
     'num_floors':floors,'longitude':pt.x,'latitude':pt.y,'cmab_iou':match['height_match_iou'] if match else None}
   for key,v in values.items():row[key+'_m']=v;row[key+'_minus_reference_m']=None if v is None else v-reference
   rows.append(row)
  coverage.append({'district':district['district_name'],'features':len(fc['features']),**counts,
   'cmab_matched_height_range_m':[min(height_estimates),max(height_estimates)] if height_estimates else None})
  print(district['district_name'],dict(counts),flush=True)
 def stats(subset,key):
  valid=[r for r in subset if r[key+'_m'] is not None]
  result={'reference_records':len(subset),'paired_records':len(valid),'reported_height_records':sum(r['reference_kind']=='reported_height' for r in valid),'floor_estimate_records':sum(r['reference_kind']=='floors_times_3.2m' for r in valid)}
  if valid:
   a=np.array([r[key+'_minus_reference_m'] for r in valid]);b=abs(a)
   result.update(median_absolute_difference_m=round(float(np.median(b)),3),p90_absolute_difference_m=round(float(np.quantile(b,.9)),3),median_signed_difference_m=round(float(np.median(a)),3),mean_absolute_difference_m=round(float(b.mean()),3),reference_median_m=round(float(np.median([r['reference_m'] for r in valid])),3),estimate_median_m=round(float(np.median([r[key+'_m'] for r in valid])),3))
  return result
 report={'purpose':'Cross-source consistency check; NOT independent ground-truth accuracy validation','reference_definition':'Overture explicit height where present, otherwise num_floors * 3.2m (assumed, not surveyed)',
  'reference_records':len(rows),'explicit_height_records':sum(r['reference_kind']=='reported_height' for r in rows),
  'floor_estimate_records':sum(r['reference_kind']=='floors_times_3.2m' for r in rows),
  'sampling':{'cmab':'EPSG3857 rooftop overlap IoU>=0.60 and both coverage>=0.70; ambiguous conflicting heights rejected; no shifts/no nearest neighbor',
  'cnbh':'Positive 10m pixels whose centers are within footprint; median. Narrow footprints without centers use representative point. No neighboring-pixel fill.',
  'ghsl':'2018 net built-surface cell average at polygon representative point'},
  'all_neighborhood_coverage':coverage,'source_comparisons':{},'seconds':round(time.time()-start,3)}
 for key in ['cmab','cnbh','ghsl']:
  result={'overall':stats(rows,key),'by_reference_kind':{},'by_district':[],'by_reference_height_bin':[]}
  for kind in ['reported_height','floors_times_3.2m']:result['by_reference_kind'][kind]=stats([r for r in rows if r['reference_kind']==kind],key)
  for d in manifest['samples']:result['by_district'].append({'district':d['district_name'],**stats([r for r in rows if r['district_id']==d['district_id']],key)})
  for lo,hi,label in [(0,10,'0-10m'),(10,30,'10-30m'),(30,60,'30-60m'),(60,100,'60-100m'),(100,float('inf'),'100m+')]:
   result['by_reference_height_bin'].append({'bin':label,**stats([r for r in rows if lo<r['reference_m']<=hi],key)})
  report['source_comparisons'][key]=result
 (args.output_dir/'height_source_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 with (args.output_dir/'height_source_comparison.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps({k:v['overall'] for k,v in report['source_comparisons'].items()},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
