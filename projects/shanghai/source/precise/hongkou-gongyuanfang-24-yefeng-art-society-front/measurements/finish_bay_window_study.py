"""Bind the three released meshes, forward first intersections and registered detail plate."""
from pathlib import Path
from hashlib import sha256
import argparse,json,subprocess,sys

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    for k in ['raw','full','lod','destination']:parser.add_argument(k,type=Path)
    args=parser.parse_args();m=Path(__file__).resolve().parent
    a=args.destination;a.mkdir(parents=True,exist_ok=True)
    results={}
    for key in ('raw','full','lod'):
        mesh=getattr(args,key);f=a/f'whole-{key}.json'
        subprocess.run([sys.executable,m/'check_bay_windows.py',mesh,f],check=True)
        report=json.loads(f.read_bytes());assert report['passed'] and report['count']==108
        results[key]=dict(mesh_sha256=digest(mesh),report_sha256=digest(f),count=report['count'],matched=report['matched'],occluded=[r['uv'] for r in report['rows'] if r.get('occluding_window')])
        press=a/f'complete-sills-{key}.json'
        subprocess.run([sys.executable,m/'check_lower_sills.py',mesh,press],check=True)
        secondary=json.loads(press.read_bytes())
        assert secondary['count']==21
        # The independent published camera has appreciable horizontal uncertainty on the far pane.
        # Keep every direct image point and its actual intersection in the release.
        rails=[r for r in secondary['rows'] if r['feature'].startswith('bottom timber')]
        assert len(rails)==15 and all(r['passed'] for r in rails)
        results[key]['published_2022']=dict(
            report_sha256=digest(press),count=secondary['count'],matched=secondary['matched'],
            first_surface_exceptions=[r for r in secondary['rows'] if not r['passed']])
    plate=a/'registered-bay-windows.jpg';drawing=a/'registered-render.json'
    subprocess.run([sys.executable,m/'render_bay_windows.py',args.full,args.lod,plate,drawing],check=True)
    sources={key:digest(m/key)for key in ['bay-window-source-pixels.json','two-cameras-and-curved-sill.json','bay-window-two-view-controls.json','press-entrance-camera.json','check_bay_windows.py','check_lower_sills.py','render_bay_windows.py']}
    sources['source/bay_windows.py']=digest(m.parent/'source/bay_windows.py')
    out=dict(variants=results,source_sha256=sources,plate_sha256=digest(plate),render_sha256=digest(drawing),method='First intersection of unfiltered released geometry. Twelve direct readings on the photograph and 96 samples on projected members. The open middle leaf covers two samples of the right frame in this camera. The separately published 2022 view contains all three bottom rails and the continuous sill. Its six direct pane readings and 15 modeled rail samples are retained, including any horizontal registration residuals.')
    f=a/'window-review.json';f.write_text(json.dumps(out,indent=1)+'\n');print(digest(f))
if __name__=='__main__':main()
