"""Estimate the courtyard elevation from two photographs taken at different distances.

Image coordinates refer to two downsampled review copies of the photographer's
2018 images. No photograph is distributed. The absolute scale depends on the
assumed height of one brick course. The French plaque and upper doorway supply
one plane; the lower doorway and outer faces of the balustrade supply two more.
"""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

OUT = Path(__file__).resolve().parent
SOURCES = [
    ('https://s8.sinaimg.cn/large/003216vszy7nKTdXGDR67',
     'df394070594d2a6988a240c435b37b2095f442582a00a1159ba95d6e175f9b8b', 1480,959,3963),
    ('https://s5.sinaimg.cn/large/003216vszy7nKTMGafGc4',
     '75e726b81fa0cd6efa50a7feead6d5f4024121e62b92c4a6e90f960002acdc59', 1342,1000,3978),
]
# Endpoints as seen from the courtyard. In each pair the first point is left.
MARKS = {
    'door spring': ([(662,442),(745,442)],[(659,437),(786,436)]),
    'door crown': ([(703,431)],[(723,419)]),
    'attic opening sill': ([(664,320),(742,320)],[(668,262),(784,262)]),
    'plaque crest': ([(703,194)],[(728,87)]),
    'plaque outside piers': ([(584,204),(822,205)],[(554,108),(900,108)]),
    'side bay upper lintels': ([(470,422),(932,422)],[(375,405),(1074,406)]),
    'lower door top': ([(655,603),(759,603)],[(633,676),(815,678)]),
    'lower door foot': ([(655,739),(760,739)],[(633,918),(815,919)]),
    'outside post crowns': ([(453,537),(953,536)],[(310,555),(1153,565)]),
    'inside post crowns': ([(619,538),(793,537)],[(577,560),(876,563)]),
    'inside post plinths': ([(619,596),(793,596)],[(577,653),(876,658)]),
}

PARAMETERS = ['arch spring height','arch crown height','attic sill height','attic opening half-width',
              'crest height','plaque pier half-width','plaque shoulder height','bay lintel half-span',
              'bay lintel height','basement door head','basement half-width','basement door depth',
              'outer post half-span','inner post half-span','post crown height','terrace height','outer rail depth']
START = [8.4,8.8,12.3,1.18,16.3,3.7,16.,7.3,9.,3.56,1.44,-3.1,6.9,2.35,5.,3.86,-3.4]


def pairs(w, y, z):
    return [(-w,y,z),(w,y,z)] if w else [(0.,y,z)]


def solve(course_height=.065):
    # The arch jambs are 38.91 courses apart. Metric output scales linearly
    # with the assumed course module; the two image series constrain the ratios.
    half_door = 38.91 * course_height / 2
    w, h, original = np.array([s[2:] for s in SOURCES]).T
    focal = 22/36 * 4032 * w/original
    def points(v):
        a,b,c,d,e,f,g,i,j,k,m,n,p,q,r,s,t = v
        return list(sum((pairs(*p) for p in [
            (half_door,0,a),(0,0,b),(d,0,c),(0,.05,e),(f,.05,g),(i,0,j),
            (m,n,k),(m,n,0),(p,t,r),(q,t,r),(q,t,s)
        ]),[]))
    def projection(v):
        xyz=np.array(points(v[:len(PARAMETERS)]))
        cams=v[len(PARAMETERS):].reshape((2,9))
        prediction=[]
        for cam,fi,wi,hi in zip(cams,focal,w,h):
            x,y,z,yaw,pitch,roll,principal_x,principal_y,relative_focal=cam
            # Unrotated camera right, up, forward are +X, +Z and +Y.
            local=Rotation.from_euler('xyz',[pitch,yaw,roll]).apply((xyz-[x,y,z])[:,[0,2,1]])
            q=local[:,:2]/local[:,2:3]
            prediction.append([wi/2+principal_x,hi/2+principal_y]+q*[fi*relative_focal,-fi*relative_focal])
        return np.array(prediction)
    measured=np.array([sum([list(pair[view]) for pair in MARKS.values()],[]) for view in range(2)])
    def residual(v):
        cams=v[len(PARAMETERS):].reshape((2,9))
        # Optical-centre priors allow the independently cropped frames to move.
        # Both pictures came from the same handset at an EXIF focal length of 3.81mm.
        priors=np.concatenate([cams[:,6]/45,cams[:,7]/85,(cams[:,8]-1)/.06,(cams[:,2]-1.6)/.30])
        return np.r_[((projection(v)-measured)/2.1).ravel(),priors]
    cameras=[0,-29,1.6,0,.12,0,0,0,1, 0,-17,1.6,0,.17,0,0,0,1]
    res=least_squares(residual,np.r_[START,cameras],x_scale='jac',max_nfev=1500,ftol=1e-11,gtol=1e-11,xtol=1e-11)
    error=projection(res.x)-measured
    return dict(assumed_course_m=course_height,estimated={name:round(float(number),4) for name,number in zip(PARAMETERS,res.x)},
                fitted_camera_parameters=res.x[len(PARAMETERS):].reshape((2,9)).round(5).tolist(),
                projected_rms_px=round(float(np.sqrt(np.mean(error**2))),3),largest_coordinate_residual_px=round(float(np.abs(error).max()),3),
                observed_xy=MARKS,projected_xy=projection(res.x).round(3).tolist(),sources=SOURCES,
                units='Metres on an assumed 65mm brick course; elevations and depths are approximate.',
                limitations='The two pictures are nearly frontal. Crop, lens correction, occulted thresholds and repeated architectural mouldings limit depth accuracy. Actual site orientation and surveyed metres require separate evidence.')


if __name__=='__main__':
    (OUT/'courtyard-camera-fit.json').write_text(json.dumps(solve(),ensure_ascii=False,indent=2)+'\n')
