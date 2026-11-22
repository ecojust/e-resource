"""Compare four windows from a separate, credited photograph with the actual mesh.
The projection is calibrated on the threshold and long continuous belts only.
"""
import argparse
import hashlib
import json
import numpy as np
from pathlib import Path
from build_model import SASH
from xintai_brick_corner import STONE
from glb_surfaces import decode,hit
from xintai_brick_corner import openings

def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def check(mesh,observations):
    # Gao photograph 15, horizontal features outside the openings.
    # image v = a + b * Z + c * X. The photograph is close to frontal.
    controls=[[1.875,.0,315.5],[5.625,.0,315.2],[1.875,3.86,265.7],[5.625,3.86,265.0],
              [1.875,7.67,215.0],[5.625,7.67,214.1],[1.875,11.03,168.8],[5.625,11.03,167.6]]
    design=np.asarray([[1,z,x] for x,z,v in controls])
    params=np.linalg.lstsq(design,[v for x,z,v in controls],rcond=None)[0]
    t,n,_=decode(mesh);result=[]
    for i,row in zip((4,5,2,3),observations['right_wing_two_bays']):
        c,sill,h,spring,rise,th,red= openings()[i]
        def test(label,point,target):
            photo=float(params@[1,point[2],point[0]])
            result.append(dict(opening=row['position'],detail=label,mesh_hit=point,reprojection_y=round(photo,3),
                         photo_y=target,error_px=round(photo-target,3)))
        # From just behind the outer brickwork shoot up to the interior soffit.
        roof=hit(t,n,np.array([c,.08,spring-.10]),np.array([0.,0.,1.]))
        assert roof is not None
        test('crown of the arched opening',roof[1],row['arch_vertex_y'])
        # Shoot vertically along the front of the transverse rail from the
        # clear opening. The arch frame is higher; the mullion lies off this x.
        cross=hit(t,n,np.array([c+.18,.19,sill+.17]),np.array([0.,0.,1.]))
        assert cross and cross[0]==SASH,cross
        test('underside of transverse frame',cross[1],row['transom_y'])
        ledge=hit(t,n,np.array([c+.28,-.07,sill+.27]),np.array([0.,0.,-1.]))
        assert ledge and ledge[0]==STONE,ledge
        test('top of pale sill',ledge[1],row['sill_glass_to_stone_y'][1])
    errors=np.asarray([q['error_px']for q in result]);maximum=float(np.max(abs(errors)))
    assert maximum<5.5,(mesh,maximum)
    return dict(controls_xyz_to_v=controls,fit=params.tolist(),maximum_absolute_px=maximum,rms_px=float(np.sqrt((errors**2).mean())),checks=result)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--measurements',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('meshes',type=Path,nargs=3);args=p.parse_args();src=json.loads(args.measurements.read_bytes())
    r=dict(photo_sha256=src['photo_sha256'],photo_resolution=src['dimensions'],pixel_observations_sha256=sha(args.measurements),
           dated_publication='高参88，2015年4月19日起刊，图15的拍摄日期未标明。',
           source='https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480102vrg2.html',
           comparison='分别测试四窗的券顶、横档下缘和浅色窗台上面。八项校正点位于窗外的落水线、线脚及门槛高度。正照830用于建模，另一张图15的窗轮廓逐点独立读数。',
           roles={role:check(f,src)for role,f in zip(('raw','full','lod'),args.meshes)})
    args.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
