#!/usr/bin/env python3
"""Actual six column top caps are below and fully under the terrace surface."""
import json,argparse
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from modern_mesh import load_raw,filemeta,require,oriented_position_hash
from finite_checks import contact_witness

def top_projection(part):
 t=part.triangles_enu;z=float(t[:,:,2].max());faces=[]
 for q in t:
  n=np.cross(q[1]-q[0],q[2]-q[0])
  if n[2]>0 and np.max(abs(q[:,2]-z))<=1e-9:faces.append(Polygon(q[:,:2]))
 require(faces,'No actual horizontal upper cap');return unary_union(faces),z

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--structure',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 require(not a.output.exists(),'Preserve prior results');asset=load_raw(a.raw);proof=json.loads(a.structure.read_bytes());require(proof['structure_passed'] is True and proof['asset_identity']['raw']['sha256']==asset.identity['raw']['sha256'],'No matching actual structure proof')
 baseline={p['key']:p for p in proof['part_results']}
 columns=asset.select({'prefix':'colonnade/F5/round-column-','expected_count':6})
 surface=asset.select({'label':'terrace/F6/colonnade-walking-surface','expected_count':1})[0]
 deck=asset.select({'label':'terrace/F6/colonnade-roof-deck','expected_count':1})[0]
 for p in columns+[surface,deck]:require(oriented_position_hash(p.triangles_enu)==baseline[p.key]['oriented_position_triangles_sha256'],'Actual part/proof mismatch')
 surface_top,height=top_projection(surface);frame={'origin_enu_m':[0,0,0],'axes_enu':[[1,0,0],[0,1,0],[0,0,1]]};rows=[]
 for p in columns:
  cap,top=top_projection(p);outside=cap.difference(surface_top);gap=height-top;contact=contact_witness(p,deck,frame)
  rows.append({'key':p.key,'actual_column_top_m':top,'actual_walking_surface_top_m':height,
   'actual_vertical_clearance_m':gap,'actual_top_cap_area_m2':cap.area,'actual_cap_outside_surface_plan_area_m2':outside.area,
   'actual_column_deck_contact':contact,'passed':bool(gap>.02 and outside.area<1e-9 and contact['positive_volume_contact_found'])})
 report={'schema':'library-actual-colonnade-cap-clearance-v1','cap_clearance_passed':all(x['passed'] for x in rows),
  'asset_identity':asset.identity,'source_structure_report':filemeta(a.structure),'column_count':len(rows),'actual_columns':rows,
  'minimum_required_vertical_clearance_m':.02,'maximum_uncovered_cap_plan_area_m2':1e-9,
  'checker_files':[filemeta(__file__),filemeta(Path(__file__).parent/'modern_mesh.py'),filemeta(Path(__file__).parent/'finite_checks.py')],
  'scope':'Actual maximum-height cap surfaces of all six F5 columns lie strictly below, and their entire top-cap footprints under, actual walking-surface top. Each column also has an actual positive-volume deck joint. Other collisions, images and engineering are not inferred.'}
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':filemeta(a.output),'passed':report['cap_clearance_passed']}));raise SystemExit(0 if report['cap_clearance_passed'] else 1)

if __name__=='__main__':main()
