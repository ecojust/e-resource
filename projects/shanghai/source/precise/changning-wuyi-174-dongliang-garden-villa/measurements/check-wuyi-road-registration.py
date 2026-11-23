"""Fit on marked facade corners and report each of three held-out window corners separately."""
import argparse
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def normalise(xy):
    centre = xy.mean(axis=0)
    scale = np.sqrt(2.0) / np.linalg.norm(xy - centre, axis=1).mean()
    return np.array([[scale, 0, -centre[0]*scale], [0, scale, -centre[1]*scale], [0, 0, 1.]])


def project(matrix, xy):
    h = np.column_stack((xy, np.ones(len(xy)))) @ matrix.T
    return h[:, :2] / h[:, 2:3]


def fit(x, y):
    first, second = normalise(x), normalise(y)
    rows = []
    for (a,b),(u,v) in zip(project(first,x),project(second,y)):
        rows.extend(([-a,-b,-1,0,0,0,u*a,u*b,u],[0,0,0,-a,-b,-1,v*a,v*b,v]))
    _, _, vt = np.linalg.svd(rows, full_matrices=True)
    h = np.linalg.solve(second, vt[-1].reshape(3,3)) @ first
    return h / h[2,2]


def run():
    source = json.loads((HERE/'wuyi-road-gable-three-photographs.json').read_bytes())
    reference = source['reference']
    report = {}
    for target, photo in source['images'].items():
        if target == reference:
            continue
        marks = [row for row in source['landmarks'] if target in row['observed']]
        x, y = (np.array([row['observed'][key] for row in marks]) for key in (reference,target))
        control = np.array([row['role']=='fit' for row in marks])
        h = fit(x[control],y[control]); prediction = project(h,x)
        scale = np.divide(photo['native_upright'],photo['working_size'])
        differences = np.linalg.norm((prediction-y)*scale,axis=1)
        result = {}
        for label, mask in [('fit',control),('held_out',~control)]:
            result[label] = dict(count=int(mask.sum()),rms_native_pixels=float(np.sqrt(np.mean(differences[mask]**2))),
                                 measurements=[dict(feature=marks[i]['feature'],measured_upright_px=(y[i]*scale).tolist(),
                                                    predicted_upright_px=(prediction[i]*scale).tolist(),error_native_px=float(differences[i]))
                                               for i in np.flatnonzero(mask)])
        report[target] = dict(reference_to_target_working_pixels=h.tolist(),**result)
    return dict(reference=reference,method='Normalized projective fit to visible sash edges. Three independently marked corners are withheld from each fit.',views=report)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);args=p.parse_args()
    result=run()
    if args.output:args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for name,v in result['views'].items():print(name,v['fit']['count'],v['fit']['rms_native_pixels'],v['held_out']['count'],v['held_out']['rms_native_pixels'])
