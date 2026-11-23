"""Keep one editable mesh in Python memory at a time while Blender builds the scene."""
import json
from pathlib import Path

class ComponentFile:
    def __init__(self,path,count):
        self.path=path
        self.count=count

    def __len__(self):
        return self.count

    def __iter__(self):
        count=0
        with self.path.open(encoding='utf-8') as stream:
            for line in stream:
                yield json.loads(line)
                count+=1
        if count!=self.count:
            raise ValueError('Incomplete editable component file')

def open_components(path):
    package=json.loads(path.read_bytes())
    if 'parts_file' in package:
        name=package['parts_file']
        if Path(name).name!=name:
            raise ValueError('Invalid component filename')
        package['parts']=ComponentFile(path.parent/name,package['part_count'])
    return package

def save_stream(source,header):
    package=json.loads(source.read_bytes())
    parts=package.pop('parts')
    target=header.with_suffix('.jsonl')
    with target.open('w',encoding='utf-8') as dst:
        for part in parts:
            dst.write(json.dumps(part,ensure_ascii=False,separators=(',',':'))+'\n')
    package.update(parts_file=target.name,part_count=len(parts))
    header.write_text(json.dumps(package,ensure_ascii=False)+'\n')

if __name__=='__main__':
    import sys
    save_stream(*(Path(arg) for arg in sys.argv[1:]))
