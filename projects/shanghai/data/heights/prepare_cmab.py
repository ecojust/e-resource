"""Create small spatial shards of licensed CMAB height estimates.

CMAB Figshare v2 is CC BY 4.0. Actual Shanghai v2 shapefiles are EPSG:3857,
with a Height field in metres. Rooftop geometry is retained without shifts.
Only rooftop representative points within supplied Shanghai boundaries remain.
"""
from pathlib import Path
import argparse,json,collections,time,zipfile
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyogrio,shapely
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

ROOT=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--raw',type=Path,default=ROOT/'.cache/height-sources/cmab/raw')
 ap.add_argument('--boundaries',type=Path,default=ROOT.parent/'districts.geojson')
 ap.add_argument('--output',type=Path,default=ROOT/'rebuilt/cmab/shards');ap.add_argument('--archive',type=Path,help='Optional CMAB Shanghai ZIP to extract into --raw before rebuilding');args=ap.parse_args()
 if args.archive:
  args.raw.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(args.archive) as archive:
   for member in archive.infolist():
    target=(args.raw/member.filename).resolve()
    if not target.is_relative_to(args.raw.resolve()):raise ValueError('Unsafe archive member')
   archive.extractall(args.raw)
 if not args.raw.exists():ap.error('CMAB raw directory is missing; supply --raw or --archive')
 args.output.mkdir(parents=True,exist_ok=True)
 features=json.loads(args.boundaries.read_text())['features']
 project=Transformer.from_crs(4326,3857,always_xy=True).transform
 districts=np.array([transform(project,shape(f['geometry'])) for f in features],dtype=object)
 tree=shapely.STRtree(districts)
 writers={};counts=collections.Counter();tile_counts=collections.Counter();inputs=[];start=time.time()
 shapefiles=sorted(args.raw.rglob('*.shp'))
 if not shapefiles:ap.error('No shapefiles found under --raw')
 schema=pa.schema([('geometry',pa.binary()),('height_m',pa.float32()),('source_id',pa.string()),('district_id',pa.string())])
 for path in shapefiles:
  info=pyogrio.read_info(path);assert info['crs']=='EPSG:3857'
  inputs.append({'file':path.name,'features':info['features'],'bounds':info['total_bounds']})
  with pyogrio.open_arrow(path,columns=['merged_id','Height'],use_pyarrow=True,batch_size=10000) as (meta,reader):
   for batch in reader:
    data=batch.to_pydict();heights=np.asarray(data['Height'],dtype=float)
    geoms=shapely.from_wkb(data['wkb_geometry']);centers=shapely.point_on_surface(geoms)
    pairs=tree.query(centers,predicate='within')
    chosen={int(row):int(district) for row,district in zip(*pairs)}
    tiles=collections.defaultdict(list)
    for idx,di in chosen.items():
     if not np.isfinite(heights[idx]) or heights[idx]<=0:continue
     c=centers[idx];key=f'{int(c.x//5000)}_{int(c.y//5000)}'
     tiles[key].append((idx,di));counts[features[di]['properties']['id']]+=1
    for key,indices in tiles.items():
     if key not in writers:writers[key]=pq.ParquetWriter(args.output/f'{key}.parquet',schema,compression='zstd',compression_level=9)
     table=pa.table({'geometry':[data['wkb_geometry'][i] for i,d in indices],
      'height_m':[heights[i] for i,d in indices],
      'source_id':[f'{path.stem}:{data["merged_id"][i]}' for i,d in indices],
      'district_id':[features[d]['properties']['id'] for i,d in indices]},schema=schema)
     writers[key].write_table(table);tile_counts[key]+=len(indices)
  print(path.name,'source',info['features'],'retained cumulative',sum(counts.values()),flush=True)
 for w in writers.values():w.close()
 report={'dataset':'CMAB Figshare 27992417 v2','license':'CC-BY-4.0','doi':'10.6084/m9.figshare.27992417.v2','input_crs':'EPSG:3857','output_crs':'EPSG:3857',
  'height_field':'Height','height_unit':'metre','height_kind':'Machine-learning prediction, not surveyed height',
  'geometry_kind':'Image-derived rooftops, not necessarily ground footprints','geometry_processing':'No shift, no simplification; representative point within Shanghai district polygons',
  'tile_size_projected_m':5000,'tile_assignment':'floor(rooftop representative point / 5000)','input_files':inputs,
  'source_features':sum(x['features'] for x in inputs),'retained_features':sum(counts.values()),
  'district_counts':[{'id':f['properties']['id'],'name':f['properties']['name'],'rooftops':counts[f['properties']['id']]} for f in features],
  'shards':[{'file':key+'.parquet','features':count,'bytes':(args.output/(key+'.parquet')).stat().st_size} for key,count in sorted(tile_counts.items())],
  'seconds':round(time.time()-start,2)}
 (args.output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps({'features':report['retained_features'],'shards':len(tile_counts),'bytes':sum(x['bytes'] for x in report['shards']),'seconds':report['seconds'],'districts':report['district_counts']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
