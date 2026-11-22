from pathlib import Path
from hashlib import file_digest
from PIL import Image,ImageChops

def sha(path):
    with Path(path).open('rb') as stream:return file_digest(stream,'sha256').hexdigest()

def saved_files(directory, rows):
    assert len(rows)==4 and len({row['file'] for row in rows})==4
    for row in rows:
        assert row['download_event'] and row['temporary_file_read'] and row['saveAsVerified']
        rel=Path('saved')/Path(row['file']).name
        assert row['saved']==rel.as_posix()
        file=directory/rel
        assert file.is_file() and file.stat().st_size==row['bytes'] and sha(file)==row['sha256']

def captured_phase(directory, data):
    assert sha(directory/'actual-driver.cjs')==data['script_sha256']
    cal=data['viewportCalibration']
    rect=tuple(cal[k] for k in ('x','y','width','height'))
    left,top,width,height=rect
    assert min(left,top)>=0 and min(width,height)>0
    probe=directory/cal['file']
    assert sha(probe)==cal['sha256']
    with Image.open(probe) as input_image:
        im=input_image.convert('RGB')
        assert im.getpixel((left,top))==(207,43,171) and im.getpixel((left+width-1,top+height-1))==(31,211,93)
    screens={entry['file']:entry for entry in data['displayCaptures']}
    assert len(screens)==len(data['captures']) and set(screens)=={c['file'] for c in data['captures']}
    for capture in data['captures']:
        item=screens[capture['file']]
        assert tuple(item['rect'])==rect and item['sha256']==capture['sha256']==sha(directory/capture['file'])
        assert sha(directory/item['root'])==item['root_sha256']
        with Image.open(directory/item['root']) as full, Image.open(directory/item['file']) as cut:
            assert cut.size==(width,height)
            crop=full.convert('RGB').crop((left,top,left+width,top+height))
            assert ImageChops.difference(crop,cut.convert('RGB')).getbbox() is None
    if data['section']=='desktop':saved_files(directory,data['saved_downloads'])
