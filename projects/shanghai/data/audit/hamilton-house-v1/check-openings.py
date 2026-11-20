"""Cast calibrated exterior rays into every delivered GLB, including the open shoulder arcades."""
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
# Front curves follow the measured 13.96m radius and separately surveyed ends.
r=13.95928
arc=lambda degrees:(r*math.sin(math.radians(degrees)),r*(math.cos(math.radians(degrees))-1))
pts=[(-16.57,-.87),*[arc(a)for a in (-56.3,-39.7,-16.7,16.7,39.7,56.3)],(16.33,-.58)]
FACES=list(zip(pts,pts[1:]))
SAMPLES=[
    (3, 'central domestic door glazing', 0.31, 1.97, ('grey blue residential glazing',1.2700), None),
    (3, 'raised threshold', 0.22, 0.081, ('dark entrance stone',0.0300), None),
    (3, 'dark stone entrance pier', 1.02, 2.02, ('dark entrance stone',-0.1600), None),
    (3, 'three-arch pale pier', 1.02, 3.85, ('sandstone coloured cast stone',-0.1300), None),
    (3, 'metal canopy fascia', 0.47, 4.55, ('silver canopy trim',-1.3600), None),
    (3, 'window below an arch', 2.27, 6.67, ('grey blue residential glazing',0.3200), None),
    (3, 'three-arch parapet', 0.95, 7.61, ('sandstone coloured cast stone',0.0000), None),
    (3, 'fabric awning', 0.49, 9.48, ('green canvas sunshade',-0.6100), None),
    (3, 'third floor central window', 0.16, 10.75, ('grey blue residential glazing',0.3200), None),
    (3, 'fifth floor north window', -1.81, 17.08, ('grey blue residential glazing',0.3200), None),
    (3, 'condenser housing near window', 2.66, 9.78, ('dark interior and vents',-0.3810), ('painted condenser case',-0.3600)),
    (3, 'setback tower arch shadow', 0.27, 48.34, ('painted steel casements',0.5300), ('dark interior and vents',0.7400)),
    (3, 'upper arch carved wall', 1.04, 49.1, ('sandstone coloured cast stone',0.0000), None),
    (2, 'north paired residential sash', -0.77, 24.38, ('grey blue residential glazing',0.3200), None),
    (4, 'south paired residential sash', 1.08, 28.12, ('grey blue residential glazing',0.3200), None),
    (1, 'outer north residential window', 0.12, 31.62, ('grey blue residential glazing',0.3200), None),
    (5, 'outer south residential window', 0.19, 14.11, ('grey blue residential glazing',0.3200), None),
    (0, 'north street wing glazing', 0.21, 17.7, ('grey blue residential glazing',0.3200), None),
    (6, 'south street wing glazing', 0.28, 21.15, ('grey blue residential glazing',0.3200), None),
    (2, 'north open double arcade', 0.97, 43.21, None, None),
    (4, 'south open double arcade', -0.96, 43.16, None, None),
    (3, 'crown light', 0.76, 56.38, ('grey blue residential glazing',1.4288), None),
    (3, 'crown fluting', 1.16, 57.61, ('sandstone coloured cast stone',1.0028), None),
    (3, 'raised north corner of crown', -2.7, 60.27, ('grey brown face brick',0.8588), None),
    (3, 'clear air above lower crown', 0.4, 60.3, None, None),
    (3, 'four letter name 福', -3.1789, 5.3124, ('gilded sign characters',-0.9170), None),
    (3, 'four letter name 州', -1.3126, 5.288, ('gilded sign characters',-0.9170), None),
    (3, 'four letter name 大', 1.2806, 4.9879, ('gilded sign characters',-0.9170), None),
    (3, 'four letter name 楼', 2.7173, 5.3748, ('gilded sign characters',-0.9170), None),
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
    args.report.write_text(json.dumps({'id':'huangpu-hamilton-house','script_sha256':digest(Path(__file__)),'ray_math_sha256':digest(HELPER),'variants':result},ensure_ascii=False,indent=2)+'\n')
    print('Checked',sum(len(a['rays'])for a in result),'street-facing surface or clear-sky rays.')
if __name__=='__main__':
    check()
