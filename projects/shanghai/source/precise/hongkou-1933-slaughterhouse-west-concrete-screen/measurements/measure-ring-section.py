"""Rectify an exterior-facing cell in Han Lei's 2010 interior photograph and measure both ring boundaries."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares

CELL=np.array([[401.7,267.4],[708.6,280.8],[713.,605.],[404.8,601.3]])
CORNERS=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])


def homography(src,dst):
    m=[];rhs=[]
    for (x,y),(u,v)in zip(src,dst):
        m.extend([[x,y,1,0,0,0,-x*u,-y*u],[0,0,0,x,y,1,-x*v,-y*v]]);rhs.extend([u,v])
    return np.r_[np.linalg.solve(m,rhs),1].reshape(3,3)


def transform(h,p):
    a=np.asarray(p);q=np.concatenate([a,np.ones((*a.shape[:-1],1))],axis=-1)@h.T
    return q[...,:2]/q[...,2,None]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('photo',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    with Image.open(args.photo)as im:
        assert im.size==(1066,1600);image=np.asarray(im.convert('L'),dtype=float)
    h=homography(CORNERS,CELL);inv=np.linalg.inv(h)
    radii=np.arange(.25,.64,.0013);edges=[]
    for theta in np.arange(240)*2*np.pi/240:
        v=np.array([np.cos(theta),np.sin(theta)])
        xy=np.array([.499,.505])+radii[:,None]*v
        px=transform(h,xy)
        g=map_coordinates(image,[px[:,1],px[:,0]],order=1)
        for band,(lo,hi,sign) in enumerate(((.34,.48,-1),(.47,.60,1))):
            if band and min(abs(v))<.25:continue
            d=sign*(np.roll(g,-4)-np.roll(g,4))
            ids=np.flatnonzero((radii>=lo)&(radii<=hi)&(d>65))
            if len(ids):
                k=ids[np.argmax(d[ids])];edges.append([*xy[k],band])
    data=np.array(edges)
    def residuals(p,points):
        cx,cy,aspect,inner,outer=p
        return np.sqrt(((points[:,0]-cx)*aspect)**2+(points[:,1]-cy)**2)-np.where(points[:,2]==0,inner,outer)
    first=least_squares(residuals,[.50,.50,.94,.39,.50],args=(data,),loss='soft_l1',f_scale=.0035)
    kept=data[abs(residuals(first.x,data))<.017]
    fit=least_squares(residuals,first.x,args=(kept,),loss='soft_l1',f_scale=.0028)
    cx,cy,aspect,ri,ro=fit.x
    # The next complete joint below the same side cell supplies the pitch.
    traces=[262.5,407.5,453.5,599.5,646.5,795.5,837.5]
    ordinates=transform(inv,[[265,y]for y in traces])[:,1]
    pt=ordinates[4]-ordinates[0]
    m=dict(pitch_cell_heights=pt,inner_diameter=2*ri/pt,outer_diameter=2*ro/pt,radial_band=(ro-ri)/pt,clear_central_cell_width=aspect/pt,clear_central_cell_height=1/pt,middle_horizontal_bar=(ordinates[2]-ordinates[1])/pt,ordinary_horizontal_bar=(ordinates[4]-ordinates[3])/pt,side_half_pitch=(ordinates[2]-ordinates[0])/pt)
    result=dict(source='https://commons.wikimedia.org/wiki/File:1933_-_panoramio.jpg',capture_date='2010-12-23',photographer='Han Lei',source_original_sha256='945a29259d3a3370136ee376e0a8d2ca8167c6c6c6dc45a9153378f6113b9a73',analysis_sha256=hashlib.sha256(args.photo.read_bytes()).hexdigest(),basis='Dimensions as fractions of repeating vertical pitch. Absolute metre scale is independently constrained by the street stations. The exact location of this interior photograph among the 16 similar leaves is unknown.',clear_frame_quadrilateral_px=CELL.tolist(),joint_trace_x_px=265,joint_trace_y_px=traces,raw_radial_edge_count=len(data),inlier_edge_count=len(kept),rms_pitch_units=float(np.sqrt(np.mean(residuals(fit.x,kept)**2))/pt),ratio=m,unit_to_original_homography=h.tolist(),inlier_edge_original_px=np.round(transform(h,kept[:,:2]),2).tolist(),inlier_boundary=['outer' if k else 'inner' for k in kept[:,2]])
    assert .675<m['inner_diameter']<.73 and .87<m['outer_diameter']<.94 and len(kept)>250
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(len(kept),m,result['rms_pitch_units'])
