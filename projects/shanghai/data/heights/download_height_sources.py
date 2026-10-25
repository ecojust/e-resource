"""Download verified public CMAB/GHSL archives into an ignored local cache.

No network or filesystem mutation occurs on import or --help. CNBH has a
separate byte-range downloader in alternatives/download_cnbh_ranges.py.
These upstream archives can exceed GitHub's per-file limit; do not commit them.
"""
from pathlib import Path
import argparse,hashlib,json,urllib.request,zipfile

HERE=Path(__file__).resolve().parent
BASE='https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_H_GLOBE_R2023A/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_4326_3ss/V1-0/tiles/'
def sources():
    entries={'cmab':{'url':'https://ndownloader.figshare.com/files/51075296','name':'shanghai.zip','bytes':335640089,'md5':'8e821a251f97e1de78511a5934e9c964'}}
    report=json.loads((HERE/'ghsl_full_extent_validation.json').read_text())
    for source in report['source_archives']:
        key='ghsl-west' if '_C30.' in source['name'] else 'ghsl-east'
        entries[key]={**source,'url':BASE+source['name']}
    return entries

def verify(path,source):
    if path.stat().st_size != source['bytes']:raise ValueError(f'Unexpected source length: {path}')
    for kind in ('md5','sha256'):
        if kind in source:
            with path.open('rb') as stream:actual=hashlib.file_digest(stream,kind).hexdigest()
            if actual!=source[kind]:raise ValueError(f'{kind} checksum mismatch: {path}')
    with zipfile.ZipFile(path) as archive:
        bad=archive.testzip()
        if bad:raise ValueError(f'ZIP CRC failed: {bad}')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',choices=['cmab','ghsl-east','ghsl-west','all'])
    parser.add_argument('--cache-dir',type=Path,default=HERE/'.cache/height-sources')
    parser.add_argument('--force',action='store_true',help='Redownload existing files after verification failure')
    args=parser.parse_args();entries=sources();args.cache_dir.mkdir(parents=True,exist_ok=True)
    keys=list(entries) if args.source=='all' else [args.source]
    for key in keys:
        source=entries[key];target=args.cache_dir/source['name']
        if target.exists():
            try:verify(target,source);print('Verified existing',target);continue
            except (ValueError,zipfile.BadZipFile):
                if not args.force:raise
        temporary=target.with_suffix(target.suffix+'.partial')
        print('Downloading',source['url'],flush=True)
        with urllib.request.urlopen(source['url'],timeout=90) as response,temporary.open('wb') as output:
            while block:=response.read(1024*1024):output.write(block)
        verify(temporary,source);temporary.replace(target)
        print('Verified',target,source['bytes'],'bytes',flush=True)

if __name__=='__main__':main()
