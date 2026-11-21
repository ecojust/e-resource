"""Compare the exposed aggregate UV to distance along each exported curved profile."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

AUDIT = Path(__file__).resolve().parent.parent
SOURCE = AUDIT.parents[1] / 'source/precise/xuhui-wuxing-96-curved-cornice/source'
read_mesh = runpy.run_path(AUDIT/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
read_tex = runpy.run_path(AUDIT/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']


def inspect(path):
    triangles, material_ids, material_names, _ = read_mesh(path)
    textures, embedded, coordinates, _ = read_tex(path, material_ids)
    mat = material_names.index('Washed stone on window hood')
    picture = SOURCE/'window-hood-aggregate.png'
    sig = hashlib.sha256(picture.read_bytes()).hexdigest()
    assert set(embedded) == {mat} and embedded[mat]['embedded_sha256'] == sig
    assert embedded[mat]['texture_dimensions'] == [384,384]
    sampler = textures[mat][1]
    assert all(sampler.get(k,10497) == 10497 for k in ['wrapS','wrapT'])
    faces = triangles[material_ids == mat]
    uv = coordinates[material_ids == mat]
    assert np.min(faces[:,:,2]) > .799 and np.max(faces[:,:,2]) < .836

    # Accumulated distance for the two straight portions and the intervening arc.
    x,y,_ = faces.transpose(2,0,1)
    arc = (x > 1.e-5) & (y < .55-1.e-5)
    angles = np.arctan2(x[arc],.55-y[arc])
    steps = len(np.unique(np.round(angles,5)))+1
    assert steps in (14,48), steps
    angle = np.clip(np.arctan2(x,.55-y),0,np.pi/2)
    is_left = x < 1.e-6
    is_right = y >= .55 - 1.e-6
    radius = np.where(is_right,x,np.hypot(x,.55-y))
    # The actual export uses chords between neighbouring measured stations.
    correction = np.sinc(1/(4*steps))
    u = (.045 + radius*angle*correction + np.where(is_right,y-.55,0)) / .24
    u = np.where(is_left,(x+.045)/.24,u)
    max_error = float(np.max(np.abs(uv[:,:,0]-u)))
    assert max_error < .00002, max_error

    # The V differential on a profile edge must match its geometric length.
    checked_edges = 0
    worst_v = 0.
    for a,b in ((0,1),(1,2),(2,0)):
        edge = faces[:,a] - faces[:,b]
        midpoint = (faces[:,a]+faces[:,b])/2
        normal_angle = np.where(midpoint[:,0]<0,0,
            np.where(midpoint[:,1]>=.55,np.pi/2,np.arctan2(midpoint[:,0],.55-midpoint[:,1])))
        along = edge[:,0]*np.cos(normal_angle) + edge[:,1]*np.sin(normal_angle)
        profile = np.abs(along) < .00001
        actual = np.abs(uv[:,a,1]-uv[:,b,1])
        expected = np.linalg.norm(edge,axis=1)/.24
        if np.count_nonzero(profile):
            worst_v = max(worst_v,float(np.max(np.abs(actual[profile]-expected[profile]))))
            checked_edges += int(profile.sum())
    assert checked_edges >= len(faces) and worst_v < .00002, (checked_edges,worst_v)
    return dict(triangles=len(faces),profile_edges=checked_edges,arc_steps=steps,repeat_display_units=.24,
                max_u_error=max_error,max_v_error=worst_v,embedded_texture_sha256=sig,
                repeat_s=True,repeat_t=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['raw','full','lod','output']:
        parser.add_argument(name,type=Path)
    opt=parser.parse_args()
    result={name:inspect(getattr(opt,name)) for name in ('raw','full','lod')}
    opt.output.write_text(json.dumps(result,indent=2)+'\n')
