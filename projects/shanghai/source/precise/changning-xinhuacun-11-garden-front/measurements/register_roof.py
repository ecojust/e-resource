"""Measure named Xinhua Village roof 11 on two separately dated images and the original city table."""
from pathlib import Path
import hashlib, json, gzip, math, argparse
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from shapely.geometry import shape, Point
from shapely.ops import transform
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("placement",type=Path);p.add_argument("original_macro_table",type=Path);args=p.parse_args()
root=args.placement; original=args.original_macro_table
data=json.loads(gzip.decompress(original.read_bytes()))
osm=ET.parse(root/'osm.xml');station=[121.4192625,31.2211925]
sx=6378137*math.pi/180*math.cos(math.radians(station[1]));sy=6378137*math.pi/180
def metre(lon,lat):return ((lon-station[0])*sx,(lat-station[1])*sy)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
features={r['localId']:(r,transform(metre,shape(r['geometry'])))for r in data['features']}
named={}
for e in osm.findall('node'):
    tags={t.get('k'):t.get('v') for t in e.findall('tag')}
    if not tags.get('name','').startswith('长宁区政府'):continue
    ll=[float(e.get('lon')),float(e.get('lat'))];point=Point(metre(*ll)); candidates=sorted([(poly.distance(point),idx,poly.boundary.distance(point),poly.covers(point))for idx,(_,poly) in features.items()])
    named[tags['name']]={'source_url':'https://www.openstreetmap.org/node/'+e.get('id'),'version':int(e.get('version')),'osm_timestamp':e.get('timestamp'),'wgs84':ll,'original_source_nearest_two':[{'id':i,'distance_m':d,'distance_to_boundary_m':b,'point_inside':c}for d,i,b,c in candidates[:2]]}
aerial={}
measures={'8432':{'window_centres':[(153,212),(191,212),(228,210),(266,207)],'main_front_eaves':[(150,266),(311,260)],'side_to_side_roof':[(118,167),(309,158)]},'3692':{'window_centres':[(138,201),(176,198),(216,196),(251,195)],'main_front_eaves':[(122,214),(293,208)],'side_to_side_roof':[(99,168),(300,157)]}}
N=256*2**19
for year,m in measures.items():
    metadata=json.loads((root/f'release-{year}.json').read_bytes());left,top=metadata['crop_global_pixel_origin']; mpp=metadata['meters_per_pixel']
    def sheet_coord(ll):return ((ll[0]+180)/360*N-left,(1-math.asinh(math.tan(math.radians(ll[1])))/math.pi)/2*N-top)
    center=sheet_coord(station); x0,y0=int(center[0]-99),int(center[1]-83)
    im=Image.open(root/f'ortho-{year}.jpg')
    # Published picks were taken in the same resized 199x167 crop (image pixel centres).
    crop=im.crop((x0,y0,x0+199,y0+167)).resize((398,334))
    drawer=ImageDraw.Draw(crop)
    measure={}
    for name,points in m.items():
        pix=[[x0+(x+.5)/2-.5,y0+(y+.5)/2-.5] for x,y in points]
        lengths=[math.dist(i,j)*mpp for i,j in zip(pix,pix[1:])]
        theta=math.degrees(math.atan2(pix[-1][0]-pix[0][0],pix[0][1]-pix[-1][1]))%360
        measure[name]={'native_pixels':pix,'segment_lengths_m':lengths,'end_to_end_m':math.dist(pix[-1],pix[0])*mpp,'axis_bearing_deg_true':theta}
        drawer.line(points,fill='#ffce41',width=1)
        for x,y in points:drawer.ellipse((x-2,y-2,x+2,y+2),outline='#00ffff',width=1)
    crop.save(root/f'11-marked-{year}.jpg',quality=92)
    aerial[year]={'src_date':metadata['metadata'][0]['records'][0]['SRC_DATE'],'metres_per_native_pixel':mpp,'metadata_sha256':digest(root/f'release-{year}.json'),'observations':measure,'center_crop_in_sheet_pixels':[x0,y0,199,167]}
r,poly=features[1617]; ring=list(poly.exterior.coords)
report={'id':'Xinhua Village building 11, 1320 Yuyuan Road, Shanghai','source_named_sites':named,'views':aerial,'owner':{'macro':'14-13717-6695','local_id':1617,'key':r['key'],'full_shape':r['geometry'],'source_attribution':r['properties']['sources'],'ring_edge_lengths_m':[math.dist(a,b)for a,b in zip(ring,ring[1:])],'ring_edge_bearings_deg_true':[math.degrees(math.atan2(b[0]-a[0],b[1]-a[1]))%360 for a,b in zip(ring,ring[1:])],'height_estimated_m':r['height'],'production_feature_table_sha256':digest(original)},'source_images':{'front':{'url':'https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480101iqnm.html','author':'高参88','caption_identification':'11号楼，图14。相邻图15为12号、图16为14号。','observation':'Four similar dormers face the two-storey veranda. The two larger towers of No. 14 are absent.'},'osm_bbox':'https://api.openstreetmap.org/api/0.6/map?bbox=121.4179,31.2206,121.4199,31.22198'},'interpretation':'The individually named OSM point is interior to original building 1617. Separate 2019 and 2025 orthophotos show four small evenly spaced raised dormer roofs on its southern long slope. The preserved city roof outline is a simple rectangle, with roof-edge shifts between orthophotos. The images constrain bay spacing better than eave overhang. They do not constrain an absolute individual storey height or the geometry of the covered northern side. Use the photographic four-bay section as an independent exhibit unless a complete non-overlapping city reconstruction is verified.','uncertainty':'Dormer centre ±2 original pixels (about 0.5 m). Visually corresponding end eaves ±4–5 native px (about 1–1.3 m), with trees on both sides. True +X runs east roughly 86–89 degrees. Do not use the geocoded common gate address as the No. 11 survey point.'}
(root/'numbered-11-and-two-roofs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print({year:[round(ob['end_to_end_m'],2)for ob in release['observations'].values()]for year,release in aerial.items()})
