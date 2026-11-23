"""Cast original photograph pixels into the actual GLB; the panorama uses its local planar registration."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Dark window lights are held out of the four-plane datum and first two upper corner correspondences.
# Moss, cropped light and the screened first ground floor are not used to score light visibility.
SAMPLES={
'one-pano':[
('top 1 left pane',894,224,'glass'),('top 2 left pane',928,221,'glass'),
('top 3 left pane',963,218,'glass'),('top 4 left pane',1000,215,'glass'),
('top 5 left pane',1040,213,'glass'),('top 6 left pane',1077,212,'glass'),
('middle 1 left pane',894,254,'glass'),('middle 2 left pane',928,253,'glass'),
('middle 3 left pane',965,252,'glass'),('middle 4 left pane',1001,249,'glass'),
('middle 5 left pane',1041,248,'glass'),('middle 6 left pane',1078,247,'glass'),
('lower 3 left pane',965,290,'glass'),('lower 4 left pane',1001,289,'glass'),
('lower 5 left pane',1042,288,'glass'),('lower 6 left pane',1079,286,'glass'),
('wall between windows 3 and 4',988,249,'wall'),('south downpipe',1024,251,'pipe'),
('north downpipe',949,239,'pipe')],
'one-front':[
('middle 1 right pane',1400,618,'glass'),('middle 2 left pane',1452,610,'glass'),
('middle 2 right pane',1470,607,'glass'),('low 2 through foliage',1460,665,'glass'),
('between second upper and middle sill',1456,575,'wall'),
('between first and second middle window',1423,607,'wall')]}
# Points are in the independently measured dark openings of the 1200 x 451 lawn image.
# Place samples within the left or right light, away from the shared central muntin.
THIRD=json.loads((HERE/'historic-lawn-window-readings.json').read_bytes())
third_points=[]
for floor,rows in THIRD['return_window_edges'].items():
    for row in rows:
        corners=row['corners']
        if any(x is None for x in corners):
            continue
        xy=np.asarray(corners,dtype=float)
        left=xy[0]*.42+xy[3]*.58;right=xy[1]*.42+xy[2]*.58
        uv=left*.71+right*.29
        third_points.append((floor+' '+str(row['axis'])+' left light',*uv,'glass'))
SAMPLES['historic-lawn']=third_points

def actual_hits(mesh):
    s=runpy.run_path(str(HELPER))['SerialScene'](mesh)
    fitted=json.loads((HERE/'lawn-return-stations.json').read_bytes())['stations']
    out={}
    for key,items in SAMPLES.items():
        station=fitted[{'one-pano':'ctny-panorama','one-front':'ctny-front'}.get(key,key)]
        eye=np.array(station['C']);inverse=np.array(station['R']).T@np.linalg.inv(station['K'])
        tests=[]
        for name,u,v,expect in items:
            def hit(dx,dy):
                direction=inverse@[u+dx,v+dy,1.]
                return s.ray(eye,direction/np.linalg.norm(direction),400.)
            def same(r):
                if not r:return False
                return r['material'] in {'glass':['casement glass','Lambuth | return window glazing'],'wall':['court ashlar','Lambuth | garden stone finish'],'pipe':['dark casement','dark lead']}[expect]
            first=hit(0,0);nearest=None
            for x,y in sorted(((x,y)for x in range(-5,6)for y in range(-5,6)if x*x+y*y<=25),key=lambda pair:pair[0]**2+pair[1]**2):
                if same(first if x==0 and y==0 else hit(x,y)):nearest=[x,y];break
            tests.append(dict(label=name,source_pixel=[u,v],expect=expect,direct=same(first),first=first,nearest_in_5_native_px=nearest))
        out[key]=dict(checked=len(tests),direct=sum(r['direct']for r in tests),within_5=sum(r['nearest_in_5_native_px'] is not None for r in tests),observations=tests)
    return dict(mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),scope='Restricted to measured southeast return-wall plane; oblique depth departures use optical centre estimates from the old frontage, not a whole-building surveyed camera.',stations=out)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('out',type=Path)
    args=parser.parse_args();report=actual_hits(args.mesh);args.out.write_text(json.dumps(report,indent=2)+'\n')
    print({k:(v['direct'],v['within_5'],v['checked'])for k,v in report['stations'].items()})
