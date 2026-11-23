"""Check the exterior identified in the architectural drawings against both actual public map camera sizes."""
from model import *
from urllib.request import urlopen
from shapely.affinity import scale,translate
import gzip
m,scenes=make_scenes(Path(sys.argv[1]))
contract=ri(w/'final-placement-contract.json')
cam=runpy.run_path(str(project/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))
module=project/'src/candidate-overview-camera.js'
with urlopen('http://127.0.0.1:31277/src/candidate-overview-camera.js')as resp: assert resp.read()==module.read_bytes()
data=urlopen(frame['origin']+'feature-table.json.gz',timeout=30).read();assert sha(data)==next(v['sha256']for v in frame['source_hashes']if v['repository_path'].endswith('feature-table.json.gz'))
mn=math.radians(1)*6371008.8;me=mn*math.cos(math.radians(lat))
others=[]
for row in json.loads(gzip.decompress(data))['features']:
    poly=G.shape(row['geometry'])
    if row['localId']==2849 or poly.distance(Point(lon,lat))>.002:continue
    poly=scale(translate(poly,xoff=-lon,yoff=-lat),xfact=me,yfact=mn,origin=(0,0))
    if poly.distance(Point(0,0))<=150:others.append((row['localId'],poly,row['height']))

tests=[]
def target(name,origin,direction,materials,length=6,mandatory=False):
    tests.append((name,np.array(origin),np.array(direction),materials,length,mandatory))
# These reference lines locate the front surface shared by all three architectural exports.
target('东侧砖券外轮廓',[11.9,4.19,6.28],[-1,0,0],['Russet moulded brick','Dark red brick joints'],4,True)
target('东券南侧垂砖',[11.9,3.36,4.75],[-1,0,0],['Russet moulded brick'],4)
target('街边弧阶压顶',[11.02,4.87,4.0],[0,0,-1],['Light grey cast stone'],4)
target('东门上方卵石面',[12.1,4.01,7.0],[-1,0,0],['Washed grey pebbles'],4,True)
target('南花廊二层西窗玻璃',[-1.59,-9.8,4.83],[0,1,0],['Grey green glazing','Warm reflected pane'],3.5,True)
target('南花廊二层东窗玻璃',[1.67,-9.8,4.97],[0,1,0],['Grey green glazing','Warm reflected pane'],3.5)
target('南花廊三层玻璃',[1.37,-9.8,8.48],[0,1,0],['Grey green glazing','Warm reflected pane'],3.5,True)
target('南面露台压顶',[.035,-9.8,11.51],[0,1,0],['Light grey cast stone','Pale terrace stone','Weathered cement sill'],3.5,True)
target('南面东山墙灰卵石',[5.47,-8.32,11.56],[0,1,0],['Washed grey pebbles'],4)
target('南花廊两孔之间实墩',[0,-9.52,1.73],[0,1,0],['Washed grey pebbles'],4)
target('主屋脊',[.56,1.04,18.0],[0,0,-1],['Terracotta ridge roll'],5,True)
target('南面东山墙屋脊',[6.13,-4.23,16.0],[0,0,-1],['Terracotta ridge roll'],5)
target('西中烟囱石帽',[-3.44,-.88,17.8],[0,0,-1],['Stone chimney cap'],4)
target('东烟囱石帽',[9.07,-.66,16.1],[0,0,-1],['Stone chimney cap'],5)
steps=[(0,0),(.03,.02),(-.046,.05),(.09,-.05),(-.08,-.09),(.13,.12),(-.16,.13),(.23,-.11),(-.24,-.14),(.34,.03),(-.38,-.04)]
reference=[]
for name,origin,direction,mats,length,required in tests:
    flat=np.flatnonzero(direction==0)
    for a,b in steps:
        q=origin.copy();q[flat]+=[a,b]
        rr={k:s.ray(q,direction.copy(),length)for k,s in scenes.items()}
        if all(v and v['material'] in mats for v in rr.values()):break
    else:
        if required:raise AssertionError(('missing reference',name,rr))
        continue
    reference.append(dict(feature=name,required=required,from_local=q.tolist(),direction=direction.tolist(),**rr))
