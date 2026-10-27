"""Photo-led architecture geometry in metres, east/north/up. Python + numpy + Shapely.

Wall openings are polygon differences, with shared vertices and actual reveals.
The exporter changes axes to glTF east/up/south and batches by material. Photo
observations belong in each building's input/evidence, never in this helper.
"""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import math
import struct

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, MultiPolygon, box as rect
from shapely.geometry.polygon import orient
from shapely.ops import unary_union


PALETTE = {
    'limestone': {'color': [.61, .59, .54], 'roughness': .78},
    'carved pale stone': {'color': [.72, .70, .65], 'roughness': .70},
    'granite base': {'color': [.31, .32, .31], 'roughness': .75},
    'painted plaster': {'color': [.66, .65, .61], 'roughness': .88},
    'recessed glass': {'color': [.13, .18, .20], 'roughness': .22, 'metallic': .25},
    'recessed glass light': {'color': [.25, .30, .31], 'roughness': .30, 'metallic': .1},
    'bronze window frame': {'color': [.13, .13, .12], 'roughness': .43, 'metallic': .30},
    'painted window frame': {'color': [.37, .36, .31], 'roughness': .63},
    'roof zinc': {'color': [.21, .23, .23], 'roughness': .65, 'metallic': .25},
    'interior shadow': {'color': [.055, .055, .05], 'roughness': .95},
    'aged brass': {'color': [.45, .34, .12], 'roughness': .48, 'metallic': .65},
    'dark stone': {'color': [.11, .115, .11], 'roughness': .60},
    'wrought iron': {'color': [.08, .08, .075], 'roughness': .6, 'metallic': .5},
    'red brick': {'color': [.36, .19, .13], 'roughness': .87},
}


def pieces(geometry):
    if geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [orient(geometry, sign=1.)]
    # Clipped decorative strips may only touch a boundary, yielding a line or
    # point. They have no solid area and must not reach polygon triangulation.
    return [p for g in getattr(geometry, 'geoms', ()) for p in pieces(g)]


def opening(u, bottom, width, height, arch=0., segments=24):
    """Return an opening polygon. arch is rise above spring (0 = rectangle)."""
    if min(width, height) <= 0 or arch < 0 or arch > height:
        raise ValueError('Invalid opening dimensions')
    if not np.isfinite([u, bottom, width, height, arch]).all():
        raise ValueError('Opening dimensions must be finite')
    if arch and (not isinstance(segments, int) or segments < 3):
        raise ValueError('Arched opening needs at least three segments')
    if not arch:
        return rect(u-width/2, bottom, u+width/2, bottom+height)
    spring = bottom+height-arch
    points = [(u-width/2, bottom), (u+width/2, bottom)]
    points.extend((u+width/2*math.cos(i*math.pi/segments),
                   spring+arch*math.sin(i*math.pi/segments)) for i in range(segments+1))
    return Polygon(points)


