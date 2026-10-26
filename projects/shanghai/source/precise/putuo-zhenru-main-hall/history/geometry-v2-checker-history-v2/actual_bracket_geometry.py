"""Read actual bracket solids and roof facets; no builder import or generation."""
from collections import defaultdict,Counter
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from actual_glb import loadraw, enu_tri, need
from audit_cover_pan_intersection import clip, area

INTERSECTION_DECOMPOSITION_COUNTS=Counter()

def positive_polygons(geometry):
    """Retain every areal component of a GEOS intersection, without buffering.

    Exact shared triangle edges can also appear as zero-area LineStrings in
    GeometryCollections. They cannot establish a positive-volume joint.
    """
    if geometry.is_empty:
        INTERSECTION_DECOMPOSITION_COUNTS['empty_intersections']+=1
        return []
    if geometry.geom_type=='Polygon':
        need(not geometry.interiors,'Unexpected hole in convex facet cell')
        return [geometry] if geometry.area>0 else []
    INTERSECTION_DECOMPOSITION_COUNTS[geometry.geom_type]+=1
    if geometry.area==0 and not hasattr(geometry,'geoms'):
        INTERSECTION_DECOMPOSITION_COUNTS['explicitly_ignored_zero_area_components']+=1
    result=[]
    for part in getattr(geometry,'geoms',[]):result.extend(positive_polygons(part))
    need(abs(sum(p.area for p in result)-geometry.area)<=1e-10,'Areal intersection component lost')
    return result


