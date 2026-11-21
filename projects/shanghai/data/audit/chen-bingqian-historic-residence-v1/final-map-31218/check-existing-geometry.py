"""Compare standing buildings around the neighborhood marker in the signed sites' near and far tile streams."""
import gzip, hashlib, json, math
from pathlib import Path
from urllib.request import urlopen
from shapely.geometry import shape, Point
from shapely.affinity import affine_transform

here=Path(__file__).resolve().parent
marker=[121.4525,31.2272]; unit=6378137*math.pi/180
sx=unit*math.cos(math.radians(marker[1])); sy=unit
macro='14-13719-6694'; origin=Point(0,0)
def digest(data):return hashlib.sha256(data).hexdigest()
def inspect(port):
    base=f'http://127.0.0.1:{port}/assets/city-detail/macros/{macro}/';files={};index={}
    def get(name):
        with urlopen(base+name,timeout=90) as response:
            assert response.status==200
            data=response.read()
        files[name]={'sha256':digest(data),'bytes':len(data)}
        if name in index:assert files[name]==index[name],name
        return data
    ready=json.loads(get('READY.json'));index=ready['published_files']
    features=json.loads(gzip.decompress(get(ready['feature_table_file'])))['features']
    nearest=[]
    for f in features:
        poly=shape(f['geometry'])
        local=affine_transform(poly,[sx,0,0,sy,-sx*marker[0],-sy*marker[1]])
        nearest.append((local.distance(origin),f['localId'],list(poly.representative_point().coords[0]),f))
    nearest.sort(key=lambda row:row[:2]);assert nearest[0][1]==1356 and 10<nearest[0][0]<15
    far=get(ready['far']['file']);assert digest(far)==ready['far']['sha256']
    rows=[];groups={}
    for dist,key,xy,f in nearest[:7]:
        g,=[g for g in ready['near'] if key in g['featureLocalIds']]
        if g['id'] not in groups:
            near=get(g['file']);assert digest(near)==g['sha256'] and digest(gzip.decompress(near))==g['decoded_sha256']
            groups[g['id']]={'members':g['featureLocalIds'],'file':g['file'],'decoded_sha256':g['decoded_sha256'],'triangles':g['triangles']}
        rows.append({'owner':key,'source_key':f['key'],'height_m':f['height'],'meters_from_rounded_marker_to_outline':round(dist,4),'ground_witness_wgs84':xy,'near_group':g['id']})
    return {'features_in_table':len(features),'nearby':rows,'groups':groups,'files':files,'far_triangles':ready['far']['triangles']}
before,after=(inspect(n) for n in (31217,31218))
assert before==after
proof={'passed':True,'ports':[31217,31218],'macro':macro,'rounded_register_point':marker,'point_is_outside_all_present_day_footprints':True,'same_content':after,'purpose':'陕西北路80号历史原址以街区坐标登记。取现有七栋各一处地面作为两期对照，保持园内现状建筑。'}
(here/'existing-city-geometry.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
print(len(after['nearby']),len(after['groups']),len(after['files']),after['nearby'][0])
