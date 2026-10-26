#!/usr/bin/env python3
"""Finite independent probes of actual serialized Zhenru triangles.

No builder import, mesh generation, browser or Blender. Part labels select
candidate solids; actual Float32 positions establish dimensions, apertures,
supports and sampled contacts. This is not a whole-assembly collision proof.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, hashlib, json, math, re
import numpy as np
from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import unary_union
from shapely import set_precision
from actual_glb import loadraw, enu_tri, z, need, filemeta

HERE = Path(__file__).resolve().parent
TOL = 0.00003
GRID = 0.00001


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Audit:
    def __init__(self, raw, structure):
        self.r = loadraw(raw)
        proof=json.loads(structure.read_bytes())
        need(proof.get('schema')=='zhenru-independent-actual-raw-structure-v1'
             and proof.get('structure_passed') is True
             and proof.get('raw',{}).get('sha256')==self.r['raw']['sha256']
             and proof.get('raw',{}).get('bytes')==self.r['raw']['bytes'],
             'Requires passing actual-raw-structure proof bound to these exact raw bytes')
        self.structure_proof=filemeta(structure)
        self.c = json.loads((HERE.parent / 'calibration.json').read_text())
        self.e = self.c['estimated']
        self.failures = []
        self.results = {}
        a = math.radians(self.c['orientation']['model_x_axis_degrees_ccw_from_east'])
        self.rotation = np.array([[math.cos(a), -math.sin(a), 0],
                                  [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        self.labels = defaultdict(list)
        for key in self.r['parts']:
            self.labels[key[0]].append(key)
        self.cache = {}
        self.hulls = {}
        self.counts = Counter()
        self.extrema = {}
        ex = self.r['doc'].get('extras', {})
        need(ex.get('id') == 'putuo-zhenru-main-hall', 'Wrong raw identity')
        for field, name in [('source_geometry_sha256', 'geometry-input.json'),
                            ('calibration_sha256', 'calibration.json')]:
            need(ex.get(field) == digest(HERE.parent / name), 'Raw/source binding differs: ' + name)

    def check(self, good, group, detail):
        self.counts[group + '_checked'] += 1
        if not good:
            self.counts[group + '_failed'] += 1
            if len(self.failures) < 100:
                self.failures.append({'group': group, **detail})

    def triangles(self, label):
        if label not in self.cache:
            need(label in self.labels, 'Missing serialized part: ' + label)
            self.cache[label] = np.concatenate([
                enu_tri(self.r['parts'][key]) @ self.rotation for key in self.labels[label]])
        return self.cache[label]

    def hull(self, label):
        if label not in self.hulls:
            self.hulls[label] = MultiPoint(self.triangles(label)[:, :, :2].reshape(-1, 2)).convex_hull
        return self.hulls[label]

    def interval(self, label, xy):
        """Require a real single enter/exit interval, never a min/max envelope."""
        need(len(self.labels[label])==1,'Contact candidate has repeated/disconnected part label: '+label)
        t = self.triangles(label)
        a=t[:,0,:2];b=t[:,1,:2]-a;c=t[:,2,:2]-a;d=np.asarray(xy)-a
        det=b[:,0]*c[:,1]-b[:,1]*c[:,0];ii=np.flatnonzero(np.abs(det)>1e-12)
        if not len(ii):return None
        b,c,d,det,tt=b[ii],c[ii],d[ii],det[ii],t[ii]
        u=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/det;v=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/det
        hit=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
        if not hit.any():return None
        zz=tt[:,0,2]+u*(tt[:,1,2]-tt[:,0,2])+v*(tt[:,2,2]-tt[:,0,2])
        crossings=sorted(zip(zz[hit].tolist(),np.sign(det[hit]).astype(int).tolist()))
        levels=[]
        for height,sign in crossings:
            if levels and abs(height-levels[-1][0])<1e-6:levels[-1][1].add(sign)
            else:levels.append([height,{sign}])
        if len(levels)!=2 or levels[0][1]!={-1} or levels[1][1]!={1}:return None
        return levels[0][0],levels[1][0]

    def contact(self, left, right, group, require=True):
        """Actual vertical solid intervals at finite common-footprint samples.

        Convex hulls only propose points. Both actual triangle surfaces must
        supply top/bottom intersections before any contact is counted.
        """
        common = self.hull(left).intersection(self.hull(right))
        result = {'left': left, 'right': right, 'overlap_xy_m2': common.area,
                  'valid_samples': 0, 'minimum_signed_vertical_overlap_m': None,
                  'maximum_signed_vertical_overlap_m': None,'sample_points':[],
                  'sampled_supported_count':0,'sampled_gap_count':0,'missing_or_non_single_interval_count':0,
                  'criterion':'At least one sampled single solid interval overlaps within30microns; not all-surface support.'}
        values = []
        if not common.is_empty and common.area > 1e-10:
            rp = common.representative_point()
            points = [(rp.x, rp.y)]
            x0, y0, x1, y1 = common.bounds
            for fx in [.2, .5, .8]:
                for fy in [.2, .5, .8]:
                    p = (x0 + (x1-x0)*fx, y0 + (y1-y0)*fy)
                    if common.covers(Point(p)):
                        points.append(p)
            for xy in points:
                a, b = self.interval(left, xy), self.interval(right, xy)
                if a is not None and b is not None:
                    overlap=min(a[1], b[1]) - max(a[0], b[0]);values.append(overlap)
                    result['sampled_supported_count' if overlap>=-TOL else 'sampled_gap_count']+=1
                    result['sample_points'].append({'xy_m':list(xy),'left_interval_m':list(a),
                                                   'right_interval_m':list(b),'signed_overlap_m':overlap})
                else:
                    result['missing_or_non_single_interval_count']+=1
                    result['sample_points'].append({'xy_m':list(xy),'valid_single_intervals':False})
        if values:
            result.update(valid_samples=len(values), minimum_signed_vertical_overlap_m=min(values),
                          maximum_signed_vertical_overlap_m=max(values))
        if require:
            self.check(bool(values) and max(values) >= -TOL, group, result)
        elif require is False:
            self.check(bool(values), group, result)
        if values:
            ex = self.extrema.setdefault(group, {'minimum_signed_overlap_m': min(values),
                                                'maximum_signed_overlap_m': max(values)})
            ex['minimum_signed_overlap_m'] = min(ex['minimum_signed_overlap_m'], min(values))
            ex['maximum_signed_overlap_m'] = max(ex['maximum_signed_overlap_m'], max(values))
        self.counts[group+'_sampled_supported']+=result['sampled_supported_count']
        self.counts[group+'_sampled_gaps']+=result['sampled_gap_count']
        self.counts[group+'_missed_or_non_single_intervals']+=result['missing_or_non_single_interval_count']
        return result

    def projection(self, label, horizontal):
        """Dissolve actual triangle projection; 10micron grid is analysis only."""
        t = self.triangles(label)
        uv = np.stack([t[:, :, :2] @ np.asarray(horizontal), t[:, :, 2]], axis=2)
        polygons = []
        for tri in uv:
            p = Polygon(tri)
            if p.area > 1e-9:
                p = set_precision(p, GRID)
                if not p.is_empty and p.area > 0:
                    polygons.append(p)
        return unary_union(polygons)

    @staticmethod
    def holes(poly):
        geoms = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
        return [Polygon(r) for p in geoms if p.geom_type == 'Polygon' for r in p.interiors
                if Polygon(r).area > .00001]

    def architecture(self):
        columns = []
        actual_column_labels=[label for label in self.labels if re.fullmatch(r'frame/column-\d+',label)]
        self.check(len(actual_column_labels)==16,'actual_column_label_count',{'count':len(actual_column_labels)})
        grid = [-self.e['core_width_m']/2, -2.55, 2.55, self.e['core_width_m']/2]
        for i in range(16):
            label = 'frame/column-' + str(i)
            v = np.unique(self.triangles(label).reshape(-1, 3), axis=0)
            z0, z1 = v[:, 2].min(), v[:, 2].max()
            base = v[np.abs(v[:, 2]-z0) < .00001, :2].mean(axis=0)
            top = v[np.abs(v[:, 2]-z1) < .00001, :2].mean(axis=0)
            height = z1-z0
            inner = abs(base[0]) < 3 and abs(base[1]) < 3
            target = 6.45 if inner else 4.28
            corner = all(abs(abs(q)-self.e['core_width_m']/2) < .001 for q in base)
            lean = float(np.linalg.norm(top-base))
            wantlean = 0 if corner else (.16 if inner else .08)
            row = {'label': label, 'base_xy_m': base.tolist(), 'top_xy_m': top.tolist(),
                   'shaft_height_m': float(height), 'lean_magnitude_m': lean,
                   'inferred_role': 'inner' if inner else 'eave'}
            columns.append(row)
            self.check(abs(height-target) < .00002 and abs(lean-wantlean) < .00002
                       and all(min(abs(q-x) for x in grid) < .00002 for q in base), 'columns', row)
        self.check(sum(r['inferred_role'] == 'inner' for r in columns) == 4, 'column_roles', {'columns': columns})
        occupied={(int(np.argmin(np.abs(np.asarray(grid)-r['base_xy_m'][0]))),
                   int(np.argmin(np.abs(np.asarray(grid)-r['base_xy_m'][1])))) for r in columns}
        self.check(occupied=={(x,y) for x in range(4) for y in range(4)},
                   'column_grid_bijection',{'unique_grid_positions':len(occupied)})
        self.results['columns'] = columns

        walls = []
        for side, expected in [('south', 3), ('north', 1)]:
            label = side + '/continuous-open-wall'
            p = self.projection(label, [1, 0])
            holes = self.holes(p)
            row = {'side': side, 'actual_projected_hole_count': len(holes),
                   'hole_bounds_xz_m': [list(q.bounds) for q in holes]}
            self.check(len(holes) == expected, 'wall_through_apertures', row)
            central = [q for q in holes if q.bounds[0] < 0 < q.bounds[2]]
            self.check(len(central) == 1, 'wall_central_door_aperture', row)
            if len(central) == 1:
                opening = central[0]
                b = opening.bounds
                self.check(abs(b[0]+2.5) < .001 and abs(b[2]-2.5) < .001
                           and abs(b[1]-.60) < .001 and abs(b[3]-3.72) < .001,
                           'wall_door_dimensions', {'side': side, 'bounds': list(b)})
                # Six separate transverse stations through the actual wall void.
                probes = []
                for x in np.linspace(-2.5+5/12, 2.5-5/12, 6):
                    for height in [1.0, 2.0, 3.4]:
                        ok = opening.contains(Point(float(x), height)) and not p.covers(Point(float(x), height))
                        probes.append(bool(ok))
                self.check(all(probes), 'six_leaf_stations_through_wall', {'side': side, 'clear_probes': sum(probes), 'total': len(probes)})
            if side == 'south':
                flame = [q for q in holes if not (q.bounds[0] < 0 < q.bounds[2])]
                self.check(len(flame) == 2, 'flame_window_count', row)
                for q in flame:
                    x0, z0, x1, z1 = q.bounds
                    center = (x0+x1)/2
                    upper = q.intersection(Polygon([(x0,3.20),(x1,3.20),(x1,3.35),(x0,3.35)]))
                    self.check(abs(z0-1.3) < .001 and abs(z1-3.34) < .001
                               and abs((x1-x0)-2.02) < .001 and upper.area < .13,
                               'flame_window_shape', {'bounds': list(q.bounds), 'upper_cap_area_m2': upper.area})
                    self.check(q.contains(Point(center, 2.0)) and not p.covers(Point(center, 2.0)),
                               'flame_window_actual_void', {'center_x_m': center})
            walls.append(row)
        self.results['wall_apertures'] = walls

        leaves = []
        for side, prefix in [('south','south/six-leaf-entrance'), ('north','north/text-supported-six-leaf-entrance')]:
            centers = []
            actual_leaf_labels=[label for label in self.labels if re.fullmatch(re.escape(prefix)+r'/leaf-\d+',label)]
            self.check(len(actual_leaf_labels)==6,'actual_leaf_count',{'side':side,'count':len(actual_leaf_labels)})
            for i in range(6):
                label = prefix + '/leaf-' + str(i)
                v = np.unique(self.triangles(label).reshape(-1,3), axis=0)
                xy = v[:, :2]; center = xy.mean(axis=0); centers.append(center)
                _, _, vh = np.linalg.svd(xy-center, full_matrices=False)
                axis = vh[0]
                projected = self.projection(label, axis)
                holes = self.holes(projected)
                b = projected.bounds
                row = {'side': side, 'leaf': i, 'lattice_open_cells': len(holes),
                       'projected_width_m': b[2]-b[0], 'height_m': b[3]-b[1],
                       'center_xy_m': center.tolist(), 'horizontal_axis_unoriented': axis.tolist()}
                self.check(len(holes) >= 60 and abs((b[2]-b[0])-(5/6-.014)) < .001
                           and abs((b[3]-b[1])-3.12) < .001, 'real_lattice_door_leaves', row)
                leaves.append(row)
            centers = np.array(centers)
            pairdist=[float(np.linalg.norm(centers[i]-centers[j])) for i in range(6) for j in range(i+1,6)]
            self.check(min(pairdist)>.02,'door_leaf_placement_uniqueness',{'side':side,'minimum_center_distance_m':min(pairdist)})
            if side=='north':
                spacings=np.diff(np.sort(centers[:,0]))
                self.check(np.max(np.abs(spacings-5/6))<.001,'rear_leaf_transverse_assembly',{'spacing_m':spacings.tolist()})
            self.check(np.ptp(centers[:,1]) > .1 if side == 'south' else np.ptp(centers[:,1]) < .001,
                       'estimated_door_configuration_geometry', {'side': side, 'center_depth_range_m': float(np.ptp(centers[:,1]))})
        self.results['door_leaves'] = leaves

    def roof(self):
        substrates = ['roof/field' + str(i) + '/continuous-substrate' for i in range(4)]
        for label in substrates:
            self.check(label in self.labels, 'four_roof_patches', {'label': label})
        # Actual roof tiles / beds: no expected PASS inferred from author counters.
        tile_re = re.compile(r'^roof/field([0-3])/(pan|cover)/c(\d+)/r(\d+)$')
        tiles = {}
        for label in self.labels:
            m = tile_re.fullmatch(label)
            if m:
                field, kind, col, row = m.groups()
                tiles[(int(field), kind, int(col), int(row))] = label
        self.check(bool(tiles) and {x[0] for x in tiles} == {0,1,2,3}, 'tile_fields_present', {'tile_count': len(tiles)})
        lap_rows = []
        for (field, kind, col, row), label in sorted(tiles.items()):
            bed = f'roof/field{field}/heel-bearing-row{row}'
            if kind == 'pan':
                self.contact(label, bed, 'pan_to_heel_bed')
                following = tiles.get((field,kind,col,row+1))
                if following:
                    probe = self.contact(label, following, 'adjacent_course_contact', require=True)
                    if probe['valid_samples']:
                        # Record actual small clearances separately. Overlap in plan is not contact.
                        self.check(probe['maximum_signed_vertical_overlap_m'] > -.02,
                                   'adjacent_course_gap_under_20mm', probe)
                    if len(lap_rows) < 12:
                        lap_rows.append(probe)
            else:
                seat = label + '/hidden-seated-bedding'
                self.contact(label, seat, 'cover_to_hidden_seat')
                self.contact(seat, substrates[field], 'cover_seat_to_substrate')
                for adjacent in [col, col+1]:
                    pan = tiles.get((field,'pan',adjacent,row))
                    self.check(pan is not None, 'cover_adjacent_pan_exists', {'cover':label,'column':adjacent})
                    if pan:
                        self.contact(label,pan,'cover_to_pan_lip')
        for label in self.labels:
            m = re.fullmatch(r'roof/field([0-3])/heel-bearing-row\d+', label)
            if m:
                self.contact(label, substrates[int(m.group(1))], 'heel_bed_to_substrate')
        self.results['tile_count'] = len(tiles)
        self.results['sample_course_pair_records'] = lap_rows

        ridges = []
        main = 'ridge/continuous-main-ridge'
        for f in [0,1]:
            ridges.append(self.contact(main, substrates[f], 'main_ridge_to_substrate'))
        for sx in [-1,1]:
            hipfield = 2 if sx > 0 else 3
            for sy in [-1,1]:
                pitch = 0 if sy < 0 else 1
                desc = f'ridge/descending-gable-{sx}-{sy}'
                hip = f'ridge/continuous-hip-{sx}-{sy}'
                ridges.append(self.contact(main,desc,'main_to_descending_ridge'))
                ridges.append(self.contact(desc,hip,'descending_to_hip_ridge'))
                ridges.append(self.contact(desc,substrates[pitch],'descending_ridge_to_pitch'))
                for f in [pitch,hipfield]:
                    ridges.append(self.contact(hip,substrates[f],'hip_ridge_to_adjacent_patch'))
        self.results['ridge_finite_contacts'] = ridges
        central_high=[]
        for label in self.labels:
            if label.startswith(('ridge/','ornament/')):
                v=self.triangles(label).reshape(-1,3)
                ix=(np.abs(v[:,0])<.8)&(np.abs(v[:,1])<.6)&(v[:,2]>self.e['ridge_surface_z_m']+.6)
                if ix.any():central_high.append({'label':label,'maximum_z_m':float(v[ix,2].max())})
        self.check(not central_high,'no_background_pagoda_spire_on_main_ridge',{'unexpected_high_central_geometry':central_high})

        bracket_results=[]
        for label in self.labels:
            if label.endswith('/roof-bearing-saddle'):
                probes=[self.contact(label,sub,'bracket_seat_candidate',require=None)
                        for sub in substrates if self.hull(label).intersection(self.hull(sub)).area>1e-9]
                supported=any(p['valid_samples'] and p['maximum_signed_vertical_overlap_m']>=-TOL for p in probes)
                row={'label':label,'supported_by_actual_patch_sample':supported,'candidate_contacts':probes}
                self.check(supported,'bracket_saddle_to_roof',row);bracket_results.append(row)
        self.check(len(bracket_results)==20,'bracket_saddle_count',{'actual_count':len(bracket_results)})
        self.results['bracket_saddle_contacts']=bracket_results

        # At the four hip seams, compare actual triangle surfaces just inside each
        # patch. The equations only choose candidate xy stations; z is read from
        # serialized triangles. A1mm inward offset avoids ambiguous edge ownership.
        seams=[];hw=self.e['roof_half_width_m'];hd=self.e['roof_half_depth_m']
        gg=self.e['gable_half_length_m'];br=self.e['gable_break_run_m']
        for sx in [-1,1]:
            for sy in [-1,1]:
                pitch=0 if sy<0 else 1;hipfield=2 if sx>0 else 3;values=[]
                for t in np.linspace(.03,.97,25):
                    x=sx*(gg+(hw-gg)*t);y=sy*(br+(hd-br)*t)
                    a=self.interval(substrates[pitch],(x-sx*.001,y))
                    b=self.interval(substrates[hipfield],(x+sx*.001,y))
                    if a is not None and b is not None:
                        values.append(abs(a[1]-b[1]))
                row={'sx':sx,'sy':sy,'valid_samples':len(values),'maximum_surface_step_m':max(values) if values else None}
                self.check(len(values)==25 and max(values)<.015,'finite_hip_patch_seams',row);seams.append(row)
        self.results['hip_patch_seams']=seams
        values=[]
        for x in np.linspace(-gg+.1,gg-.1,31):
            a=self.interval(substrates[0],(x,-.001));b=self.interval(substrates[1],(x,.001))
            if a is not None and b is not None:values.append(abs(a[1]-b[1]))
        self.check(len(values)==31 and max(values)<.001,'finite_main_ridge_patch_seam',
                   {'valid_samples':len(values),'maximum_surface_step_m':max(values) if values else None})

    def run(self):
        self.architecture();self.roof()
        return {'schema':'zhenru-independent-actual-roles-contacts-v1','finite_checks_passed':not self.failures,
                'raw':self.r['raw'],'part_manifest_sha256':self.r['side_sha256'],
                'structure_report':self.structure_proof,
                'calibration':filemeta(HERE.parent/'calibration.json'),
                'test_counts':dict(self.counts),'contact_extrema':self.extrema,
                'first_at_most_100_failures':self.failures,'results':self.results,
                'tolerances':{'vertical_contact_m':TOL,'aperture_projection_grid_m':GRID,
                              'hip_seam_sample_step_limit_m':.015,'course_gap_limit_m':.02},
                'model_appearance_accepted':False,'native_or_browser_passed':False,
                'complete_collision_freedom_claimed':False,'current_rear_or_interior_certified':False,
                'scope':'Actual serialized Float32 geometry. Contacts require a single actual enter/exit ray interval from one serialized part and at least one supported station; all sample coordinates, gaps and misses are counted. Finite probes cannot prove global floating/nonfloating status and may miss narrow contacts. Geometric column bijection, actual wall voids and distinct perforated door leaves are tested. Labels select candidates only. Does not prove universal contact, self-intersection absence, whole-assembly structural safety, contemporary rear detail, or measured real-world dimensions.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--structure-proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();need(out.is_relative_to(HERE) and not out.exists(),'Use a new report in independent-review')
    try:r=Audit(a.raw.resolve(),a.structure_proof.resolve()).run()
    except Exception as exc:r={'schema':'zhenru-independent-actual-roles-contacts-v1','finite_checks_passed':False,'error':str(exc),'model_appearance_accepted':False}
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'report':str(out),'finite_checks_passed':r['finite_checks_passed'],'counts':r.get('test_counts'), 'error':r.get('error')}))
    raise SystemExit(0 if r['finite_checks_passed'] else 1)


if __name__=='__main__':main()
