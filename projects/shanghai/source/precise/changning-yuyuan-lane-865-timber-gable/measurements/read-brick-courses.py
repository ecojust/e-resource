"""Read horizontal mortar levels in an unobstructed strip to the right of the red-brick portal."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
here=Path(__file__).absolute().parent
sys.path.insert(0,str(here.parent/'source'))
from projection import photo,DATA
def measure(source):
    assert hashlib.sha256(source.read_bytes()).hexdigest()==DATA['source_sha256']
    rgb=np.asarray(Image.open(source).convert('RGB'),float)
    zz=np.arange(.30,2.57,.002);xx=np.linspace(1.17,1.73,70);z,x=np.meshgrid(zz,xx,indexing='ij')
    uv=photo(np.column_stack([x.ravel(),np.zeros(x.size),z.ravel()])).T
    # Light grey mortar is substantially paler and less red than the surrounding bricks.
    signal=rgb[:,:,1]*.68+rgb[:,:,2]*.5-rgb[:,:,0]*.18
    rect=map_coordinates(signal,[uv[1],uv[0]],order=1).reshape(z.shape)
    score=np.median(rect,axis=1);score-=gaussian_filter1d(score,13)
    peaks,_=find_peaks(score,distance=18,prominence=2.1)
    actual=zz[peaks];spacing=np.diff(actual);typical=np.median(spacing[(spacing>.043)&(spacing<.086)])
    return dict(source_sha256=DATA['source_sha256'],x_range_m=[1.17,1.73],z_range_m=[float(zz[0]),float(zz[-1])],profile_step_m=.002,
                read_bed_centres_m=actual.tolist(),typical_pitch_m=float(typical),profile_strength=[round(float(v),3) for v in score[peaks]],
                limitations='可见样带以外按实测中位节距外推。横竖砖缝间距的局部变化并非逐砖测绘。')
if __name__=='__main__':
    m=measure(Path(sys.argv[1]));print(len(m['read_bed_centres_m']),m['typical_pitch_m'],np.round(m['read_bed_centres_m'],3))
    (here/'brick-courses.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
