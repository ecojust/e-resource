"""Evaluate the real public directory camera, the visible original city and the physical material at each target."""
from model import *
from urllib.request import urlopen
import gzip
from shapely.affinity import scale,translate
m,scenes=make_scenes(Path(sys.argv[1]));contract=ri(w/'final-placement-contract.json');cam=runpy.run_path(str(project/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))
cameraModule=w/'signed-runtime-276/src/candidate-overview-camera.js'
cameraModule.parent.mkdir(parents=True,exist_ok=True)
cameraData=urlopen('http://127.0.0.1:31276/src/candidate-overview-camera.js',timeout=30).read()
assert sha(cameraData)=='73e4c91277cb4f07db11dda2ebfb78ccd5dcd11d2f266ff7eacd9ea201784845'
if cameraModule.is_file():assert cameraModule.read_bytes()==cameraData
else:cameraModule.write_bytes(cameraData)
cam['evaluate'].__globals__['PROJECT']=cameraModule.parents[1]
data=urlopen(frame['origin']+'feature-table.json.gz',timeout=30).read();assert sha(data)==next(v['sha256']for v in frame['source_hashes']if v['repository_path'].endswith('feature-table.json.gz'))
mn=math.radians(1)*6371008.8;me=mn*math.cos(math.radians(lat));meter=lambda p:scale(translate(p,xoff=-lon,yoff=-lat),xfact=me,yfact=mn,origin=(0,0))
neighbors=[]
for row in json.loads(gzip.decompress(data))['features']:
    poly=G.shape(row['geometry'])
    if poly.distance(Point(lon,lat))>.002:continue
    poly=meter(poly)
    if poly.distance(Point(0,0))<=150:neighbors.append((row['localId'],poly,row['height']))
source=scenes['full'];C=source.tri.mean(axis=1)
survey=[]
def point(label,material,xx,z,dz=.15,dx=.25):
    mids=np.where((source.mi==source.materials.index(material))&(np.abs(C[:,0]-xx)<dx)&(np.abs(C[:,2]-z)<dz)&(source.cross[:,1]<-.000001))[0]
    assert len(mids),(label,material,xx,z)
    near_front=C[mids,1].min();mids=mids[C[mids,1]<near_front+.08];chosen=mids[np.argmax(source.areas[mids])];x,y,z=C[chosen]
    survey.append((label,x,z,material.lower()))
for side,x in [('西柱',-1.835),('东柱',1.835)]:
    for z,letter in zip([3.11,2.49,1.88,1.23],'上海別墅'):
        point(side+letter,'Dark infill in name strokes',x,z,.25,.27)
    point(side+'柱座','Grey plinth stone',x,.32,.32,.6)
    point(side+'柱帽','Weathered capstone',x,3.79,.17,.7)
for lab,mat,low,high in [('112号墙面','Grey courtyard render',.3,1.85),('112上部木条','Brown horizontal screen',2.25,3.9),('112号字','Charcoal address numerals',.9,2.1),('东门扇','Dark iron door panels',.4,2.2)]:
    mask=np.where((source.mi==source.materials.index(mat))&(C[:,2]>low)&(C[:,2]<high)&(source.cross[:,1]<-.000001))[0]
    if lab=='东门扇':mask=mask[C[mask,0]>0]
    assert len(mask),lab
    chosen=mask[np.argmax(source.areas[mask])];p=C[chosen];survey.append((lab,p[0],p[2],mat.lower()))
reference=[];locpoints=[]
for name,x,z,material in survey:
    matching=[]
    for dx in [0,-.018,.018,-.044,.044,-.080,.080,-.14,.14]:
        for dz in [0,-.011,.011,-.022,.022,-.08,.08]:
            hits={role:scenes[role].ray([x+dx,-2,z+dz],[0,1,0],8)for role in ('full','lod')}
            if all(a and material in a['material'].lower() for a in hits.values()):matching.append(hits);break
        if matching:break
    if not matching:
        if name=='西柱门牌':continue
        raise AssertionError((name,x,z,material))
    hits=matching[0];reference.append(dict(feature=name,**hits));locpoints.append(np.array(hits['full']['point_enu_m']))
