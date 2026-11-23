"""Recover the photographed gallery plane from its repeated timber posts."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).parent
WIDTH, HEIGHT = 1080, 638
BAY = 1.65
DECK, HEAD = 3.04, 5.30
POSTS = [
    ((369, 412), (370, 311)),
    ((453, 415), (453, 316)),
    ((533, 418), (533, 321)),
    ((609, 421), (609, 326)),
    ((680, 424), (680, 330)),
    ((747, 427), (747, 334)),
    ((811, 430), (811, 337)),
    ((870, 433), (870, 340)),
]
def camera(p):
    x, distance, height, yaw, roll, focal, horizon = p[:7]
    co, si = np.cos(yaw), np.sin(yaw)
    eye = np.array([x, -distance, height])
    right, forward, up = np.array([co, -si, 0]), np.array([si, co, 0]), np.array([0,0,1])
    def row(v):return np.array([*v, -v @ eye])
    depth = row(forward)
    horizontal = focal*row(np.cos(roll)*right + np.sin(roll)*up)
    vertical = focal*row(np.sin(roll)*right - np.cos(roll)*up)
    return np.stack((WIDTH/2*depth+horizontal,horizon*depth+vertical,depth))

def project(mat, xyz):
    h = mat @ np.array([*xyz,1])
    return h[:2]/h[2]

def fit():
    train = [0,1,3,4,6,7]
    start = [-4.2, 15., 1.65, .46, 0., 800., 490., 5.18]
    tunnel_depth=7.1
    reveal=[((108,434),(137,457)),((251,437),(235,458)),((108,570),(137,540)),((251,565),(235,538))]
    def residual(p):
        mat=camera(p);out=[]
        for i in train:
            for z,pix in zip((DECK,p[7]),POSTS[i]):
                out.extend(project(mat,(BAY*i,0,z))-pix)
        inverse=np.linalg.inv(mat[:,[0,2,3]])
        for near,far in reveal:
            pt=inverse@[*near,1];x,z=pt[:2]/pt[2]
            out.extend(project(mat,(x,tunnel_depth,z))-far)
        out.extend([(p[5]-840)/140,(p[2]-1.68)/.35,(p[6]-465)/85])
        return out
    result=least_squares(residual,start,bounds=([-30,4,.7,0,-.045,450,280,4.65],[8,38,3.5,1.25,.045,1700,650,5.8]),max_nfev=10000)
    mat=camera(result.x)
    controls=[{'post':i+1,'used_in_fit':i in train,'pixel':list(pix),'z':z,'delta_px':float(np.linalg.norm(project(mat,(BAY*i,0,z))-pix))}for i in range(8)for z,pix in zip((DECK,result.x[7]),POSTS[i])]
    # Set zero on the two unobstructed foreground paving joints below the arcade.
    inv=np.linalg.inv(mat[:,[0,2,3]])
    pavement=[(367,563),(813,551)]
    feet=[inv@[*uv,1] for uv in pavement]
    offset=float(np.mean([v[1]/v[2] for v in feet]))
    mat[:,3]+=mat[:,2]*offset
    calibrated=result.x.copy();calibrated[2]-=offset;calibrated[7]-=offset
    for item in controls:item['z']-=offset
    return dict(photo='https://imagepphcloud.thepaper.cn/pph/image/149/275/318.jpg',frame=[WIDTH,HEIGHT],unit='m',datum='Equal-post spacing 1.65 m is a conditional scale, pending an original measured plan.',camera_model='Verticals corrected in source. Horizontal optical axis and floating principal-row horizon.',parameters=calibrated.tolist(),height_origin=dict(photo_pixels=pavement,subtracted_m=offset),projection=mat.tolist(),controls=controls,tunnel_depth_m=tunnel_depth,tunnel_front_and_back_image_pairs=reveal,scope='Image 318 front row and the full-depth passage. Four post readings held out.')
class GalleryPlane:
    def __init__(self):
        self.fit=json.loads((HERE/'gallery-station.json').read_bytes())
        self.matrix=np.asarray(self.fit['projection'])
        self.inverse=np.linalg.inv(self.matrix[:,[0,2,3]])
    def at(self,x,y):
        q=self.inverse @ np.array([x,y,1]);return q[:2]/q[2]
    def at_depth(self,px,py,depth):
        m=self.matrix
        transform=np.column_stack((m[:,0],m[:,2],m[:,3]+depth*m[:,1]))
        q=np.linalg.solve(transform,[px,py,1]);return q[:2]/q[2]
    def x(self,px,py):return float(self.at(px,py)[0])
    def z(self,px,py):return float(self.at(px,py)[1])
if __name__=='__main__':
    fit_data=fit()
    target=HERE/'gallery-station.json'
    target.write_text(json.dumps(fit_data,ensure_ascii=False,indent=2)+'\n')
    print(fit_data['parameters'])
    print([(r['post'],round(r['delta_px'],2)) for r in fit_data['controls'] if not r['used_in_fit']])
    plane=GalleryPlane()
    for px,py in [(40,559),(108,570),(247,563),(367,563),(870,551),(870,325),(370,294)]:print(px,py,plane.at(px,py))