class ActualMeshes:
    def __init__(self,path):
        self.raw=loadraw(path);self.labels=defaultdict(list);self.cache={}
        for key in self.raw['parts']:self.labels[key[0]].append(key)

    def mesh(self,label):
        if label in self.cache:return self.cache[label]
        need(len(self.labels[label])==1,'Require one actual part per contact label: '+label)
        t=enu_tri(self.raw['parts'][self.labels[label][0]])
        faces={'up':[],'down':[]}
        for triangle in t:
            n=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0])
            if abs(n[2])<1e-12:continue
            polygon=Polygon(triangle[:,:2]);plane=np.linalg.solve(np.column_stack([triangle[:,:2],np.ones(3)]),triangle[:,2])
            faces['up' if n[2]>0 else 'down'].append({'poly':polygon,'plane':plane})
        for side in ['up','down']:
            need(faces[side],'No actual '+side+' facets: '+label)
            faces[side+'_tree']=STRtree([f['poly'] for f in faces[side]])
        faces['triangles']=t;faces['plan']=unary_union([f['poly'] for f in faces['up']]);faces['label']=label
        faces['bbox3']=(t.min(axis=(0,1)),t.max(axis=(0,1)))
        self.cache[label]=faces;return faces

    def interval(self,label,xy):
        m=self.mesh(label);levels=[]
        p=Point(xy)
        for side,sign in [('up',1),('down',-1)]:
            for i in m[side+'_tree'].query(p):
                f=m[side][int(i)]
                if f['poly'].covers(p):levels.append((float(f['plane']@[*xy,1]),sign))
        merged=[]
        for z,sign in sorted(levels):
            if merged and abs(z-merged[-1][0])<1e-6:merged[-1][1].add(sign)
            else:merged.append([z,{sign}])
        if len(merged)!=2 or merged[0][1]!={-1} or merged[1][1]!={1}:return None
        return merged[0][0],merged[1][0]

    def positive_contact(self,left,right,minimum_embed=.000001):
        """Find positive-area overlap of actual four heightfield facet cells.

        A witness proves local positive volume, not full contact everywhere.
        Both actual solids must have a single vertical interval at the witness.
        """
        a,b=self.mesh(left),self.mesh(right)
        result={'left':left,'right':right,'positive_volume_contact_found':False}
        if np.any(np.minimum(a['bbox3'][1],b['bbox3'][1])-np.maximum(a['bbox3'][0],b['bbox3'][0])<=0):return result
        for au in a['up']:
            for bi in b['up_tree'].query(au['poly']):
                bu=b['up'][int(bi)];p=au['poly'].intersection(bu['poly'])
                if p.area<1e-10:continue
                for ai in a['down_tree'].query(p):
                    ad=a['down'][int(ai)];q=p.intersection(ad['poly'])
                    if q.area<1e-10:continue
                    for bj in b['down_tree'].query(q):
                        bd=b['down'][int(bj)];cell=q.intersection(bd['poly'])
                        if cell.area<1e-10:continue
                        for polygon in positive_polygons(cell):
                            vertices=[list(x) for x in polygon.exterior.coords[:-1]]
                            c1=au['plane']-bd['plane'];c2=bu['plane']-ad['plane']
                            c1=c1.copy();c2=c2.copy();c1[2]-=minimum_embed;c2[2]-=minimum_embed
                            cut=clip(clip(vertices,c1),c2)
                            if area(cut)<=1e-10:continue
                            joint=Polygon(cut);point=joint.representative_point();xy=(point.x,point.y)
                            ia,ib=self.interval(left,xy),self.interval(right,xy)
                            if ia is None or ib is None:continue
                            overlap=min(ia[1],ib[1])-max(ia[0],ib[0])
                            if overlap<minimum_embed-1e-8:continue
                            return {**result,'positive_volume_contact_found':True,'witness_cell_area_m2':joint.area,
                                    'witness_xy_m':list(xy),'actual_left_interval_m':list(ia),'actual_right_interval_m':list(ib),
                                    'witness_vertical_overlap_m':overlap,'minimum_clip_embed_m':minimum_embed}
        return result

    def roof_visibility(self,label,roof_labels):
        """All actual wood upper facets against every overlapping roof upper facet.

        Comparing every roof candidate is conservative at seams: no arbitrary
        higher facet can hide an exposure against a lower overlapping patch.
        """
        wood=self.mesh(label);roof_faces=[]
        for r in roof_labels:
            for f in self.mesh(r)['up']:roof_faces.append((r,f))
        tree=STRtree([f['poly'] for _,f in roof_faces]);covered=[];cells=[];maximum=-float('inf');minimum=float('inf')
        for wf in wood['up']:
            for i in tree.query(wf['poly']):
                r,rf=roof_faces[int(i)];p=wf['poly'].intersection(rf['poly'])
                if p.area<1e-12:continue
                for polygon in positive_polygons(p):
                    covered.append(polygon);difference=wf['plane']-rf['plane']
                    values=[float(difference@[*xy,1]) for xy in polygon.exterior.coords[:-1]]
                    maximum=max(maximum,*values);minimum=min(minimum,*values)
                    cells.append({'roof':r,'area_m2':polygon.area,'maximum_wood_above_roof_m':max(values),
                                  'minimum_wood_above_roof_m':min(values)})
        covered_union=unary_union(covered);uncovered=wood['plan'].difference(covered_union)
        # Old unchanged roof fields have Float32 sub-micron seam slivers. Keep
        # their absence of exact coverage explicit; bound horizontal distance
        # to actual roof triangles, then report actual adjacent-ray heights.
        seam_records=[]
        gap_parts=[uncovered] if uncovered.geom_type=='Polygon' else list(getattr(uncovered,'geoms',[]))
        for gap in gap_parts:
            if gap.area<=1e-18:continue
            near=[roof_faces[int(i)][1]['poly'] for i in tree.query(gap.buffer(.000003))]
            local_roof=unary_union(near)
            def within(radius):
                return gap.difference(local_roof.buffer(radius,quad_segs=32)).area<=1e-18
            lo,hi=0.,.000002
            bounded=within(hi)
            if bounded:
                for _ in range(24):
                    mid=(lo+hi)/2
                    if within(mid):hi=mid
                    else:lo=mid
            rp=gap.representative_point();xy=(rp.x,rp.y);wi=self.interval(label,xy);adjacent=[]
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                q=(xy[0]+dx*.000001,xy[1]+dy*.000001)
                for r in roof_labels:
                    ri=self.interval(r,q)
                    if ri is not None:adjacent.append({'offset_xy_m':[dx*.000001,dy*.000001],
                                                       'actual_xy_m':list(q),'roof':r,'roof_interval_m':list(ri)})
            maxabove=max((wi[1]-x['roof_interval_m'][1] for x in adjacent),default=None) if wi else None
            seam_records.append({'actual_uncovered_area_m2':gap.area,
                 'maximum_horizontal_distance_to_actual_roof_lower_m':lo if bounded else None,
                 'maximum_horizontal_distance_to_actual_roof_upper_m':hi if bounded else None,
                 'horizontal_distance_bound_method':'Binary coverage by32-segment conservative circular buffers of actual neighboring projected roof triangles; analysis only, no model/source geometry changes.',
                 'representative_xy_m':list(xy),'actual_wood_interval_at_uncovered_point_m':wi,
                 'actual_adjacent_roof_rays':adjacent,'maximum_wood_top_minus_actual_adjacent_roof_top_m':maxabove,
                 'float32_seam_with_bounded_height_uncertainty':bounded and wi is not None and bool(adjacent)
                     and maxabove is not None and maxabove<-.001})
        seams_ok=uncovered.area<=.000001 and all(x['float32_seam_with_bounded_height_uncertainty'] for x in seam_records)
        # Additional actual corner/grid rays retain direct, interpretable samples.
        p=wood['plan'];rp=p.representative_point();samples=[]
        pieces=[p] if p.geom_type=='Polygon' else list(p.geoms)
        for q in pieces:
            for xy in q.exterior.coords[:-1]:
                v=np.array(xy);delta=np.array([rp.x,rp.y])-v
                if np.linalg.norm(delta)>0:v=v+delta/np.linalg.norm(delta)*.000001
                if p.covers(Point(v)):samples.append(('corner-inset1micron',tuple(v)))
        x0,y0,x1,y1=p.bounds
        for fx in [.05,.25,.5,.75,.95]:
            for fy in [.05,.25,.5,.75,.95]:
                xy=(x0+(x1-x0)*fx,y0+(y1-y0)*fy)
                if p.covers(Point(xy)):samples.append(('grid',xy))
        rays=[]
        for kind,xy in samples:
            wi=self.interval(label,xy);ri=[]
            for r in roof_labels:
                q=self.interval(r,xy)
                if q is not None:ri.append((r,q))
            rays.append({'kind':kind,'xy_m':list(xy),'wood_interval_m':wi,'roof_intervals':ri,
                         'maximum_wood_above_roof_m':max((wi[1]-q[1] for _,q in ri),default=None) if wi else None})
        valid=[r for r in rays if r['maximum_wood_above_roof_m'] is not None]
        return {'label':label,'no_protrusion_passed':bool(cells) and seams_ok and maximum<=.00003,
                'actual_wood_top_plan_area_m2':p.area,'uncovered_by_actual_roof_area_m2':uncovered.area,
                'exact_full_roof_coverage':uncovered.area<=1e-18,'float32_roof_seam_uncertainty_bounded':seams_ok,
                'actual_microseam_distance_and_height_records':seam_records,
                'actual_intersection_cell_count':len(cells),'maximum_wood_above_roof_m':maximum if cells else None,
                'minimum_wood_above_roof_m':minimum if cells else None,
                'exposed_cells':[c for c in cells if c['maximum_wood_above_roof_m']>.00003],
                'corner_grid_ray_count':len(rays),'valid_single_interval_ray_count':len(valid),'corner_grid_rays':rays,
                'roof_envelope_rule':'Every intersecting roof facet is checked; lower overlapping facet governs conservatively. No coordinate snapping. Any uncovered oldroofseam is separately bounded to<=2microns actual horizontal distance and<=1e-6m2 total area, with actual adjacent1micron rays requiring woodtop more than1mm belowroof. Such a seam is explicitly not exact coverage. Other upward exposure uses30micron Float32 vertical tolerance.'}