targets=[(row['feature'],*(q[:2]@axes),q[2])for row,q in zip(reference,locpoints)]
def evaluate(bearing,pitch,zoom):
    d={**contract,'overviewBearing':bearing,'overviewPitch':pitch,'overview_focus_bounds_glb':dict(min=[-5.41,.20,-.74],max=[2.22,3.82,.04])};physical={k:[]for k in ('full','lod')};views=[]
    for label,ww,hh,pads in cam['VIEWS']:
        view=cam['evaluate'](d,dict(width=ww,height=hh,insets=dict(zip(['left','right','top','bottom'],pads))),label,neighbors,lon,lat,me,mn,targets);views.append(view)
        eye=np.r_[np.array(view['camera_enu'][:2])@axes.T,view['camera_enu'][2]]
        for role in physical:
            rows=[]
            for i,(q,r)in enumerate(zip(locpoints,reference)):
                dvec=q-eye;dist=float(np.linalg.norm(dvec));a=scenes[role].ray(eye,dvec.copy(),dist+.1)
                err=a['distance_m']-dist if a else None
                ok=bool(view['probes'][i]['clear'] and a and abs(err)<.11 and a['material']==r[role]['material'])
                rows.append(dict(feature=r['feature'],point=q.tolist(),screen_visible=view['probes'][i]['clear'],expected_material=r[role]['material'],depth_error_m=err,visible=ok,first_hit=a))
            physical[role].append(dict(screen=label,eye_local=eye.tolist(),samples=rows))
    shown=set.intersection(*[{p['feature'] for p in vs['samples'] if p['visible']} for rows in physical.values() for vs in rows]);core=[side+v for side in ('西柱','东柱') for v in '上海別墅'];rank=(sum(k in shown for k in core),len(shown),-abs(340-bearing)-abs(66-pitch))
    return rank,dict(bearing=bearing,pitch=pitch,zoom=zoom,views=views,physical=physical,visible=sorted(shown),not_visible=[r['feature'] for r in reference if r['feature'] not in shown])
best=None;trials=[]
for bearing,pitch,zoom in [(341,70,20.6),(341,65,20.6),(341,59,20.6),(341,70,20.9),(341,73,20.9),(341,65,20.9),(337,73,20.7),(343,68,20.75),(342,70,21.1),(341,71,21.3),(341,64,21.1),(345,63,21.1),(333,60,21.1),(320,63,21.15),(353,63,21.15),(342,55,21.02)]:
    rank,v=evaluate(bearing,pitch,zoom);trials.append(dict(bearing=bearing,pitch=pitch,zoom=zoom,visible=len(v['visible']),not_visible=v['not_visible']))
    if best is None or rank>best[0]:best=(rank,v)
    if len(v['visible'])==len(reference):break
rank,row=best;save(w/'debug-camera.json',row);assert rank[0]==8 and rank[1]>=13,(rank,trials)
contract.update(overview_focus_bounds_glb=dict(min=[-5.41,.20,-.74],max=[2.22,3.82,.04]),overviewBearing=row['bearing'],overviewPitch=row['pitch'],overviewZoom=row['zoom']);save(w/'final-placement-contract.json',contract)
save(w/'selected-camera.json',row);save(w/'camera-comparison.json',dict(module=sha(cameraModule.read_bytes()),surfaces=reference,trials=trials));save(w/'overview-sightlines.json',dict(id=m['id'],contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),camera_module_sha256=sha(cameraModule.read_bytes()),cases={'delivered':row['views']},retained_volumes=len(neighbors),certified_features=row['visible']));save(w/'model-sightlines.json',dict(passed=True,id=m['id'],contract_sha256=sha((w/'final-placement-contract.json').read_bytes()),asset_manifest_sha256=sha((Path(sys.argv[1])/'manifest.json').read_bytes()),views=row['physical'],certified_features=row['visible'],not_visible=row['not_visible']));print('camera',rank,row['bearing'],row['pitch'],row['zoom'],len(reference),row['not_visible'])
