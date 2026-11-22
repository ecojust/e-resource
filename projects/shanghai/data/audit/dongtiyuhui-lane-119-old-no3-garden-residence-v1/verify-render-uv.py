"""Compare the original embedded surface finishes, per-face UVs, and measured surface coverage."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/hongkou-dongtiyuhui-lane-119-old-no3-garden-residence/source'
sys.path.insert(0,str(SRC))
from build_blender_source import texture_faces
from material_names import TEXTURES
def check_material(path,reference,material):
    face=texture_faces(path,material)
    assert set(face)==set(reference)
    errors=[abs(np.array(uv)-np.array(reference[k][pt])).max() for k,row in face.items() for pt,uv in row.items()]
    maximum=float(max(errors));assert maximum<1e-4
    areas=[]
    for key,row in face.items():
        coords=np.array(list(row.values()))
        areas.append(abs(float(np.linalg.det(np.stack([coords[1]-coords[0],coords[2]-coords[0]])))))
    assert min(areas)>1e-10
    return dict(triangles=len(face),textured_corners=3*len(face),nondegenerate_texture_faces=sum(x>1e-9 for x in areas),
                embedded_texture_sha256=hashlib.sha256(TEXTURES[material].read_bytes()).hexdigest(),maximum_corner_uv_difference=maximum,
                scale='original per-material coordinates')
if __name__=='__main__':
    paths=list(map(Path,sys.argv[1:4]))
    data={}
    for role,path,ref in zip(('raw','full','lod'),paths,(paths[0],paths[0],Path(sys.argv[5]))):
        from asset_rights import document
        def textured_names(f):
            return {m['name'] for m in document(f)['materials'] if 'baseColorTexture' in m.get('pbrMetallicRoughness',{})}
        active=textured_names(ref)
        assert active==textured_names(path) and active<=TEXTURES.keys()
        if role!='lod':assert active==TEXTURES.keys()
        material={k:check_material(path,texture_faces(ref,k),k) for k in sorted(active)}
        data[role]=dict(textured_corners=sum(row['textured_corners']for row in material.values()),materials=material)
    Path(sys.argv[4]).write_text(json.dumps(data,indent=2)+'\n')
