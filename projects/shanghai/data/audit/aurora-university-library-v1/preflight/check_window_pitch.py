"""Repeat the independent window-head scale fits for the two 2020 photographs."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
INPUT = PROJECT / 'source/precise/huangpu-aurora-university-library/reference-review.json'
BAYS = [-18.60,-15.17,-11.59,-8.20,-4.79,4.79,8.20,11.59,15.17,18.60]

def homography(points):
    grid = np.array([[column,1-floor,1.] for column in BAYS for floor in range(3)])
    target = np.asarray(points, dtype=float).reshape(-1, 2)
    def error(parameters):
        transform = np.r_[parameters,1.].reshape(3,3)
        homogeneous = grid @ transform.T
        return (homogeneous[:,:2] / homogeneous[:,2,None] - target).ravel()
    fitted = least_squares(error,[10,0,420,.5,-50,200,.006,.0001],loss='soft_l1',f_scale=1.1)
    return np.r_[fitted.x,1.].reshape(3,3),float(np.sqrt(np.mean(error(fitted.x)**2)))

def measure(points, center, normal_focal=None):
    matrix,rms = homography(points)
    x,z = matrix[:,0],matrix[:,1]
    horizontal = x[:2] - center*x[2]
    vertical = z[:2] - center*z[2]
    if normal_focal is None:
        normal_focal = np.sqrt(-(horizontal@vertical)/(x[2]*z[2]))
    height = np.linalg.norm([*vertical/normal_focal,z[2]]) / np.linalg.norm([*horizontal/normal_focal,x[2]])
    return rms,float(normal_focal),float(height)

if __name__ == "__main__":
    data = json.loads(INPUT.read_bytes())['floor_height_estimate']
    close = data['photo26_oblique']
    rms,focal,pitch = measure(close['points'], np.array([420.,226.8]))
    assert abs(pitch-close['storey_pitch_m']) < .00001
    assert abs(rms-close['rms_px']) < .00001
    distant = data['photo25_near_level']
    second = [measure(distant['points'],np.array([420.,315.]),f)[2] for f in distant['sampled_focal_range_px']]
    assert np.allclose(second,distant['storey_pitch_range_m'],atol=.00001)
    print(json.dumps({'oblique_pitch_m':pitch,'oblique_rms_px':rms,'near_level_pitch_interval_m':sorted(second),'model_pitch_m':data['chosen_storey_pitch_m']},indent=2))
