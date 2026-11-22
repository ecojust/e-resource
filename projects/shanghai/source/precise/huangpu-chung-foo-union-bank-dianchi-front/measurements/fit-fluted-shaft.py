"""Solve circular shaft silhouettes and the pitch registration of the four visible channels."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.optimize import least_squares

def solve(source,photo):
    sys.path.insert(0,str(source))
    from photo_plane import CAMERAS
    data=source.parent/'measurements'
    traced=json.loads((data/'ionic-front-traces.json').read_bytes())
    if hashlib.sha256(photo.read_bytes()).hexdigest()!=traced['photograph_sha256']:raise ValueError('Wrong street photograph')
    controls=json.loads((data/'north-photo-controls.json').read_bytes())
    reg=json.loads((data/'north-portico-axes.json').read_bytes())['axes']
    ref=reg[3]; photo_lum=gaussian_filter(np.asarray(Image.open(photo).convert('L'),float),.68)
    near=CAMERAS['close'];wide=CAMERAS['wide']
    period=2*np.pi/16
    samples=[]
    for v in np.arange(1178.,1339.,10.):
        l=1687.+.203*(v-1170.);r=1769.+.269*(v-1170.)
        line=[]
        for a in traced['scale']['observed_trough_angles_rad']:
            u=(l+r)/2+(r-l)/2*np.sin(a)
            uvs=u+np.arange(-2.0,2.01,.25)
            tone=map_coordinates(photo_lum,[np.full(len(uvs),v),uvs],order=1)
            line.append(float(uvs[np.argmin(tone+.42*(uvs-u)**2)]))
        samples.append((v,l,r,line))
    def us_at(angles,x,y,r,phase,view,v,z0,z1):
        plane=view[1]-v*view[2];z=(z0+z1)*.5
        theta=(angles-phase)/period
        frac=(theta+.5)%1.-.5
        cut=.073*np.sqrt(np.maximum(0.,1.-(frac/.4375)**2))
        for _ in range(4):
            t=(z-z0)/(z1-z0)
            radii=r*(1.+.085*(1.-t)+.021*np.sin(np.pi*t)-cut)
            xx=x+radii*np.cos(angles);yy=y+radii*np.sin(angles)
            z=-(plane[0]*xx+plane[1]*yy+plane[3])/plane[2]
        return (view[0,0]*xx+view[0,1]*yy+view[0,2]*z+view[0,3])/(view[2,0]*xx+view[2,1]*yy+view[2,2]*z+view[2,3])
    # Uniform angular mesh matches the spacing used by the mesh author; include
    # both channel centres and the narrow flat fillets when fitting the silhouette.
    full_angle=np.arange(16*50)*2*np.pi/(16*50)
    def project_shell(params,row,view,v):
        x,y,r,phase=params;z0,z1=[row['z_and_pixels'][k]['z_m'] for k in ['base','neck']]
        uv=us_at(full_angle+phase,x,y,r,phase,view,v,z0,z1)
        return [uv.min(),uv.max()]
    def projections(params,v):
        x,y,r,phase=params;z0,z1=[ref['z_and_pixels'][k]['z_m'] for k in ['base','neck']]
        angles=np.arange(-9,0)*period+phase
        return us_at(angles,x,y,r,phase,near,v,z0,z1)
    def residual(params,selection,ret=False):
        parts=[];allp=[]
        for j,(v,l,r,channels)in enumerate(selection):
            p=project_shell(params,ref,near,v)
            vals=projections(params,v)
            # The camera faces the front-left quadrant; the four consecutive
            # observed grooves proceed from the viewer-left outline inwards.
            seq=min((vals[k:k+4] for k in range(len(vals)-3)),key=lambda a: np.linalg.norm(a-channels))
            parts.extend((seq-channels)/2.4);parts.extend((np.array(p)-[l,r])/3.0)
            allp.append(dict(v_px=v,observed_edges_px=[l,r],projected_edges_px=np.round(p,2).tolist(),
                             observed_troughs_px=np.round(channels,2).tolist(),projected_troughs_px=seq.round(2).tolist()))
        wh=project_shell(params,ref,wide,900.)
        parts.extend((np.array(wh)-controls['wide_shaft_edges_u_at_v900'][3])/1.1)
        if ret:return allp,wh
        return parts
    anchors=np.array([c["x_m"]for c in reg]);radii=np.array([c["radius_m_by_view"].get("close",c["radius_m_by_view"]["wide"])for c in reg])
    datum_y=ref["y_m"]
    def planar(points):
        y=points[0];xs=points[1:7];rs=points[7:13];result=[(y-datum_y)/.16]
        for i,row in enumerate(reg):
            params=[xs[i],y,rs[i],.11]
            w=project_shell(params,row,wide,900.)
            result.extend((np.array(w)-controls["wide_shaft_edges_u_at_v900"][i])/1.1)
            n=controls["close_shaft_edges_u_at_v1240"][i]
            if n:
                result.extend((np.array(project_shell(params,row,near,1240.))-n)/2.4)
            result.extend([(xs[i]-anchors[i])/.13,(rs[i]-radii[i])/.04])
        return result
    basis=least_squares(planar,np.r_[datum_y,anchors,radii])
    common_y=float(basis.x[0])
    start=[ref['x_m'],common_y,ref['radius_m_by_view']['close']]
    def fit_one(p0):
        return least_squares(lambda a:residual(a,samples[::2]),[*start,p0],
                            bounds=([start[0]-.35,start[1]-.000001,.20,-period/2],[start[0]+.35,start[1]+.000001,.35,period/2]),max_nfev=120)
    fit=min((fit_one(seed) for seed in [-.15,-.05,.05,.15]),key=lambda f:f.cost)
    x,y,r,phase=fit.x
    output=[]
    for i,row in enumerate(reg):
        z0,z1=[row['z_and_pixels'][k]['z_m']for k in ['base','neck']]
        init=np.array([row['x_m'],common_y,row['radius_m_by_view'].get('close',row['radius_m_by_view']['wide'])])
        def sides(p):
            vals=[*p,phase]
            w=np.array(project_shell(vals,row,wide,900.))-controls['wide_shaft_edges_u_at_v900'][i]
            result=list(w/1.1)
            if controls['close_shaft_edges_u_at_v1240'][i]:
                n=np.array(project_shell(vals,row,near,1240.))-controls['close_shaft_edges_u_at_v1240'][i]
                result.extend(n/2.4)
            result.extend([(p[1]-row['y_m'])/.135,(p[0]-row['x_m'])/.10,(p[2]-init[2])/.045])
            return result
        if i==3:sol=fit.x[:3]
        else:sol=least_squares(sides,init,bounds=([init[0]-.35,init[1]-.000001,.16],[init[0]+.35,init[1]+.000001,.36])).x
        output.append(dict(index=i+1,original_shaft_xyr_m=[row['x_m'],row['y_m'],float(init[2])],shaft_xyr_m=sol.round(7).tolist(),
                           fitted_wide_silhouette_at_v900_px=np.round(project_shell([*sol,phase],row,wide,900),2).tolist(),
                           close_boundaries_measured=bool(controls['close_shaft_edges_u_at_v1240'][i])))
    observations,wide_out=residual(fit.x,samples[1::2],True)
    errors=np.array([np.array(s["projected_troughs_px"])-s["observed_troughs_px"] for s in observations])
    edge=np.array([np.array(s["projected_edges_px"])-s["observed_edges_px"] for s in observations])
    return dict(source_url=traced['source_page'],source_sha=traced['photograph_sha256'],axis_note="The round shaft uses both street views. The fourth shaft has 17 direct scans of four visible troughs. The hidden angular continuation uses a regular 16-fold pitch; groove depth is estimated.",common_shaft_axis_y_m=common_y,phase_rad=float(phase),columns=output,
                heldout_fourth_shaft=observations,holdout_trough_rms_px=float(np.sqrt(np.mean(errors**2))),holdout_contour_rms_px=float(np.sqrt(np.mean(edge**2))),
                wide_fourth_v900_edges_px=wide_out,wide_measured_v900=controls['wide_shaft_edges_u_at_v900'][3])
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--source',required=True,type=Path);a.add_argument('--photo',required=True,type=Path);a.add_argument('--output',required=True,type=Path);a=a.parse_args()
    rec=solve(a.source,a.photo);a.output.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
    print(rec['phase_rad'],rec['holdout_trough_rms_px'],rec['holdout_contour_rms_px'],rec['wide_fourth_v900_edges_px'],rec['columns'][3])
