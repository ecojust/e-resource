"""Verify the normal front and oblique poses on desktop and touch devices and compare actual canvas pixels."""
from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np

def verify(audit,order,names):
    assert order==257
    root=Path(audit);prefix='city-31257/front-and-oblique'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    read=lambda p:json.loads(p.read_bytes())
    ledger=root/prefix/'physical.json';assert sha(ledger)=='141f0867ad023b1b6a523245cf86b3d6d46e47e6cc1c5cc7c79dd7bbc881dbd5'
    x=read(ledger);keep={prefix+'/physical.json'}
    for filename,expected in x['files'].items():
        assert Path(filename).name==filename
        p=root/prefix/filename;assert sha(p)==expected['sha256'] and p.stat().st_size==expected['bytes'];keep.add(prefix+'/'+filename)
    for device,pointer in (('desktop','mouse'),('phone','touch')):
        closed=read(root/prefix/(device+'-closed.json'));r=read(root/prefix/(device+'-viewer.json'))
        assert closed['exit_code']==0 and closed['remaining']==[] and closed['node_closed'] and closed['descendants'] and r['completed'] and r['browser_closed']
        assert closed['report_sha256']==sha(root/prefix/(device+'-viewer.json')) and closed['log_sha256']==sha(root/prefix/(device+'-log.txt'))
        assert r['port']==31257 and r['route']=='qianxin-six-arches-history.html' and r['id']=='huangpu-qianxin-building-historic-front'
        assert r['driver_sha256']==sha(root/prefix/'normal-two-views.cjs') and not r['errors']
        assert [(i['view'],i['trusted'],i['device'])for i in r['inputs']]==[('front',True,pointer),('oblique',True,pointer)]
        two=[]
        for cap in r['captures']:
            p=root/prefix/cap['file'];assert sha(p)==cap['sha256'] and p.stat().st_size==cap['bytes']
            x0,y,w,h=cap['canvas_rect']
            with Image.open(p) as im:two.append(np.asarray(im.convert('RGB').crop((x0,y,x0+w,y+h))))
        assert two[0].shape==two[1].shape
        changed=int((two[0]!=two[1]).any(axis=2).sum())
        assert changed==r['display_difference']['changed']>1000 and w*h==r['display_difference']['pixels']
    assert keep<=set(names)
    return keep
