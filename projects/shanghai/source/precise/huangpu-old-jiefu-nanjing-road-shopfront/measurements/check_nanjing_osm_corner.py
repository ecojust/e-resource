from pathlib import Path
import requests,json,hashlib,math
from shapely.geometry import Polygon,Point,LineString
R=Path(__file__).resolve().parent;q=json.loads((R/'north-front-site.json').read_bytes());w='https://api.openstreetmap.org/api/0.6/way/378107150/full.json'
res=requests.get(w,timeout=12);res.raise_for_status();d=res.json();way=next(o for o in d['elements']if o['type']=='way');nodes={o['id']:[o['lon'],o['lat']]for o in d['elements']if o['type']=='node'}
print(way['version'],way['tags'],flush=True);l,t=q['north_origin_lonlat'];cr=q['owner']['geometry']['coordinates'][0];a=6378137.;e=.00669437999014;rad=math.radians(t);n=a/(1-e*math.sin(rad)**2)**.5;m=n*(1-e)/(1-e*math.sin(rad)**2)
def en(p):return ((p[0]-l)*math.pi/180*n*math.cos(rad),(p[1]-t)*math.pi/180*m)
x,y=en(cr[3]);width=math.hypot(x,y);ux=-x/width;uy=-y/width
def loc(p):
 x,y=en(p);return [round(x*ux+y*uy,4),round(-x*uy+y*ux,4)]
coords=[{'node':i,'lonlat':nodes[i],'xy_m':loc(nodes[i])}for i in way['nodes']]
frozen=q['ring_xy_m'];g=[s['xy_m']for s in coords];p=Polygon(g);c=Polygon(frozen)
out={'url':w,'raw_response_sha256':hashlib.sha256(res.content).hexdigest(),'osm_version':way['version'],'name':way['tags'].get('name'),'frozen_macro_original':q['macro_sha256'],'local_axes':'First entry of each xy pair points westward along the frozen north straight, second inward. Origin is frozen ring vertex 2.','full_way_nodes_current':coords,'intersection_over_union_with_macro':p.intersection(c).area/p.union(c).area,'hausdorff_distance_m':p.hausdorff_distance(c),'meaning':'Unsimplified OSM footprint is a second plan source; node positions and plan offsets are not evidence for roof details.'}
(R/'original-osm-street-corner.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print([(x['node'],x['xy_m']) for x in coords],out['intersection_over_union_with_macro'],out['hausdorff_distance_m'])
