"""Reproject exterior photographic features into a model's uncompressed authored GLB.

All image positions use the original, uncropped pixel grid. Sampling a window
tests its visible frame and glazing. Missing or occluded source corners are
kept out of the statistics. Supply a new GLB to rerun the same observations.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct

HERE = Path(__file__).absolute().parent

def dot(a,b):
    return sum(x*y for x,y in zip(a,b))

def sub(a,b):
    return tuple(x-y for x,y in zip(a,b))

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def mesh(path):
    content=path.read_bytes()
    assert content[:4]==b'glTF'
    n=struct.unpack_from('<I',content,12)[0]
    d=json.loads(content[20:20+n])
    buf=memoryview(content)[28+n:]
    def accessor(i):
        a=d['accessors'][i]
        v=d['bufferViews'][a['bufferView']]
        count={'SCALAR':1,'VEC3':3}[a['type']]
        fmt=struct.Struct('<'+str(count)+{5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']])
        start=v.get('byteOffset',0)+a.get('byteOffset',0)
        step=v.get('byteStride',fmt.size)
        return [fmt.unpack_from(buf,start+j*step) for j in range(a['count'])]
    primitives=[]
    for node in d['nodes']:
        if 'mesh' not in node: continue
        assert not any(k in node for k in ('translation','rotation','scale','matrix'))
        for p in d['meshes'][node['mesh']]['primitives']:
            positions=[(x,-z,y) for x,y,z in accessor(p['attributes']['POSITION'])]
            ix=accessor(p['indices'])
            name=d['materials'][p['material']]['name']
            for i in range(0,len(ix),3):
                a,b,c=(positions[ix[j][0]] for j in (i,i+1,i+2))
                primitives.append((a,sub(b,a),sub(c,a),name))
    return primitives,hashlib.sha256(content).hexdigest()

def first(triangles,camera,uv):
    K,R=camera['K'],camera['R']
    v=(uv[1]-K[1][2])/K[1][1]
    u=(uv[0]-K[0][2]-K[0][1]*v)/K[0][0]
    eye=camera['eye'];direction=[dot(col,[u,v,1])for col in zip(*R)]
    nearest=float('inf');material=None
    for a,b,c,name in triangles:
        p=cross(direction,c)
        det=dot(b,p)
        if abs(det)<1e-10:continue
        t=sub(eye,a)
        bu=dot(t,p)/det
        if bu<0 or bu>1:continue
        q=cross(t,b);bv=dot(direction,q)/det
        if bv<0 or bu+bv>1:continue
        distance=dot(c,q)/det
        if 0<distance<nearest:
            nearest=distance;material=name
    return {'native_pixel':[round(t,2)for t in uv],'first_material':material,'model_point':None if material is None else [round(x+nearest*d,4)for x,d in zip(eye,direction)]}

def reprojection(cam,point):
    homogeneous=[dot(r,(*point,1.))for r in cam['P']]
    return [homogeneous[j]/homogeneous[2]for j in (0,1)]

def examine(path):
    triangles,digest=mesh(path)
    cameras=json.loads((HERE/'street-cameras.json').read_bytes())['cameras']
    panels=json.loads((HERE/'facade-control-pixels.json').read_bytes())['views']
    gate=json.loads((HERE/'gate-station-cameras.json').read_bytes())
    windows={}
    for key,view in panels.items():
        measured=view['points'];rows={}
        for window in ('A','B'):
            names=(window+'L',window+'R',window.lower()+'L')
            if not all(n in measured for n in names):continue
            tl,tr,bl=(measured[n]for n in names)
            br=measured.get(window.lower()+'R',[c+b-a for a,b,c in zip(tl,tr,bl)])
            samples=[]
            for h in (.33,.67):
                for w in (.24,.50,.76):
                    uv=[(1-h)*((1-w)*a+w*b)+h*((1-w)*c+w*d) for a,b,c,d in zip(tl,tr,bl,br)]
                    samples.append(first(triangles,cameras[key],uv))
            rows[window]={'source_corner_names':[n for n in (*names,window.lower()+'R') if n in measured],
                          'fourth_corner_interpolated':window.lower()+'R' not in measured,
                          'observations':samples}
        windows[key]=rows
    green=[a for a,b,c,n in triangles if 'green enamel address' in n]
    assert green
    # The four extremes of the enamel tablet are present in the emitted triangles.
    centre=[(min(v[j] for v in green)+max(v[j] for v in green))/2 for j in range(3)]
    plaque=gate['observations']['337 plaque centre']
    plates={}
    for key,cam in gate['cameras'].items():
        target=plaque['native_pixels'][key]
        model_uv=reprojection(cam,centre)
        plates[key]={'original_measured_pixel':target,'projected_model_centre':model_uv,'residual_px':math.dist(target,model_uv),
                     'observed_pixel_hit':first(triangles,cam,target),'actual_model_centre_hit':first(triangles,cam,model_uv)}
    return {'mesh_sha256':digest,'triangle_count':len(triangles),'frame':'Local exterior model axes, metres. Source observations retain independent calibration and date.','window_samples':windows,'street_number_tablet':{'model_centre':centre,'independent_photographic_centre':plaque['xyz'],'difference_xyz_m':sub(centre,plaque['xyz']),'views':plates},'limitations':'Native pixels on a transparent, partly open or reflective window can hit a frame, sash or the surface behind it. Sparse corners use a fourth corner interpolated in the image; these tests do not measure the hidden wall or the interior.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.write_text(json.dumps(examine(args.mesh),ensure_ascii=False,indent=2)+'\n')
