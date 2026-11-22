"""Map Dai Zoujun's 780×437 courtyard image onto its red-brick wall."""
from pathlib import Path
import json
import numpy as np
record=json.loads(Path(__file__).with_name('dai-court-camera.json').read_bytes())
K,R,eye=(np.asarray(record[k]) for k in ['K','R','eye'])
def cut(uv,y=11.33):
    ray=R.T@np.linalg.solve(K,[*uv,1])
    return eye+(y-eye[1])/ray[1]*ray
def project(p):
    v=K@R@(np.array(p)-eye)
    return v[:2]/v[2]
