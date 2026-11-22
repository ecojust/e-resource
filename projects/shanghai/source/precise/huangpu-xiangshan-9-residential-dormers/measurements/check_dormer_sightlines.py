"""Test the observed glazing against first intersections from the two street cameras and the 2018 camera."""
import argparse,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from xiangshan_dormers import DATA,GLASS,SASH,BEAD,FRAME,ROD,PLASTER,EAVE
from xiangshan_photo_plane import CALIBRATION,pixel
def photograph_witnesses():
    # The mid-bay has two apertures, the small and large gables contain one and two.
    views={'eastern':['alignment-roof-0'],'western':['roof-15-west','2018_commons'],'link':['alignment-roof-0','2018_commons']}
    for name,cameras in views.items():
        section=DATA[name]
        for idx,(l,r,b,t) in enumerate(section['openings']):
            # The left leaf of the rightmost aperture stands open in the winter photograph.
            fractions=[.68,.84] if name=='western' and idx==1 else [.19,.34,.68,.84]
            for c in cameras:
                # The summer appliance masks the second connecting sash. Its actual
                # divided lights can be checked in winter from the western camera.
                if name=='link' and idx==1 and c=='2018_commons':
                    c='roof-15-west'
                for xf in fractions:
                    for zf in (.20,.5,.80):
                        target=[l+(r-l)*xf,section.get('front_y',0.)+.107,b+(t-b)*zf]
                        yield c,name,idx+1,pixel(target,c),target,xf,zf
def check(path):
    scene=SerialScene(path);rows=[]
    for cam,name,aperture,uv,aim,xf,zf in photograph_witnesses():
        P=np.asarray(CALIBRATION['camera_matrices'][cam]);eye=-np.linalg.solve(P[:,:3],P[:,3])
        direction=np.linalg.solve(P[:,:3],[*uv,1.]);direction/=np.linalg.norm(direction)
        hit=scene.ray(eye,direction,100.);material=hit['material']if hit else None
        point=hit['point_enu_m']if hit else None
        # A fine photographed glazing bar may be foremost at the sampled cell, but roof/sky/other walls are not glazing.
        expectation='casement'
        passed=bool(material in (GLASS,SASH,FRAME,BEAD) and np.linalg.norm(np.asarray(point)-aim)<.42)
        if name=='western' and zf==.20:
            # Both documented racks project across the lower lights when seen from the pavement.
            expectation='drying rack in front of the lower lights'
            passed=bool(material==ROD and -.32<point[1]<-.13 and abs(point[2]-9.50)<.055)
        if cam=='roof-15-west' and name=='link' and aperture==2 and xf>=.68 and zf==.80:
            # The 2015 oblique photograph shows the right-hand upper lights
            # behind the edge of the larger foreground gable's extended eave.
            expectation='overhanging timber soffit of the western gable'
            passed=bool(material==EAVE and -.45<point[1]<.15 and 10.0<point[2]<10.4)
        rows.append(dict(camera=cam,opening=f'{name} {aperture}',expected_foremost=expectation,native_image_pixel=np.round(uv,2).tolist(),first_material=material,first_xyz_m=point,passed=passed))
    return dict(**scene.asset,rays=len(rows),passed=all(v['passed']for v in rows),checks=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args();j=check(a.mesh);a.output.write_text(json.dumps(j,ensure_ascii=False,indent=1)+'\n');print(sum(v['passed']for v in j['checks']),j['rays']);raise SystemExit(int(not j['passed']))
