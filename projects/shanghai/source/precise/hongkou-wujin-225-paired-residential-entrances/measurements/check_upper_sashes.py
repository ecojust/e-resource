"""Check dated original photograph sightlines against the first surface of a GLB."""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from upper_sashes import DATA, WINE,WHITE,AGED,GLASS,SHADE,DARK,CLOTH,FOLD,PANEL,BLUE,BLUE_EDGE,GREEN,IRON,PUTTY

# Hand readings on the common orthorectification, at 200px per model metre;
# the transformed Gao 04 original pixel is written alongside each result.
west=[
 ('upper glass',GLASS,[(285,253),(317,247),(390,255),(421,247)]),
 ('upper painted frame',WHITE,[(259,240),(353,243),(450,243),(290,296),(411,293)]),
 ('lower glass',GLASS,[(286,365),(296,403),(308,429),(389,365),(393,399),(405,433)]),
 ('brown lower blind',SHADE,[(268,503),(286,531),(292,562),(371,505),(393,520),(408,552)]),
 ('lower painted frame',WHITE,[(252,377),(243,501),(336,423),(332,515),(443,357),(434,537)]),
 ('old surround',WINE,[(233,439),(226,531),(461,385),(452,544)]),
 ('blue sheet',BLUE,[(220,149),(242,159),(316,144),(356,143),(408,139),(439,146)]),
 ('blue outer lip',BLUE_EDGE,[(205,125),(292,120),(382,107)])]
east=[
 ('transom',DARK,[(397,291),(430,281),(507,283),(548,280)]),
 ('red transom frame',WINE,[(371,287),(465,287),(597,287)]),
 ('left sash glazing',GLASS,[(408,392),(420,400),(412,472),(423,486),(409,563),(433,576)]),
 ('left sash paint',WINE,[(376,398),(375,475),(377,573),(457,389),(456,488),(455,558)]),
 ('right sash glazing',GLASS,[(598,324),(598,385),(592,465),(605,441),(598,551),(606,536)]),
 ('right sash paint',AGED,[(620,308),(620,399),(623,487)]),
 ('warm panel',PANEL,[(493,390),(523,388),(554,390)]),
 ('draped curtain',[CLOTH,FOLD],[(482,463),(503,473),(524,456),(546,456),(501,508),(514,553)]),
 ('open space behind casements',DARK,[(542,590),(558,570),(551,610)]),
 ('green ridged sheet',GREEN,[(296,120),(389,132),(435,153),(500,136),(545,172),(620,128),(639,177)]),
 ('two awning supports',WINE,[(342,112),(349,172),(587,129),(585,175)])]

def inspect(asset):
    p=np.asarray(DATA['camera_P']);eye=-np.linalg.solve(p[:,:3],p[:,3]);scene=SerialScene(asset);rows=[]
    for number,x0,z0,readings in [(9,-1.55,8.8,west),(11,1.15,9.15,east)]:
        for label,expected,points in readings:
            accepted=[expected]if isinstance(expected,str)else expected
            for u,v in points:
                t=np.array([x0+u/200,0,z0-v/200])
                uv=p@np.r_[t,1]
                hit=scene.ray(eye,t-eye,np.linalg.norm(t-eye)+2.)
                mat=hit['material']if hit else None
                rows.append(dict(window=number,observed=label,orthophoto_pixel=[u,v],original_gao04_pixel=(uv[:2]/uv[2]).round(3).tolist(),
                                 expected=accepted,first_material=mat,first_xyz=np.round(hit['point_enu_m'],4).tolist()if hit else None,passed=mat in accepted))
    return dict(source_photo_sha256=DATA['images']['Gao 04']['sha256'],mesh_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
                tests=rows,total=len(rows),hits=sum(r['passed']for r in rows),passed=all(r['passed']for r in rows))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('mesh',type=Path);a.add_argument('output',type=Path);v=a.parse_args();r=inspect(v.mesh)
    v.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n');print(r['total'],r['hits'],r['mesh_sha256'])
    for p in r['tests']:
        if not p['passed']:print(p['window'],p['observed'],p['orthophoto_pixel'],p['first_material'])
    raise SystemExit(int(not r['passed']))