coords=[np.array(r['full']['point_enu_m']) for r in reference]
targets=[(r['feature'],*(q[:2]@axes),q[2])for r,q in zip(reference,coords)]
def evaluate(bearing,pitch,zoom):
    place={**contract,'overviewBearing':bearing,'overviewPitch':pitch,'overviewZoom':zoom}
    views=[];physical={role:[]for role in ['full','lod']}
    for name,ww,hh,pads in cam['VIEWS']:
        viewport=dict(width=ww,height=hh,insets=dict(zip(['left','right','top','bottom'],pads)))
        view=cam['evaluate'](place,viewport,name,others,lon,lat,me,mn,targets)
        views.append(view)
        eye=np.r_[np.array(view['camera_enu'][:2])@axes.T,view['camera_enu'][2]]
        for role,rows in physical.items():
            obs=[]
            for i,(r,q) in enumerate(zip(reference,coords)):
                toward=q-eye;dist=float(np.linalg.norm(toward));hit=scenes[role].ray(eye,toward.copy(),dist+.15)
                diff=None if not hit else hit['distance_m']-dist
                seen=bool(view['probes'][i]['clear'] and hit and abs(diff)<.11 and hit['material']==r[role]['material'])
                obs.append(dict(feature=r['feature'],point=q.tolist(),screen_visible=view['probes'][i]['clear'],expected_material=r[role]['material'],depth_error_m=diff,visible=seen,first_hit=hit))
            rows.append(dict(screen=name,eye_local=eye.tolist(),samples=obs))
    visible=set.intersection(*[{p['feature']for p in view['samples']if p['visible']}for rs in physical.values()for view in rs])
    required={r['feature']for r in reference if r['required']}
    rank=(len(visible&required),len(visible),-abs(bearing-305)-abs(pitch-32))
    return rank,dict(bearing=bearing,pitch=pitch,zoom=zoom,views=views,physical=physical,visible=sorted(visible),not_visible=[r['feature']for r in reference if r['feature']not in visible])
best=None;trials=[]
for bearing,pitch,zoom in [(305,32,19.6),(295,32,19.6),(315,28,19.75),(300,36,19.84),(305,40,19.95),(291,34,19.84),
                               (289,42,20),(310,28,20),(298,45,19.75),(303,27,19.9),(310,35,19.75),(319,36,19.9),
                               (296,41,20.05),(307,42,19.6),(284,34,19.75),(315,21,19.82)]:
    rank,rec=evaluate(bearing,pitch,zoom);trials.append(dict(bearing=bearing,pitch=pitch,zoom=zoom,rank=rank,missed=rec['not_visible']))
    if best is None or rank>best[0]:best=(rank,rec)
rank,rec=best
save(w/'selected-camera.json',rec);save(w/'camera-comparison.json',dict(module=sha(module.read_bytes()),surfaces=reference,trials=trials))
print(rank,rec['bearing'],rec['pitch'],rec['zoom'],rec['visible'],rec['not_visible'],flush=True)
assert rank[0]>=4 and rank[1]>=8
contract.update(overviewBearing=rec['bearing'],overviewPitch=rec['pitch'],overviewZoom=rec['zoom']);save(w/'final-placement-contract.json',contract)
save(w/'overview-sightlines.json',dict(id=model_id,contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),camera_module_sha256=sha(module.read_bytes()),cases={'delivered':rec['views']},retained_volumes=len(others),certified_features=rec['visible']))
save(w/'model-sightlines.json',dict(id=model_id,passed=True,contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),asset_manifest_sha256=sha((Path(sys.argv[1])/'manifest.json').read_bytes()),views=rec['physical'],certified_features=rec['visible'],not_visible=rec['not_visible']))
