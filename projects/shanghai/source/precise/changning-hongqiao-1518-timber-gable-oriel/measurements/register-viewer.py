"""Map the five public view buttons to the measured modelling cameras at the reference aspect ratio."""
from pathlib import Path
import hashlib,itertools,json
import numpy as np
here=Path(__file__).absolute().parent;src=here.parent;project=src.parents[2]
page=project/'hongqiao-1518-timber-gable-oriel.html'
camfile=src/'source/cameras.json';cams={r['name']:r for r in json.loads(camfile.read_bytes())}
def unit(v):return v/np.linalg.norm(v)
def gl(p):return np.array([p[0],p[2],-p[1]])
def frame(direction,span,aspect):
    right=unit(np.cross([0.,1.,0.],direction));up=np.cross(direction,right)
    initial=np.array([1,1/aspect,.08]);tan=np.tan(np.deg2rad(19))
    distance=max(np.dot(v,direction)+1.14*max(abs(np.dot(v,up)),abs(np.dot(v,right))/aspect)/tan
                for sides in itertools.product([-.5,.5],repeat=3) for v in [initial*np.array(sides)])
    factor=span/(2*distance*tan*aspect)
    return initial*factor
MAP={'oblique':'garden','front':'oriel','above':'tile','inscription':'relief','return':'bow'}
if __name__=='__main__':
    out={};records={}
    for key,name in MAP.items():
        r=cams[name];eye,target=gl(r['eye']),gl(r['target']);direction=unit(eye-target)
        aspect=r['width']/r['height'];box=frame(direction,r['width_m'],aspect)
        out[key]=dict(center=target.round(8).tolist(),size=box.round(8).tolist(),direction=direction.round(8).tolist())
        records[key]=dict(camera=name,span_m=r['width_m'],web=out[key])
    t=page.read_text();start=t.index("showCandidateAssetViewer('changning-")+len("showCandidateAssetViewer('changning-hongqiao-1518-timber-gable-oriel', ")
    end=t.index(');',start)
    page.write_text(t[:start]+json.dumps(out,ensure_ascii=False,indent=2)+t[end:])
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    (here/'viewer-camera-registration.json').write_text(json.dumps(dict(camera_sha256=sha(camfile),page_sha256=sha(page),reference_resolution=[620,520],views=records),ensure_ascii=False,indent=2)+'\n')
