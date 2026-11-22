"""Compare the packed garden brick image, per-face UVs, and measured surface coverage."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/jingan-jiaozhou-450-garden-residence/source'
sys.path.insert(0,str(SRC))
from build_blender_source import texture_faces
from material_names import TEXTURE
def review(path,reference):
    face=texture_faces(path)
    assert face.keys()==reference.keys()
    errors=[abs(np.array(uv)-np.array(reference[k][pt])).max() for k,row in face.items() for pt,uv in row.items()]
    maximum=float(max(errors));assert maximum<1e-4
    areas=[]
    for key,row in face.items():
        coords=np.array(list(row.values()))
        areas.append(abs(float(np.linalg.det(np.stack([coords[1]-coords[0],coords[2]-coords[0]])))))
    assert min(areas)>1e-10
    return dict(triangles=len(face),textured_corners=3*len(face),nondegenerate_texture_faces=sum(x>1e-9 for x in areas),
                embedded_texture_sha256=hashlib.sha256(TEXTURE.read_bytes()).hexdigest(),maximum_corner_uv_difference=maximum,
                scale='The west gable, garden arcade and shaded porch wall repeat one 576 by 448px procedural atlas, covering 2.712 m by 2.048 m.')
if __name__=='__main__':
    paths=list(map(Path,sys.argv[1:4]));expected=texture_faces(paths[0])
    data={role:review(p,expected) for role,p in zip(('raw','full','lod'),paths)}
    Path(sys.argv[4]).write_text(json.dumps(data,indent=2)+'\n')
