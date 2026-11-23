"""Two 22 February 2020 street panoramas measure the numbered east facade.

Camera stations are in WGS84. Their printed pan/tilt optically approximate each
zero-parallax eye. We adjust these within the observed panorama alignment error.
The separate 2015 exposure is reserved for an independent check.
"""
from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parent
base=np.array([121.4533,31.2097]);meters=np.array([111320*np.cos(np.radians(base[1])),110875])
origin=np.array([-.984,-.852]);U=np.array([.01850,.99983]);U/=np.linalg.norm(U);out=np.array([U[1],-U[0]])
stations=[('south',322.4192980218,[121.4533895052,31.2095778213]),('east',260.7566707466,[121.4533820107,31.2097142544])]
def camera(i,delta):
    tag,a,geo=stations[i];az=np.radians(a);pitch=np.radians(14)
    eye=np.r_[(geo-base)*meters,2.32];eye=np.r_[(eye[:2]-origin)@U,-(eye[:2]-origin)@out,eye[2]]+delta[3:6]
    f=np.array([np.sin(az)*np.cos(pitch),np.cos(az)*np.cos(pitch),np.sin(pitch)])
    right=np.array([np.cos(az),-np.sin(az),0.]);down=np.cross(f,right)
    basis=np.eye(3);basis[:2,0]=U;basis[:2,1]=-out
    R=Rotation.from_rotvec(np.radians(delta[:3])).as_matrix()@np.array([right,down,f])@basis
    focal=360/np.tan(np.radians(41))
    return np.array([[focal,0,360],[0,focal,267],[0,0,1]])@np.c_[R,-R@eye],eye
features={
 'numbered arch crown':('gate',0,'door',(370,376),(306,341)),
 'threshold at doorway axis':('gate',0,'grade',(370,451),(309,470)),
 'south arch apex':('left',0,'arch',(290,253),(158,192)),
 'north arch apex':('right',0,'arch',(428,304),(535,195)),
 'south arched sash sill':('left',0,'sill2',(289,325),(149,279)),
 'north arched sash sill':('right',0,'sill2',(428,348),(532,282)),
 'wide upper casement lintel':('center',0,'head2',(370,280),(324,184)),
 'wide upper casement sill':('center',0,'sill2',(368,337),(322,281)),
 'third-floor central paired lights sill':('center',0,'sill3',(370,242),(322,127)),
 'south third-storey casement sill':('left',0,'sill3',(302,195),(180,132)),
 'south third-storey casement head':('left',0,'head3',(297,145),(182,72)),
 'south roof-end tangent':('endL',.82,'eave',(175,87),(116,49)),
 'north roof-end tangent':('endR',.06,'eave',(443,228),(607,23)),
 'north ground cornice tangent':('endR',.06,'cornice',(446,354),(631,296)),
 'south ground cornice tangent':('endL',.82,'cornice',(132,309),(49,279))}
names=['left','right','center','endL','endR','arch','sill2','head2','sill3','head3','eave','cornice']
guess=np.array([-4.05,4.65,.12,-7.20,6.56,6.03,3.93,6.23,7.77,9.93,10.79,3.65])
sigma=np.array([.34,.34,.4,.85,.74,.45,.35,.45,.48,.6,.76,.33])
def params(a):return dict(gate=0.,grade=0.,door=2.55,**dict(zip(names,a[:len(names)])))
def observe(vals,feat):
    u,d,z=feat[:3];return np.array([vals[u],d,vals[z],1])
def solve(x,raw=False):
    v=params(x);res=[];report=[]
    for i in range(2):
        cd=x[len(names)+6*i:len(names)+6*i+6];P,eye=camera(i,cd)
        group=[]
        for name,feat in features.items():
            pt=observe(v,feat);a=P@pt;uv=a[:2]/a[2];b=np.array(feat[3+i]);delta=uv-b
            res.extend(delta/(4.3 if 'tangent'in name else 2.2))
            group.append({'feature':name,'udz_m':pt[:3].round(4).tolist(),'observed':b.tolist(),'projected':uv.round(3).tolist(),'residual_px':float(np.linalg.norm(delta))})
        errors=np.array([g['residual_px']for g in group]);report.append({'station':stations[i][0],'station_wgs84':stations[i][2],'P':P.tolist(),'adjusted_eye_udz':eye.tolist(),'median_px':float(np.median(errors)),'p90_px':float(np.quantile(errors,.9)),'control_points':group})
        res.extend(cd/np.array([2.3,2.3,2.2,.75,.75,.44]))
    res.extend((x[:len(names)]-guess)/sigma)
    return report if raw else res
def main():
    fit=least_squares(solve,np.r_[guess,np.zeros(12)],loss='soft_l1',f_scale=2.2,max_nfev=1500)
    v=params(fit.x);r=solve(fit.x,True)
    doc={'register':'5D023','street_number':'364','source_panorama_ids':['09000300122002221452161555O','09000300122002221452176135O'],'observations_working_size':[720,534],'original_raster':[1200,890],'original_panorama':{'manual_heading_deg':[v[1]for v in stations],'pitch_deg':14,'horizontal_fov_deg':82},'basis':'u follows the street to the right when facing the main entrance, d inside, z above pavement','datum_wgs84':base.tolist(),'arch_origin_east_north_m':origin.tolist(),'along_unit_vector':U.tolist(),'scale':'Original station separation and two independent sight-lines; entrance crown held at 2.55 m. Endpoint tangencies and obscured trim have wider uncertainty.','dimensions_m':v,'stations':r}
    (ROOT/'street-facade-dimensions.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n');print({k:round(v,2)for k,v in v.items()});print([(s['median_px'],s['p90_px'],s['adjusted_eye_udz'])for s in r])
if __name__=='__main__':main()