class Builder:
    def __init__(self, palette=None):
        self.palette = {k: dict(v) for k, v in PALETTE.items()}
        self.palette.update(palette or {})
        self.parts = []

    def add(self, vertices, faces, material='limestone', label='detail'):
        if material not in self.palette:
            raise ValueError(f'Unknown material: {material}')
        vertices = [tuple(map(float, v)) for v in vertices]
        if not vertices or not np.isfinite(vertices).all():
            raise ValueError('Empty/non-finite geometry')
        triangles = []
        for face in faces:
            for k in range(1, len(face)-1):
                f = (face[0], face[k], face[k+1])
                a, b, c = (np.asarray(vertices[i]) for i in f)
                if np.linalg.norm(np.cross(b-a, c-a)) > 1e-10:
                    triangles.append(f)
        if triangles:
            self.parts.append({'label': label, 'material': material,
                               'vertices': vertices, 'triangles': triangles})

    def box(self, center, size, material='limestone', basis=None, label='detail'):
        if min(size) <= 0:
            return
        basis = np.eye(3) if basis is None else np.asarray(basis, float).T
        if basis.shape != (3, 3) or not np.isfinite(basis).all() or abs(np.linalg.det(basis)) < 1e-12:
            raise ValueError('Box basis must be finite and nonsingular')
        center = np.asarray(center)
        signs = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                 (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
        verts = [center+basis@(np.asarray(p)*np.asarray(size)/2) for p in signs]
        faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        if np.linalg.det(basis) < 0:
            faces = [tuple(reversed(f)) for f in faces]
        self.add(verts, faces, material, label)

    def prism(self, polygon, low, high, mapper, material='limestone', label='wall'):
        """Extrude a u,z polygon along outward d. Mapper accepts (u,z,d).

        u cross z must point along positive d. A wall's two skins, jambs,
        lintels and outer edge share exact vertices. No per-window wall boxes.
        """
        if high <= low:
            raise ValueError('Prism must have positive thickness')
        zero = np.asarray(mapper(0., 0., 0.), float)
        axes = np.asarray([np.asarray(mapper(*point), float)-zero
                           for point in [(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]])
        if axes.shape != (3, 3) or not np.isfinite(axes).all() or np.linalg.det(axes) <= 1e-12:
            raise ValueError('Prism mapper requires right-handed u,z,d axes: u cross z points along positive d')
        for poly in pieces(polygon):
            if not poly.is_valid:
                raise ValueError('Invalid wall polygon')
            vertices, faces, lookup = [], [], {}
            def index(u, z, d):
                key = (float(u), float(z), float(d))
                if key not in lookup:
                    lookup[key] = len(vertices)
                    vertices.append(mapper(*key))
                return lookup[key]
            tris = constrained_delaunay_triangles(poly)
            area = 0.
            for tri in tris.geoms:
                p = list(orient(tri, sign=1.).exterior.coords)[:3]
                area += tri.area
                faces.append(tuple(index(u,z,high) for u,z in p))
                faces.append(tuple(index(u,z,low) for u,z in reversed(p)))
            if abs(area-poly.area) > 1e-6*max(1., poly.area):
                raise ValueError('Triangulation lost wall area')
            for ring in [poly.exterior, *poly.interiors]:
                points = list(ring.coords)
                for a, b in zip(points, points[1:]):
                    faces.append((index(*a,low), index(*b,low), index(*b,high), index(*a,high)))
            self.add(vertices, faces, material, label)

    def plan_prism(self, polygon, bottom, top, material='limestone', label='roof'):
        # Map 2-D east/north polygon to horizontal x/y with d as altitude.
        self.prism(polygon, bottom, top, lambda x,y,d: (x,y,d), material, label)

    def tube(self, points, radius, material='wrought iron', sides=10, label='rail'):
        points = np.asarray(points, float)
        if points.ndim != 2 or points.shape[1] != 3 or len(points) < 2 or not np.isfinite(points).all():
            raise ValueError('Tube requires at least two finite 3-D points')
        if not math.isfinite(radius) or radius <= 0 or not isinstance(sides, int) or sides < 3:
            raise ValueError('Tube requires positive radius and at least three sides')
        if np.any(np.linalg.norm(np.diff(points, axis=0), axis=1) < 1e-10):
            raise ValueError('Tube has repeated adjacent points')
        vs = []
        for i, p in enumerate(points):
            direction = points[min(i+1,len(points)-1)]-points[max(0,i-1)]
            length = np.linalg.norm(direction)
            if length < 1e-10:
                raise ValueError('Tube has a reversing/undefined tangent')
            direction /= length
            aux = np.array([0.,0.,1.]) if abs(direction[2]) < .95 else np.array([0.,1.,0.])
            u = np.cross(direction, aux); u /= np.linalg.norm(u)
            v = np.cross(direction, u)
            vs.extend(p+radius*(u*math.cos(j*math.tau/sides)+v*math.sin(j*math.tau/sides)) for j in range(sides))
        fs = [tuple(reversed(range(sides))), tuple((len(points)-1)*sides+j for j in range(sides))]
        for k in range(len(points)-1):
            for j in range(sides):
                a=k*sides+j; b=k*sides+(j+1)%sides
                fs.append((a,b,b+sides,a+sides))
        self.add(vs, fs, material, label)

    def lathe(self, center, profile, material='carved pale stone', segments=32, label='column'):
        profile = np.asarray(profile, float)
        if profile.ndim != 2 or profile.shape[1] != 2 or len(profile) < 2 or not np.isfinite(profile).all():
            raise ValueError('Lathe profile requires at least two finite (height,radius) points')
        if np.any(profile[:,1] < 0) or np.any(np.diff(profile[:,0]) < 0) or profile[-1,0] <= profile[0,0]:
            raise ValueError('Lathe heights must increase from bottom to top and radii must be nonnegative')
        if not isinstance(segments, int) or segments < 3:
            raise ValueError('Lathe needs at least three segments')
        x,y = center
        vs = [(x+r*math.cos(j*math.tau/segments), y+r*math.sin(j*math.tau/segments), z)
              for z,r in profile for j in range(segments)]
        fs = [tuple(reversed(range(segments))), tuple((len(profile)-1)*segments+j for j in range(segments))]
        for k in range(len(profile)-1):
            for j in range(segments):
                a=k*segments+j; b=k*segments+(j+1)%segments
                fs.append((a,b,b+segments,a+segments))
        self.add(vs, fs, material, label)

    def photograph_parts(self, image, project_uv, select, *, name='PhotoFacade_CalibratedGlazing', roughness=.48, orientation=None):
        """Map original photo pixels only to explicitly selected real geometry.

        project_uv receives an ENU point and returns glTF top-left-origin UVs
        in the original stored image, not an automatically EXIF-rotated preview.
        The source image bytes are embedded unchanged; callers own calibration,
        region/occlusion selection, licence metadata and photographic QA.
        """
        image=Path(image).resolve()
        if not image.is_file() or image.stat().st_size>=100_000_000:
            raise ValueError('Photo source missing or exceeds file limit')
        selected=[p for p in self.parts if select(p)]
        if not selected:raise ValueError('Photographic selection is empty')
        if image.suffix.lower() not in ('.jpg','.jpeg','.png'):
            raise ValueError('Photo source must be an original JPEG or PNG')
        self.palette[name]={'color':[1.,1.,1.],'roughness':roughness,'metallic':0.,'texture':str(image)}
        if orientation is not None:self.palette[name]['extras']={'photographicSource':orientation}
        for part in selected:
            uv=np.asarray([project_uv(p) for p in part['vertices']],float)
            if uv.shape!=(len(part['vertices']),2) or not np.isfinite(uv).all() or np.any(uv<0) or np.any(uv>1):
                raise ValueError('Photo projection falls outside its source image')
            part['texcoords']=uv.tolist();part['material']=name
        return {'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
                'parts':len(selected),'labels':[p['label'] for p in selected]}

    def save(self, path, metadata=None):
        """Write a single embedded, uncompressed GLB and companion mesh audit."""
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        if not self.parts:
            raise ValueError('Cannot export an empty model')
        by_material = defaultdict(list)
        for part in self.parts:
            by_material[part['material']].append(part)
        binary = bytearray(); views=[]; accessors=[]; primitives=[]; materials=[];images=[];textures=[]
        image_indices={}
        def embed_image(filename):
            source=Path(filename); data=source.read_bytes(); key=hashlib.sha256(data).hexdigest()
            if key not in image_indices:
                while len(binary)%4:binary.append(0)
                vi=len(views);views.append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)})
                binary.extend(data)
                images.append({'name':source.name,'bufferView':vi,'mimeType':'image/png' if source.suffix.lower()=='.png' else 'image/jpeg'})
                textures.append({'source':len(images)-1,'sampler':0});image_indices[key]=len(textures)-1
            return image_indices[key]
        def accessor(array, kind, component, target):
            while len(binary)%4: binary.append(0)
            offset=len(binary); binary.extend(array.tobytes())
            vi=len(views); views.append({'buffer':0,'byteOffset':offset,'byteLength':array.nbytes,'target':target})
            ac={'bufferView':vi,'componentType':component,'count':len(array),'type':kind}
            if kind=='VEC3':ac.update(min=array.min(0).tolist(),max=array.max(0).tolist())
            accessors.append(ac); return len(accessors)-1
        total_triangles=0; bounds=[]
        for mi,(name,parts) in enumerate(by_material.items()):
            spec=self.palette[name]
            materials.append({'name':name,'pbrMetallicRoughness':{
                'baseColorFactor':spec['color']+[1], 'roughnessFactor':spec.get('roughness',.75),
                'metallicFactor':spec.get('metallic',0)}})
            if spec.get('extras'):materials[-1]['extras']=spec['extras']
            if spec.get('alpha') is not None:
                materials[-1]['pbrMetallicRoughness']['baseColorFactor'][3]=spec['alpha']
                materials[-1]['alphaMode']='BLEND';materials[-1]['doubleSided']=True
            textured=bool(spec.get('texture'))
            if textured:
                materials[-1]['pbrMetallicRoughness']['baseColorTexture']={'index':embed_image(spec['texture'])}
                if spec.get('normal_texture'):
                    materials[-1]['normalTexture']={'index':embed_image(spec['normal_texture']),'scale':spec.get('normal_scale',1.)}
                if spec.get('orm_texture'):
                    # Explicit glTF packed RGB occlusion/roughness/metalness.
                    # This differs from the older grayscale-roughness input.
                    ti=embed_image(spec['orm_texture'])
                    materials[-1]['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':ti}
                    materials[-1]['occlusionTexture']={'index':ti}
                if spec.get('roughness_texture'):
                    if spec.get('metallic',0)!=0:raise ValueError('Generic grayscale roughness requires metallicFactor=0')
                    materials[-1]['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':embed_image(spec['roughness_texture'])}
            verts=[]; norms=[]; ids=[]; uvs=[]; lookup={}
            for part in parts:
                if textured and len(part.get('texcoords',[]))!=len(part['vertices']):
                    raise ValueError('Every textured vertex requires calibrated UVs')
                xyz=np.asarray(part['vertices'],float)
                xyz=xyz[:,[0,2,1]]*np.array([1,1,-1])
                # Normals must describe the actual serialized FLOAT32 vertices.
                # A model whose triangles collapse at this precision is invalid;
                # do not silently export a solid with missing or zero-area faces.
                xyz=np.asarray(xyz,dtype='<f4').astype(float)
                for tri in part['triangles']:
                    a,b,c=xyz[list(tri)]; n=np.cross(b-a,c-a); length=np.linalg.norm(n)
                    if length<=1e-12:
                        raise ValueError(f'FLOAT32 collapsed a triangle in {part["label"]}; keep coordinates local and preserve representable thickness')
                    n/=length
                    for vertex_id,pos in zip(tri,(a,b,c)):
                        uv=part['texcoords'][vertex_id] if textured else []
                        key=tuple(np.asarray([*pos,*n,*uv],dtype='<f4'))
                        if key not in lookup:
                            lookup[key]=len(verts);verts.append(pos);norms.append(n)
                            if textured:uvs.append(uv)
                        ids.append(lookup[key])
            p=np.asarray(verts,dtype='<f4'); n=np.asarray(norms,dtype='<f4'); ind=np.asarray(ids,dtype='<u4')
            pa=accessor(p,'VEC3',5126,34962); na=accessor(n,'VEC3',5126,34962); ia=accessor(ind,'SCALAR',5125,34963)
            attributes={'POSITION':pa,'NORMAL':na}
            if textured:attributes['TEXCOORD_0']=accessor(np.asarray(uvs,dtype='<f4'),'VEC2',5126,34962)
            primitives.append({'attributes':attributes,'indices':ia,'material':mi})
            total_triangles+=len(ids)//3;bounds.extend([p.min(0),p.max(0)])
        while len(binary)%4:binary.append(0)
        bounds=np.asarray(bounds)
        doc={'asset':{'version':'2.0','generator':'Photo-informed architectural reconstruction v6',
                      'copyright':(metadata or {}).get('copyright','Geometry: MIT; map geometry: ODbL-1.0; source photographs retain their own licences')},
             'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':(metadata or {}).get('name',path.stem),'mesh':0}],
             'meshes':[{'primitives':primitives}],'materials':materials,'buffers':[{'byteLength':len(binary)}],
             'bufferViews':views,'accessors':accessors,'extras':metadata or {}}
        if images:
            doc.update(images=images,textures=textures,samplers=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}])
        data=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();data+=b' '*((-len(data))%4)
        glb=struct.pack('<4sII',b'glTF',2,28+len(data)+len(binary))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(binary),0x004e4942)+binary
        if len(glb)>=100_000_000:raise ValueError('Model must remain strictly below 100 MB')
        path.write_bytes(glb)
        report={'file':path.name,'bytes':len(glb),'sha256':hashlib.sha256(glb).hexdigest(),
                'triangles':total_triangles,'materials':len(materials),'parts':len(self.parts),
                'bounds_glb':{'min':bounds.min(0).tolist(),'max':bounds.max(0).tolist()},
                'part_summary':[{'label':p['label'],'material':p['material'],'vertices':len(p['vertices']),'triangles':len(p['triangles'])} for p in self.parts]}
        path.with_suffix('.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        return report


class Facade:
    """Directed CCW footprint edge; outward is its right-hand horizontal normal."""
    def __init__(self, builder, a, b, label='facade'):
        self.builder=builder;self.a=np.array([*a,0.]);self.b=np.array([*b,0.])
        self.length=float(np.linalg.norm(self.b-self.a))
        if not math.isfinite(self.length) or self.length < 1e-10:
            raise ValueError('Facade edge must have distinct finite endpoints')
        self.t=(self.b-self.a)/self.length
        self.n=np.array([self.t[1],-self.t[0],0.]);self.center=(self.a+self.b)/2;self.label=label
    def point(self,u,z,d=0):return self.center+self.t*u+self.n*d+np.array([0.,0.,z])
    def box(self,u,z,w,h,depth=.3,d=0,material='carved pale stone',label='trim'):
        self.builder.box(self.point(u,z,d),(w,depth,h),material,[self.t,self.n,[0,0,1]],self.label+'/'+label)
    def prism(self,poly,back,front,material='limestone',label='wall'):
        self.builder.prism(poly,back,front,self.point,material,self.label+'/'+label)
    def wall(self,bottom,top,holes=(),thickness=.48,material='limestone',outline=None):
        surface=outline if outline is not None else rect(-self.length/2,bottom,self.length/2,top)
        if holes:surface=surface.difference(unary_union(holes))
        self.prism(surface,-thickness,0,material,'continuous-open-wall')
        return surface
    def window(self,shape,columns=2,rows=3,frame='bronze window frame',trim=True,glass='recessed glass',label='window'):
        if not isinstance(columns,int) or not isinstance(rows,int) or min(columns,rows)<1:
            raise ValueError('Window rows and columns must be positive integers')
        bounds=shape.bounds; x0,z0,x1,z1=bounds; w=x1-x0
        inner=shape.buffer(-.09,join_style=2)
        if shape.is_empty or not shape.is_valid or inner.is_empty:
            raise ValueError('Window opening is invalid or too narrow for its frame')
        self.prism(inner,-.34,-.32,glass,label+'-glass')
        outer=shape.buffer(-.025,join_style=2)
        bars=[]
        for k in range(1,columns):
            x=x0+w*k/columns
            bars.append(rect(x-.028,z0,x+.028,z1))
        for k in range(1,rows):
            z=z0+(z1-z0)*k/rows
            bars.append(rect(x0,z-.027,x1,z+.027))
        # One solid frame grid removes coplanar crossing faces and internal
        # opposing end faces where mullions/transoms meet the perimeter frame.
        # Cut the remaining glass panes out of one outer solid. Cutting bars
        # against the inner curve first and unioning the pieces can leave tiny
        # arc-boundary slits that collapse to four-face edges in FLOAT32.
        panes=inner.difference(unary_union(bars)) if bars else inner
        self.prism(outer.difference(panes),-.27,-.16,frame,label+'-frame-grid')
        if trim:
            self.prism(shape.buffer(.16,join_style=2).difference(shape),-.025,.105,'carved pale stone',label+'-surround')
        self.box((x0+x1)/2,z0-.07,w+.30,.14,.60,.10,'carved pale stone',label+'-sill')
    def beam(self,z,height=.2,projection=.3,material='carved pale stone',width=None,label='cornice'):
        self.box(0,z,self.length+.1 if width is None else width,height,.48+projection,projection/2-.20,material,label)
    def line(self,a,b,radius=.04,material='wrought iron',sides=8,label='rail'):
        self.builder.tube([self.point(*a),self.point(*b)],radius,material,sides,self.label+'/'+label)


def facade_ring(builder, polygon, prefix='edge'):
    points=list(orient(polygon,sign=1.).exterior.coords)
    return [Facade(builder,a,b,f'{prefix}-{i}') for i,(a,b) in enumerate(zip(points,points[1:]))]
