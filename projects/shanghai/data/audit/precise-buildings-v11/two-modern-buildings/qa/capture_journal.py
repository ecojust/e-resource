"""Persist returned observations and completed screenshots before assertions."""
from pathlib import Path
import hashlib

def begin_capture(report,row,save):
    row['capture_completed']=False
    report['captures'].append(row)
    save()
    return row

def observation(row,key,value,save):
    if key not in ('osm_capture_before','osm_capture_after'):
        raise ValueError('Unexpected observation phase')
    row[key]=value
    save()
    return value

def completed_screenshot(row,path,save):
    path=Path(path)
    with path.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    row['image']=path.name
    row['screenshot_complete']={'file':path.name,'bytes':path.stat().st_size,'sha256':digest}
    save()

def finish_capture(row,save):
    if not all(isinstance(row.get(k),dict) and row[k].get('passed') is True for k in ('osm_capture_before','osm_capture_after')):
        raise ValueError('Both actual observations must pass before capture completion')
    if row.get('image') and not row.get('screenshot_complete'):
        raise ValueError('Completed screenshot identity missing')
    row['capture_completed']=True
    save()
