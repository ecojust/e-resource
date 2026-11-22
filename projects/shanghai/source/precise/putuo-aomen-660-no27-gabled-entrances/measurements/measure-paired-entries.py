"""Read visible transom edges and door surrounds from the credited 500 by 375 street photograph."""
from hashlib import sha256
from pathlib import Path
import argparse,json
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.optimize import least_squares

def point(params,angle):
    cx,cy,rx,rz,slope=params
    theta=np.radians(angle)
    u=cx+rx*np.cos(theta)
    return np.array([u,cy-rz*np.sin(theta)+slope*(u-cx)])

def observe(gray,guide,angle,sign):
    theta=np.deg2rad(angle)
    guide_pt=point(guide,angle)
    unit=np.array([np.cos(theta),-np.sin(theta)])
    offsets=np.arange(-3.8,3.81,.10)
    coords=guide_pt[:,None]+unit[:,None]*offsets
    vals=map_coordinates(gray,coords[::-1],order=1)
    changes=np.gradient(vals,.10)*sign
    strength=np.convolve(changes,np.ones(9)/9,mode='same')
    idx=4+np.argmax(strength[4:-4]);pt=coords[:,idx]
    return dict(theta=angle,u=round(pt[0],3),v=round(pt[1],3),contrast=round(float(strength[idx]),3))

def measure(path):
    im=Image.open(path).convert('L');assert im.size==(500,375)
    g=gaussian_filter(np.asarray(im,dtype=float),.55)
    sides={'left':{'inside':[197.8,241,28.0,28.1,-.025],'outside':[198.8,241,40,39,-.025]},
           'right':{'inside':[333.1,237.8,29.8,29.4,-.036],'outside':[332.1,237.8,41.5,42,-.036]}}
    arches={}
    for side,guides in sides.items():
        arches[side]={}
        for key,guide in guides.items():
            # Training and held-out angles are disjoint; below the left fan long clothing conceals its spring.
            train=[10,28,46,64,82,100,118,136,154]
            tests=[19,37,55,73,91,109,127,145,163]
            vals=[observe(g,guide,float(a),1 if key=='inside' else -1) for a in train]
            def residual(m):
                cx,rx,rz=m; params=(cx,guide[1],rx,rz,guide[4])
                return [(point(params,r['theta'])-[r['u'],r['v']])@np.array([np.cos(np.radians(r['theta'])),-np.sin(np.radians(r['theta']))]) for r in vals]
            fit=least_squares(residual,(guide[0],guide[2],guide[3]),loss='soft_l1',f_scale=.9,
                              bounds=([guide[0]-2.6,guide[2]-2.5,guide[3]-2.5],[guide[0]+2.6,guide[2]+2.5,guide[3]+2.5]))
            params=[round(fit.x[0],4),guide[1],round(fit.x[1],4),round(fit.x[2],4),guide[4]]
            hold=[observe(g,guide,float(a),1 if key=='inside' else -1) for a in tests]
            arches[side][key]=dict(ellipse=params,train=vals,held_out=hold)
    return dict(image_size=[500,375],photo_sha256=sha256(path.read_bytes()).hexdigest(),url='https://4travel.jp/travelogue/10996441',photographer='中国の風景',visit='2015-03-12',photo_id='photo_link_37989109',public_photo_embedded=False,
            nominal_scale_m_per_px=.018,origin_pixel=[267,358],axes='x right, z up, negative y towards lane',arches=arches,
            doorways={'left':{'inner_jamb_px':[166.4,230.6],'top_v':[263,261],'floor_v':357.2,'seam_u':191.9,'jamb_outer_px':[154.2,242.4],'soldier_top_v':[253.1,250.9],'course_h_px':3.6},
                      'right':{'inner_jamb_px':[301.9,370.9],'top_v':[258.6,256.9],'floor_v':357.0,'closed_leaf_start':346.4,'open_leaf_edges':[304.8,310.0],'jamb_outer_px':[288.4,384.0],'soldier_top_v':[246.7,244.7],'course_h_px':3.55}},
            plaque={'corners':[[388.0,256.0],[400.0,255.3],[400.0,264.7],[387.9,265.5]],'numerals':'27'},
            limits='Only the right-hand house number is legible. The left opening and part of the left fan are occluded by hanging clothes. Visible lintel, crown and spring were measured without assigning covered ornament; all depths and materials are visual estimates.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('original',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    a.output.write_text(json.dumps(measure(a.original),ensure_ascii=False,indent=2)+'\n')
