"""Measure consecutive stair noses from the independent portrait looking up the same flight."""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image
import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter1d
HERE=Path(__file__).absolute().parent
SHA='d926fa07905fc6d8971974ac64d9ccf8f4f10561f616a51fcd5e560207c279ce'
SEEDS=[574,504,446,399,360,327,302,277,251,234,216,200,186,174,162,154]
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('original',type=Path);file=ap.parse_args().original
    assert hashlib.sha256(file.read_bytes()).hexdigest()==SHA
    with Image.open(file)as im:a=np.asarray(im.resize((450,600),Image.Resampling.LANCZOS),float)
    line=np.median(a[:,173:217,:]@[.24,.58,.18],axis=1)
    grad=gaussian_filter1d(line,.91,order=1)
    rows=[]
    for i,y in enumerate(SEEDS):
        yr=y+np.argmax(grad[y-5:y+6])-5
        rows.append(dict(index=i+1,working_y_px=int(yr),light_rise=float(grad[yr])))
    t=np.arange(len(rows));v=np.array([r['working_y_px']for r in rows])
    f=lambda q:(q[0]+q[1]*t)/(1+q[2]*t)
    fit=least_squares(lambda q:f(q)-v,[574,-9,.11],loss='soft_l1')
    res=f(fit.x)-v
    out=dict(photograph_sha256=SHA,working_size=[450,600],brightness_columns=[173,217],noses=rows,projective_row_fit=fit.x.tolist(),
             rms_working_px=np.sqrt(np.mean(res**2)),conditional_rise_m=.171,conditional_run_m=.240,
             interpretation='16道连续前缘可单独辨认。级高、进深与照片以外的上层平台范围为估计；上方仅留可见的过渡台。')
    assert len(rows)==16 and max(abs(res))<7
    (HERE/'stair-noses.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(v,np.sqrt(np.mean(res**2)))
