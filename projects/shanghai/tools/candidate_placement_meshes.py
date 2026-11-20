"""Measure actual delivered meshes against SHA-256-bound, owner-scoped city GLBs."""
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess

import numpy as np
import shapely as geo
from shapely.geometry import mapping, shape


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PlacementMeshes:
    def __init__(self, project, work, review):
        self.project = project
        self.work = work.resolve()
        self.work.mkdir(exist_ok=True, parents=True)
        self.review = review
        self.decoders = project/'data/audit/postal-office-v1'
        spec = importlib.util.spec_from_file_location('projected_mesh',
            project/'data/audit/country-hospital-v1/verify-placement.py')
        helpers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helpers)
        self.project_faces = helpers.project_triangles
        self.ground_faces = helpers.ground_projection
        self.env = dict(os.environ, POSTAL_REPO=str(project.parents[1]),
                        POSTAL_MAPPING_WORK=str(self.work), POSTAL_ASSET_PREFIX='')
        frame = review['author_frame']
        self.lon, self.lat = frame['anchor']['lng'], frame['anchor']['lat']
        h = math.radians(frame['runtime_heading_deg'])
        c, s = math.cos(h), math.sin(h)
        self.axes = np.array([[c, -s], [s, c]])
        self.k = frame['earth_radius_m'] * math.cos(math.radians(self.lat))
        self.loglat = math.asinh(math.tan(math.radians(self.lat)))
        self.files = {}
        for receipt in review['frozen_bindings']:
            key = receipt['repository_path']
            file = self.work/Path(key).name
            if not file.exists() or sha(file) != receipt['sha256']:
                file.write_bytes(subprocess.check_output(
                    ['git', 'show', review['baseline_commit']+':'+key], cwd=project.parents[1]))
            assert file.stat().st_size == receipt['bytes'] and sha(file) == receipt['sha256']
            self.files[file.name] = file
        table = json.loads(gzip.decompress(self.files['feature-table.json.gz'].read_bytes()))
        center = geo.Point(self.lon, self.lat)
        self.footprints = {r['localId']: geo.transform(shape(r['geometry']), self.to_xy)
            for r in table['features'] if shape(r['geometry']).distance(center) < .003}
        write(self.work/'initial-local-frame.json', {'anchor': frame['anchor']})

    def to_xy(self, points):
        north = (np.arcsinh(np.tan(np.radians(points[:, 1]))) - self.loglat) * self.k
        return np.column_stack((np.radians(points[:, 0] - self.lon)*self.k, north)) @ self.axes.T

    def to_wgs(self, points):
        east, north = (points @ self.axes).T
        return np.column_stack((self.lon+np.degrees(east/self.k),
                                np.degrees(np.arctan(np.sinh(self.loglat+north/self.k)))))

    def wgs(self, poly):
        return mapping(geo.transform(poly, self.to_wgs))

    def link(self, name, file):
        link = self.work/name
        link.unlink(missing_ok=True)
        link.symlink_to(file.resolve())

    def decode_model(self, manifest_path):
        doc = read(manifest_path)
        assert doc['id'] == self.review['model_id']
        assets = {}
        for role, variant in [('raw', 'raw'), ('full', 'web'), ('lod', 'lod')]:
            receipt = doc['assets'][role]
            file = manifest_path.parent/receipt['file']
            assert sha(file) == receipt['sha256'] and file.stat().st_size == receipt['bytes']
            self.link(variant+'.glb', file)
            assets[variant] = {key: receipt[key] for key in ('sha256', 'bytes', 'triangles')}
        subprocess.run(['node', self.decoders/'map-decode-delivered.mjs', self.work],
                       env=self.env, check=True, stdout=subprocess.DEVNULL)
        bounds, profiles, ground = [], [], []
        for variant in read(self.work/'delivered-decode.json'):
            tris = np.fromfile(variant['triangle_file'], np.float64).reshape(-1, 3, 3)
            assert len(tris) == assets[variant['variant']]['triangles'] and np.isfinite(tris).all()
            bounds.append([tris.min((0, 1)), tris.max((0, 1))])
            local = tris[:, :, [0, 2, 1]] * [1, -1, 1]
            profiles.append(self.project_faces(local))
            ground.append(self.ground_faces(local))
        bbox = np.array(bounds)
        collision = geo.union_all(ground, grid_size=.001).simplify(.025, preserve_topology=True)
        assert collision.is_valid and not collision.is_empty
        return (assets, {'min': bbox[:, 0].min(0).tolist(), 'max': bbox[:, 1].max(0).tolist()},
                geo.union_all(profiles), collision)

    def decode_group(self, group, checked_owner):
        ids = group['feature_local_ids']
        self.link('baseline-far.glb', self.files['far.glb'])
        self.link('baseline-near.glb.gz', self.files[Path(group['file']).name])
        self.link('macro-READY.json', self.files['READY.json'])
        write(self.work/'context-features.json', [{'localId': i} for i in ids])
        subprocess.run(['node', self.decoders/'map-decode-source.mjs'], env=self.env,
                       check=True, stdout=subprocess.DEVNULL)
        output = {}
        for variant in ('near', 'far'):
            tris = np.fromfile(self.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
            tris[:, :, :2] = tris[:, :, :2] @ self.axes.T
            if variant == 'far':
                owners = np.fromfile(self.work/'baseline-far-owners.u32',np.uint32)
                assignment = {'method': 'per-vertex _FEATURE_ID_0'}
            else:
                points = geo.points(tris[:, :, :2].mean(1))
                distances = np.stack([geo.distance(points,self.footprints[i]) for i in ids], axis=1)
                owners = np.asarray(ids)[distances.argmin(1)]
                near = np.sort(distances[owners == checked_owner],axis=1)
                max_own = float(near[:,0].max())
                margin = float((near[:,1]-near[:,0]).min())
                assert max_own < .4 and margin > 1.5, (checked_owner,max_own,margin)
                assignment = {'method': 'group IDs and triangle-centroid distance to original polygons',
                              'largest_own_distance_m': max_own,'smallest_next_owner_margin_m': margin}
            assert set(owners) == set(ids)
            output[variant] = (tris[owners==checked_owner],tris[owners!=checked_owner],assignment)
        return output
