"""Cast calibrated exterior rays into every delivered GLB, including central entrance recesses and the stepped-down south eave."""
from pathlib import Path
from argparse import ArgumentParser
import hashlib,importlib.util,json,math
import numpy as np

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
HELPER=PROJECT/'source/precise/huangpu-wing-on-skybridges/source/check_bridge.py'
spec=importlib.util.spec_from_file_location('entry_ray',HELPER)
helper=importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
# Inward distances are perpendicular to the visible chord or street segment.
# Test seven calibrated wall chords along the road arc, southwest to northeast.
FACES=[[[-29.384701, 13.85391], [-26.989428, 11.785073]], [[-16.267057, 5.136998], [-13.343657, 3.924316]], [[-7.372715, 1.825201], [-4.315616, 1.007563]], [[-4.315616, 1.007563], [4.341671, -0.882127]], [[4.341671, -0.882127], [7.480361, -1.284344]], [[19.686269, 1.407575], [22.440342, 2.962864]], [[31.790129, 11.444831], [33.843492, 13.853476]]]
SAMPLES=[
    (0, 'south end ground window', 0.21, 2.1, ('smoke grey glazing', 0.39), None),
    (0, 'south band bottom sill', 0.5, 4.99, ('pale window-band concrete', -0.115), None),
    (1, 'lower south ribbon', 0.26, 9.55, ('smoke grey glazing', 0.39), None),
    (1, 'air above lower south eave', 0.35, 21.71, None, None),
    (1, 'south parapet', 0.24, 18.8, ('buff glazed facing tile', -0.0), None),
    (2, 'south band upper edge', 0.3, 17.7, ('pale window-band concrete', -0.115), None),
    (2, 'south-side near central brick spandrel', 0.34, 14.89, ('buff glazed facing tile', -0.0), None),
    (3, 'left door glazing', -2.32, 1.86, ('smoke grey glazing', 0.88), None),
    (3, 'right door glazing', 2.32, 1.86, ('smoke grey glazing', 0.88), None),
    (3, 'shared round post', 0, 1.66, ('tan fluted stone', -0.2148), ('tan fluted stone', -0.2106)),
    (3, 'right portal stone edge', 4.06, 2.55, ('tan fluted stone', -0.17), None),
    (3, 'entry lintel', 0.97, 3.74, ('tan fluted stone', -0.21), None),
    (3, 'left paired high window', -1.7, 20.16, ('smoke grey glazing', 0.39), None),
    (3, 'right paired low window', 1.64, 5.89, ('smoke grey glazing', 0.39), None),
    (3, 'brick between paired windows', 0.02, 10.01, ('buff glazed facing tile', -0.0), None),
    (3, 'edge reed', 3.81, 11.05, ('brown glazed tile', -0.085), None),
    (3, 'upper band through centre', 0.3, 19.63, ('pale window-band concrete', -0.108), None),
    (3, 'retained high parapet', 0.48, 22.55, ('buff glazed facing tile', -0.0), None),
    (3, 'clear sky above high parapet', 0.4, 22.9, None, None),
    (4, 'first east upper window', 0.17, 20.41, ('smoke grey glazing', 0.39), None),
    (4, 'pale upper ribbon sill', 0.52, 19.63, ('pale window-band concrete', -0.115), None),
    (4, 'east bay narrow pier', 1.46, 16.82, ('buff glazed facing tile', -0.0), None),
    (5, 'east lower sash transom', 0.19, 9.85, ('dark metal window sash', 0.265), None),
    (5, 'east sixth-row glass', 0.21, 20.42, ('smoke grey glazing', 0.39), None),
    (5, 'east base window', 0.18, 1.74, ('smoke grey glazing', 0.39), None),
    (6, 'far east upper glazing', 0.17, 20.46, ('smoke grey glazing', 0.39), None),
    (6, 'east end brick surround', 1.48, 19.0, ('buff glazed facing tile', -0.0017), None),
    (6, 'outer northern wrap', 0.72, 8.65, ('pale window-band concrete', -0.115), None),
]

def check():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--report',type=Path,default=AUDIT/'opening-rays.json')
    args=parser.parse_args()
    result=[]
    for variant in json.loads((args.work/'delivered-decode.json').read_bytes()):
        coords=np.fromfile(variant['triangle_file'],np.float64).reshape(-1,3,3)
        coords=coords[:,:,[0,2,1]]*[1,-1,1]
        mats=np.fromfile(variant['triangle_material_ids_file'],np.uint16)
        faces=[]
        for a,c in FACES:
            a,c=np.array(a),np.array(c)
            axis=(c-a)/np.linalg.norm(c-a)
            inward=np.array([-axis[1],axis[0]])
            relative=coords[:,:,:2]-(a+c)/2
            faces.append(np.stack((relative@axis,coords[:,:,2],relative@inward),axis=2))
        records=[]
        for face,label,x,z,full,lod in SAMPLES:
            expected=lod if variant['variant']=='lod' and lod else full
            try:
                material,depth=helper.face_hit(faces[face],mats,variant['material_names'],x,z)
            except AssertionError:
                material,depth=None,None
            if expected is None:
                assert material is None and depth is None,(variant['variant'],label,material,depth)
            else:
                assert material==expected[0]and abs(depth-expected[1])<.025,(variant['variant'],label,material,depth)
            records.append({'feature':label,'facade_number':face,'x_m':x,'elevation_m':z,'material':material,'first_inward_distance_m':depth})
        result.append({'variant':variant['variant'],'sha256':variant['sha256'],'rays':records})
    digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    args.report.write_text(json.dumps({'id':'huangpu-texaco-building','script_sha256':digest(Path(__file__)),'ray_math_sha256':digest(HELPER),'variants':result},ensure_ascii=False,indent=2)+'\n')
    print('Checked',sum(len(a['rays'])for a in result),'street-facing surface or clear-sky rays.')
if __name__=='__main__':
    check()
