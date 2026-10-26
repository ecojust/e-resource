#!/usr/bin/env python3
"""Actual v1→geometry-v2 identity and bracket exposure/support checks.

Only140 bracket solids and4descending-gable ridges may change. The ridge
revision has a separate independent acceptance report. No historical proof
is relabeled as testing the new raw; unchanged geometry is explicitly bound.
"""
from pathlib import Path
from collections import defaultdict
import argparse,hashlib,json,re
import numpy as np
from actual_glb import need,filemeta
from actual_bracket_geometry import ActualMeshes

HERE=Path(__file__).resolve().parent
BRACKET=re.compile(r'(?:(?:south|east|north|west)/)?(frame/e[0-3]/dougong[^/]+)/(lateral[0-2]|radial[0-2]|roof-bearing-saddle)')
RIDGE=re.compile(r'ridge/descending-gable-(?:-1|1)-(?:-1|1)')


def bind_structure(path,raw):
    r=json.loads(path.read_bytes())
    need(r.get('schema')=='zhenru-independent-actual-raw-structure-v1'
         and r.get('structure_passed') is True and r.get('raw')==raw,
         'Requires actual structure PASS bound to the exact raw: '+str(path))
    return filemeta(path)


def reachable(adjacency,start):
    seen={start};todo=[start]
    while todo:
        q=todo.pop();new=adjacency[q]-seen;seen|=new;todo.extend(new)
    return seen


