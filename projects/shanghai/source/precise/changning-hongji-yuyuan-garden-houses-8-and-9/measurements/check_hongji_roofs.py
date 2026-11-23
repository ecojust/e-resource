"""Read the two roof studies against annotated ground photographs and two satellite images.

Use --components for editable-part checks. An independently decoded whole garden GLB
uses --mesh. The optional --house reads a local-coordinate, single-house study.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import struct
import numpy as np

M = Path(__file__).resolve().parent
PROJECT = M.parents[3]
sys.path.insert(0, str(M.parent / 'source'))
sys.path.insert(0, str(PROJECT / 'tools'))
sys.path.insert(0, str(M.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
import roof_8, roof_9
from hongji_roof_geometry import CAP, EAVE, VERGE, SOFFIT, STONE, BRICK, PEBBLE, TILE8, TILE9, FLASH
from glb_triangles import SerialScene

HOUSES = {8: roof_8, 9: roof_9}
TILES = {8: TILE8, 9: TILE9}
COVER = {TILE8, TILE9, CAP, FLASH, VERGE, SOFFIT, EAVE}
STACK = {8: {BRICK,STONE}, 9: {PEBBLE,STONE}}
# Display coordinates of the registered upright photographs. Points fall inside
# material, away from the horizon. Tree-covered areas are omitted. The south
# roof edge and Café terrace in the aerial tables retain their original labels.
PHOTO = {
    'winter2023-04': {'tile': [(374,407),(407,408),(459,395),(498,373)], 'shaft': [(643,224),(646,266)], 'cap':[(646,201)]},
    'winter2023-06': {'tile': [(248,337),(294,332),(336,328),(393,279),(482,279)], 'shaft':[(672,177),(674,212)], 'cap':[(676,140)]},
    'gao-02': {'tile':[(70,251),(85,246),(106,245)], 'shaft': [(283,92),(284,120)]},
    'winter2023-14': {'tile':[(283,351),(308,344),(334,336),(693,328),(724,333)], 'shaft':[(442,248)],'cap':[(449,238)]},
    'winter2023-18': {'tile':[(157,277),(188,272),(223,272),(695,307),(746,314)]},
    'commons-00': {'tile':[(36,346),(73,331),(628,206),(704,207),(744,207),(42,356),(75,345),(705,235),(742,235),(800,222),(831,213)], 'shaft':[(313,113)],'cap':[(312,98)]}
}

def read(path):
    return json.loads(path.read_bytes())

def component_review(n, lod, directory):
    from package_architectural_model import Builder
    model = HOUSES[n]
    builder = Builder({})
    model.add_roof(builder, lod, {})
    materials = Counter()
    counts = Counter()
    minimum_volume = np.inf
    for item in builder.parts:
        v = np.asarray(item['vertices'], dtype=float)
        f = np.asarray(item['triangles'], dtype=int)
        tri = v[f]
        # UV seams duplicate points. Compare original solid edges at micrometre resolution.
        _, vertices = np.unique(np.rint(v * 1.e6).astype(np.int64), axis=0, return_inverse=True)
        body = vertices[f]
        edges = Counter((a,b) for face in body for a,b in zip(face, np.roll(face, -1)))
        if any(a == b or multiplicity != 1 or edges[(b,a)] != 1 for (a,b), multiplicity in edges.items()):
            raise ValueError(('open or multiply used edge',n,lod,item['label']))
        origin = tri[0,0]
        volume = np.einsum('ij,ij->i',tri[:,0]-origin,np.cross(tri[:,1]-origin,tri[:,2]-origin)).sum()/6
        if volume <= 0: raise ValueError(('nonpositive volume',item['label'], volume))
        minimum_volume = min(minimum_volume, volume)
        if item['material'] == TILES[n]:
            uv = np.asarray(item['texcoords'])[f]
            det = (uv[:,1,0]-uv[:,0,0])*(uv[:,2,1]-uv[:,0,1]) - (uv[:,2,0]-uv[:,0,0])*(uv[:,1,1]-uv[:,0,1])
            if np.any(abs(det)<1.e-10): raise ValueError(('degenerate UV',item['label']))
            counts['faces_with_checked_tile_uv'] += len(uv)
        materials[item['material']] += len(f)
        counts['triangles'] += len(f)
    report = dict(house=n,lod=lod,closed_positive_parts=len(builder.parts),
                  minimum_closed_volume_m3=float(minimum_volume),triangles_by_material=dict(materials),**counts)
    if directory:
        output = directory / ('%d-%s.glb'%(n,'lod' if lod else 'near'))
        builder.save(output, {'title':'Roof geometry study','house':n})
        # The building packer sets REPEAT for these drawings. Preserve the same
        # sampler in isolated component exports, including their negative UVs.
        payload=output.read_bytes()
        length=struct.unpack_from('<I',payload,12)[0]
        document=json.loads(payload[20:20+length])
        for sampler in document.get('samplers',[]):
            sampler.update(wrapS=10497,wrapT=10497)
        chunk=json.dumps(document,separators=(',',':')).encode()
        chunk+=b' '*(-len(chunk)%4)
        tail=payload[20+length:]
        output.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(chunk)+len(tail))
                           +struct.pack('<II',len(chunk),0x4e4f534a)+chunk+tail)
        report['file'] = output.name
        report['sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    return report

def map_frame(n):
    record = read(M/'two-house-placement-and-garden-axes.json')['houses'][str(n)]
    linear = np.eye(3)
    linear[:2,0] = record['local_X_unit_EN']
    linear[:2,1] = record['local_Y_unit_EN']
    return np.array(record['left_wall_projection']['garden_ENU_m']+[0.]), linear

def sample(scene, origin, direction, allowed):
    hit = scene.ray(origin, direction, 95.)
    return {'matched':bool(hit and hit['material'] in allowed),
            'hit':None if hit is None else {'material':hit['material'],'point':np.around(hit['point_enu_m'],4).tolist()}}

def survey(scene, n, camera_file, local):
    offset, basis = map_frame(n)
    inverse = np.linalg.inv(basis)
    def ray(o, d, allowed):
        if not local: o,d = offset + basis@o,basis@d
        return sample(scene, o, d, allowed)
    rows=[]
    cameras=read(camera_file)[str(n)]['fits']
    for record in cameras:
        p=np.array(record['P'])
        transform=np.linalg.inv(p[:,:3])
        eye=-transform@p[:,3]
        for category,points in PHOTO[record['image']].items():
            allowed=COVER if category=='tile' else STACK[n] if category=='shaft' else {STONE}
            for u,v in points:
                rows.append(dict(source=record['image'],kind=category,uv=[u,v],**ray(eye,transform@[u,v,1.],allowed)))
    controls = read(M/('house-%d-roofs-and-source-points.json'%n))
    aerial=[]
    geo=read(M/'roof-aerial-two-ridge-registrations.json')[str(n)]
    for key in ('current','google'):
        image=controls['aerial_views'][key]
        for label,points in image['points'].items():
            for pt in points:
                if key=='current':pixel=np.array(pt)
                else:
                    global_pixel=np.asarray(image['global_z20_bounds'][:2])+pt
                    pixel=global_pixel/2-controls['aerial_views']['current']['global_z19_origin']
                def top_at(p):
                    xy=(p-[410,170])*[.2553423778884,-.2553423778884]
                    origin=inverse@(np.r_[xy,30.]-offset)
                    return ray(origin,[0,0,-1],COVER|STACK[n])
                absolute=top_at(pixel)
                if key=='google': pixel=pixel+geo['translation_to_esri_z19_px']
                result=top_at(pixel)
                # Outer rakes and silhouette points lie on a surface boundary.
                # State whether the roof lies within one metre of the original
                # pixel, as well as the unmodified central ray's actual hit.
                neighbours=[(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(-2,2),(2,-2),(2,2)]
                near=[top_at(pixel+shift)['matched'] for shift in neighbours]
                aerial.append(dict(source=key,feature=label,uv=pt,registered_z19=pixel.tolist(),
                                   geodetic_before_registration=absolute,
                                   within_0_77_m=result['matched'] or any(near),**result))
    # Direct downward rays to each editable face are independent of the view
    # selection. Endpoint and satellite misses stay observable in the output.
    probes=[]
    for zone,shape,plane in HOUSES[n].roof_sections({}):
        point=shape.representative_point()
        for fraction in (.32,.68):
            q=point if fraction==.32 else shape.centroid
            if not shape.contains(q) or q.distance(shape.boundary)<.12: q=point
            x,y=q.coords[0]
            probes.append(dict(zone=zone,local_xy=[round(x,4),round(y,4)],**ray(np.array([x,y,30.]),[0,0,-1],COVER|STACK[n])))
    return {'house':n,'photos':rows,'aerial':aerial,'roof_surface':probes,
            'summary':{k:[sum(row['matched'] for row in values),len(values)] for k,values in [('photo_pixels',rows),('aerial_pixels',aerial),('roof_faces',probes)]}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mesh',type=Path)
    parser.add_argument('--cameras',type=Path,default=M/'front-roof-registrations.json')
    parser.add_argument('--house',type=int,choices=[8,9])
    parser.add_argument('--components',action='store_true')
    parser.add_argument('--save-studies-to',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.components:
        out={'editable_components':[component_review(n,lod,args.save_studies_to) for n in HOUSES for lod in (False,True)]}
    else:
        if not args.mesh: parser.error('A GLB is required for ray checks')
        scene=SerialScene(args.mesh)
        out={'mesh':scene.asset,'registered_photographs_sha256':hashlib.sha256(args.cameras.read_bytes()).hexdigest(),
             'coordinate_system':'local house' if args.house else 'garden ENU',
             'houses':[survey(scene,n,args.cameras,bool(args.house)) for n in ([args.house] if args.house else HOUSES)]}
    args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    for result in out.get('houses',[]): print(result['house'],result['summary'])
    for result in out.get('editable_components',[]): print(result['house'],result['lod'],result['closed_positive_parts'],result['triangles'],result['faces_with_checked_tile_uv'])
if __name__=='__main__': main()
