"""Apply metric texture coordinates, glass opacity and the six authored camera frames."""
from surface_textures import check_or_apply,check_glass,fitted_cameras
import json
def install(scene,data,raw):
    m=data['metadata']
    scene['model_id']=m['id']
    scene['geometry_license']=m['geometry_license']
    scene['gongyi_camera_views']=json.dumps(m['camera_views'],ensure_ascii=False)
    check_or_apply(scene,raw,True)
    check_glass(scene,raw,True)
    fitted_cameras(scene,m['camera_views'],True)