def audit(old_path,new_path,old_structure,new_structure,tile_proof):
    old=ActualMeshes(old_path);new=ActualMeshes(new_path)
    oldmeta=old.raw['raw'];newmeta=new.raw['raw']
    oldstruct=bind_structure(old_structure,oldmeta);newstruct=bind_structure(new_structure,newmeta)
    need(set(old.raw['parts'])==set(new.raw['parts']),'Actual part label/material/occurrence sets differ')
    need(old.raw['materials']==new.raw['materials'],'Actual material definitions changed')
    need(old.raw['doc']['extras']['source_geometry_sha256']==new.raw['doc']['extras']['source_geometry_sha256'],
         'Source owner geometry changed')
    olddigest=hashlib.sha256();newdigest=hashlib.sha256();changed=[];nonallowed=[];unchanged_count=0
    roof_count=0;roof_digest_old=hashlib.sha256();roof_digest_new=hashlib.sha256();groups=defaultdict(list)
    for key in sorted(old.raw['parts']):
        label=key[0];a=old.raw['parts'][key];b=new.raw['parts'][key]
        pa=a['pos'][a['indices']];pb=b['pos'][b['indices']]
        na=a['norm'][a['indices']];nb=b['norm'][b['indices']]
        equal=np.array_equal(pa,pb) and np.array_equal(na,nb)
        bracket=BRACKET.fullmatch(label);allowed=bool(bracket or RIDGE.fullmatch(label))
        if bracket:groups[bracket.group(1)].append(label)
        if allowed:
            changed.append({'label':label,'geometry_changed':not equal,
                            'old_triangles':len(a['indices']),'new_triangles':len(b['indices']),
                            'old_actual_position_normal_sha256':hashlib.sha256(pa.tobytes()+na.tobytes()).hexdigest(),
                            'new_actual_position_normal_sha256':hashlib.sha256(pb.tobytes()+nb.tobytes()).hexdigest()})
        else:
            unchanged_count+=1
            if not equal:nonallowed.append(label)
            identity=json.dumps(key,separators=(',',':')).encode()
            olddigest.update(identity);olddigest.update(pa.tobytes());olddigest.update(na.tobytes())
            newdigest.update(identity);newdigest.update(pb.tobytes());newdigest.update(nb.tobytes())
        if label.startswith('roof/'):
            roof_count+=1
            roof_digest_old.update(label.encode());roof_digest_old.update(pa.tobytes());roof_digest_old.update(na.tobytes())
            roof_digest_new.update(label.encode());roof_digest_new.update(pb.tobytes());roof_digest_new.update(nb.tobytes())
    need(len(changed)==144 and len(groups)==20 and all(len(x)==7 for x in groups.values()),'Actual allowed144/20×7part schema differs')
    need(not nonallowed and olddigest.hexdigest()==newdigest.hexdigest(),'Non-allowlisted actual geometry/normals changed: '+repr(nonallowed))
    need(roof_digest_old.hexdigest()==roof_digest_new.hexdigest(),'Actual roof/tile bytes changed')
    historical=json.loads(tile_proof.read_bytes())
    need(historical.get('schema')=='zhenru-actual-cover-pan-piecewise-intersection-v2'
         and historical.get('strict_edge_band_contact_passed') is True
         and historical.get('pair_count')==8500 and historical.get('failed_pair_count')==0
         and historical.get('raw')==oldmeta,'Historical tile proof is not actual oldraw8500PASS')
    original_tile_hash=filemeta(tile_proof)

    roofs=[f'roof/field{i}/continuous-substrate' for i in range(4)]
    bracket_labels=sorted(x for members in groups.values() for x in members)
    visibility=[new.roof_visibility(label,roofs) for label in bracket_labels]
    noexposure=all(x['no_protrusion_passed'] and x['valid_single_interval_ray_count']>=5
                   and all(r['maximum_wood_above_roof_m']<=.00003 for r in x['corner_grid_rays']
                           if r['maximum_wood_above_roof_m'] is not None) for x in visibility)

    columns=[f'frame/column-{i}' for i in range(16)]
    ties=[f'{side}/eave-tie' for side in ['south','east','north','west']]
    contact_cache={}
    def contact(a,b):
        key=tuple(sorted((a,b)))
        if key not in contact_cache:contact_cache[key]=new.positive_contact(*key)
        return contact_cache[key]
    base=columns+ties;base_edges=[]
    for i,a in enumerate(base):
        for b in base[i+1:]:
            c=contact(a,b)
            if c['positive_volume_contact_found']:base_edges.append((a,b,c))
    chains=[]
    for group,members in sorted(groups.items()):
        nodes=base+members;adj={x:set() for x in nodes};edges=[]
        for a,b,c in base_edges:adj[a].add(b);adj[b].add(a);edges.append(c)
        for i,a in enumerate(members):
            for b in base+members[i+1:]:
                c=contact(a,b)
                if c['positive_volume_contact_found']:adj[a].add(b);adj[b].add(a);edges.append(c)
        saddle=next(x for x in members if x.endswith('/roof-bearing-saddle'))
        seen=reachable(adj,saddle)
        roofcontacts=[contact(saddle,r) for r in roofs]
        contacts_roof=any(x['positive_volume_contact_found'] for x in roofcontacts)
        row={'group':group,'all7members_connected_to_saddle':set(members)<=seen,
             'actual_support_columns':sorted(set(columns)&seen),'actual_support_eave_ties':sorted(set(ties)&seen),
             'saddle_has_actual_positive_volume_roof_contact':contacts_roof,
             'disconnected_group_parts':sorted(set(members)-seen),
             'positive_volume_contact_edges':edges,'saddle_roof_contact_proofs':roofcontacts}
        row['column_tie_arms_saddle_roof_chain_passed']=set(members)<=seen and bool(set(columns)&seen) and bool(set(ties)&seen) and contacts_roof
        chains.append(row)
    chainspass=all(r['column_tie_arms_saddle_roof_chain_passed'] for r in chains)
    need(filemeta(tile_proof)==original_tile_hash,'Historical tile report changed during audit')
    need(filemeta(old_path)==oldmeta and filemeta(new_path)==newmeta,'An actual raw changed during audit')
    return {'schema':'zhenru-actual-geometry-v2-bracket-preservation-v1','geometry_revision_passed':noexposure and chainspass,
            'raw':newmeta,'previous_raw':oldmeta,'structure_report':newstruct,'previous_structure_report':oldstruct,
            'changed_part_allowlist_count':144,'actual_allowed_parts':changed,'non_allowlisted_part_count':unchanged_count,
            'non_allowlisted_parts_byte_identical':True,'non_allowlisted_actual_position_normal_digest_old':olddigest.hexdigest(),
            'non_allowlisted_actual_position_normal_digest_new':newdigest.hexdigest(),'material_definitions_identical':True,
            'bracket_part_count':140,'bracket_no_protrusion_passed':noexposure,'bracket_support_chains_passed':chainspass,
            'maximum_actual_bracket_wood_above_roof_m':max(r['maximum_wood_above_roof_m'] for r in visibility),
            'bracket_visibility':visibility,'bracket_support_chains':chains,
            'tile_proof_carryforward':{'previous_raw':oldmeta,'current_raw':newmeta,'historical_report':original_tile_hash,
                'actual_all_roof_tile_triangle_normals_materials_unchanged':True,'roof_part_count':roof_count,
                'actual_roof_position_normal_digest_old':roof_digest_old.hexdigest(),
                'actual_roof_position_normal_digest_new':roof_digest_new.hexdigest(),'original_report_not_modified':True,
                'scope':'The historic8500pair proof still states only its originalraw. Every actual roof substrate/tile/bed position and normal and allmaterials are exactly unchanged in currentraw, providing an explicit geometry identity carryforward. This is not a rerun or relabeling of the historical report.'},
            'descending_ridge_revision_independently_accepted':False,
            'descending_ridge_scope':'Four allowed descending-gable ridge changes require separate actual ridge contact/connection/gable visibility report by reviewerA; this bracket report does not accept them.',
            'method':'Per-part serializedFloat32 triangle/normal bytes; actual wood/roof upward-facet projection intersections and allcellvertices; fullprojectedcoverage; conservative loweroverlaproof-envelope; additionalcorner/gridrays. Support graph edges require positive-area fourfacet heightfield intersection and independent singleactualrayinterval withpositiveembed.',
            'limitations':['No wholemodel collision/selfintersection or architectural accuracy certification.','Native appearance and browser remain separate; oldroof exposure and both oldtilecriteria failures are retained.','Only the declared144parts may change; gablepanels,16columns,allroof/tiles/doors remain exact.'],
            'native_or_browser_passed':False,'model_appearance_accepted':False,'author_geometry_modified_by_audit':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['old-raw','new-raw','old-structure','new-structure','historical-tile-proof','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();need(out.is_relative_to(HERE) and not out.exists(),'Use new report within independent-review')
    try:r=audit(a.old_raw.resolve(),a.new_raw.resolve(),a.old_structure.resolve(),a.new_structure.resolve(),a.historical_tile_proof.resolve())
    except Exception as exc:r={'schema':'zhenru-actual-geometry-v2-bracket-preservation-v1','geometry_revision_passed':False,'error':str(exc),'model_appearance_accepted':False}
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:r.get(k) for k in ['geometry_revision_passed','non_allowlisted_parts_byte_identical','bracket_no_protrusion_passed','bracket_support_chains_passed','maximum_actual_bracket_wood_above_roof_m','error']}))
    raise SystemExit(0 if r['geometry_revision_passed'] else 1)


if __name__=='__main__':main()
