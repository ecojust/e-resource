"""Test actual unfiltered, first triangle hits at native upper-ornament photo pixels."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

# Interior controls are independent readings of the unmarked, full-resolution image.
# Each tuple gives native row and the individual measured columns across that row.
SAMPLES={
    'exposed aggregate':[(889,[1537,1564,1590]),(920,[1503,1537,1582,1625]),
       (955,[1481,1511,1550,1591,1631,1652]),(985,[1474,1503,1549,1581,1621,1656]),
       (1012,[1471,1492,1533,1572,1613,1645]),(1047,[1501,1534,1578,1604,1620]),(1066,[1523,1561,1593])],
    'smooth mount':[(925,[1442,1688]),(950,[1441,1693]),(979,[1443,1688]),(1018,[1443,1689]),
       (1054,[1447,1464,1666,1693]),(1070,[1445,1481,1640,1689]),(1085,[1447,1484,1667])],
    'grey hood stone':[(818,[1435,1487,1553,1610,1691,1705]),(843,[1440,1494,1550,1604,1680,1704]),
       (876,[1435,1456,1685,1705]),(893,[1435,1455,1682,1707])],
    'light cap':[(793,[1461,1506,1555,1597,1645,1681])],
    'bottom stone':[(1104,[1424,1472,1511,1563,1607,1648,1695]),(1120,[1428,1457,1518,1567,1608,1661,1698])]}

def check(glb,metric):
    scene=SerialScene(glb)
    registration=json.loads(metric.read_text())
    P=np.array(registration['2018_P']);lens=P[:,:3]
    eye=-np.linalg.solve(lens,P[:,3]);hits=[]
    for stone,rows in SAMPLES.items():
        for v,columns in rows:
            for u in columns:
                hit=scene.ray(eye,np.linalg.solve(lens,[u,v,1.]),35.)
                material=hit['material'] if hit else None
                hits.append({'uv':[u,v],'expected':stone,'visible_material':material,
                    'visible_point_m':np.round(hit['point_enu_m'],5).tolist() if hit else None,
                    'passed':material=='Tablet | '+stone})
    edge_pairs=[]
    outline=np.asarray(registration['native_px']['tablet'])
    for edge,(a,b) in enumerate(zip(outline,np.roll(outline,-1,axis=0))):
        outward=np.array([b[1]-a[1],a[0]-b[0]])/np.linalg.norm(b-a)
        for fraction in (.25,.5,.75):
            centre=a+fraction*(b-a);pair=[]
            # The upper straight edge faces the hood. The other seven face the mount.
            for offset,expected in [(-8.,'exposed aggregate'),(10.,'grey hood stone' if edge==0 else 'smooth mount')]:
                uv=centre+offset*outward
                hit=scene.ray(eye,np.linalg.solve(lens,[*uv,1.]),35.)
                observed=hit['material'] if hit else None
                pair.append({'uv':np.round(uv,3).tolist(),'offset_px':offset,'expected':expected,
                             'visible_material':observed,'passed':observed=='Tablet | '+expected})
            edge_pairs.append({'edge':edge,'fraction':fraction,'inside_outside':pair})
    return {'asset':scene.asset,'source_camera':'2018 street upper ornament',
            'method':'First triangle of the entire input asset on each original photographic ray. All materials participate.',
            'passed':all(row['passed'] for row in hits) and all(r['passed'] for e in edge_pairs for r in e['inside_outside']),
            'rays':hits,'edge_pairs':edge_pairs}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('glb',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--metric',type=Path,default=HERE/'central-tablet-metric.json');a=p.parse_args()
    result=check(a.glb,a.metric);a.out.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    failed=[(q['uv'],q['expected'],q['visible_material']) for q in result['rays'] if not q['passed']]
    print(result['asset']['sha256'],len(result['rays']),len(result['edge_pairs']),failed);raise SystemExit(0 if result['passed'] else 1)
