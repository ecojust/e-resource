"""Check the immutable height-data lock without loading GIS dependencies."""
from pathlib import Path
import argparse,hashlib,json

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--lock',type=Path)
    args=parser.parse_args();lock=args.lock or args.root/'height_sources_lock.json'
    manifest=json.loads(lock.read_text());failures=[];total=0
    for item in manifest['files']:
        path=args.root/item['path']
        if not path.is_file():failures.append({'path':item['path'],'error':'missing'});continue
        total+=path.stat().st_size
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=item['sha256'] or path.stat().st_size!=item['bytes']:
            failures.append({'path':item['path'],'error':'checksum or size mismatch'})
    report={'sampler_version':manifest['sampler_version'],'files':len(manifest['files']),'bytes':total,'failures':failures}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
