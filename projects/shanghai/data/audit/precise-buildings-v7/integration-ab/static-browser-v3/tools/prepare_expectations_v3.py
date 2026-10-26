#!/usr/bin/env python3
"""Freeze actual candidate assets plus one root-reviewed normalized oblique.
This prepares camera expectations only, never model/catalog acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import json
import prepare_expectations as original
from browser_expectations import require, walk_pose

TARGET='qingpu-beidajie-208-212'
def digest(path):
    body=path.read_bytes();return {'file':str(path),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}

def reviewed_view(review_path):
    review=json.loads(review_path.read_bytes());folder=review_path.parent
    require(review.get('schema')=='root-diagnostic-camera-pose-review-v1' and review.get('reviewer')=='root'
      and review.get('selection_passed') is True and review.get('oblique_approved') is True,'Actual root camera selection is required')
    diagnostic_path=folder/'diagnosis.json';diagnostic=json.loads(diagnostic_path.read_bytes())
    require(digest(diagnostic_path)['sha256']==review.get('diagnosis_sha256') and diagnostic.get('completed') is True,'Diagnostic evidence changed or did not complete')
    viewed={}
    for item in review.get('actually_viewed',[]):
        name=item.get('file');require(isinstance(name,str) and Path(name).name==name and name.endswith('.png'),'Invalid viewed image path')
        actual=digest(folder/name);require(item.get('actually_viewed') is True and all(item.get(k)==actual[k] for k in ['bytes','sha256']),'Root-viewed image bytes changed')
        viewed[name]=item
    captures={row['name']:row for row in diagnostic['captures']}
    selected='walk-'+review['selected_walk_id'];require(selected in captures and selected+'.png' in viewed,'Selected walk has no actual viewed capture')
    row=captures['reviewed-oblique'];require(row['image'] in viewed,'Oblique was not actually viewed')
    request=review['reviewed_oblique'];actual=row['state']['camera']['eye']
    require(request['from']==actual,'Formal eye must match the actual reviewed, possibly clamped camera')
    require(request['to']==row['requested']['to'] and request['fov']==row['requested']['fov'],'Reviewed target/FOV differs from actual diagnostic operation')
    pose=captures[selected]['requested'];require(review['selected_walk']=={k:pose[k] for k in ['walkStart','bearing']},'Selected walking pose differs from captured operation')
    return {'scope':'root-reviewed-actual-camera-v1','request':request,'evidence':{
      'diagnostic_sha256':digest(diagnostic_path)['sha256'],
      'visual_review_sha256':digest(review_path)['sha256'],
      'image_sha256':viewed[row['image']]['sha256'],
      'visual_review_file':str(review_path),'image_file':row['image'],
      'limitations':['Close oblique intentionally crops the left edge and lower base.','Camera selection does not grant model/catalog acceptance.']}},review

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True);p.add_argument('--visual-review',type=Path,required=True)
    p.add_argument('--targets',nargs='+',required=True);p.add_argument('--expected-record-count',type=int,required=True)
    p.add_argument('--allow-asset-root',type=Path,action='append',default=[]);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();require(TARGET in a.targets,'The reviewed B target must be selected')
    view,review=reviewed_view(a.visual_review)
    nav=a.project/'data/landmarks.json';registry=a.project/'data/precise-buildings-v6.json'
    record=next(row for row in json.loads(nav.read_bytes()) if row['id']==TARGET)
    start,bearing=walk_pose(record);require({'walkStart':start,'bearing':bearing}==review['selected_walk'],'Actual installed navigation differs from selected root pose')
    require(not a.output.exists(),'Refuse existing frozen output')
    temporary=a.output.with_suffix(a.output.suffix+'.base-only');require(not temporary.exists(),'Refuse existing temporary profile')
    try:
        result=original.prepare(a.project,nav,registry,temporary,a.targets,a.expected_record_count,a.allow_asset_root)
        actual=result['targets'][TARGET]['record']
        require({'walkStart':actual['walkStart'],'bearing':actual['bearing']}==review['selected_walk'],'Installed navigation changed during asset verification')
        result['targets'][TARGET]['reviewed_oblique']=view
        result['camera_review']=digest(a.visual_review)
        result['required_runner']='browser-next-v3.py'
        staged=a.output.with_suffix(a.output.suffix+'.tmp');require(not staged.exists(),'Refuse existing output temporary')
        staged.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');staged.replace(a.output)
    finally:temporary.unlink(missing_ok=True)
    print(json.dumps({'preparation_passed':True,'model_acceptance_claimed':False,'output':digest(a.output),
      'targets':a.targets,'navigation_count':a.expected_record_count,'preserved_neighbors':len(result['registry']['derived_selected_neighbors'])},indent=2))

if __name__=='__main__':main()
