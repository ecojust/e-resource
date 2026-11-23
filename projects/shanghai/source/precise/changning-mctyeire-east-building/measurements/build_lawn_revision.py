"""Rebuild the original GLB or either new LOD without launching a graphics process."""
import argparse, hashlib, json, struct, sys
from pathlib import Path

S = Path(__file__).resolve().parents[1]
PROJECT = S.parents[2]
sys.path[:0] = [str(S / 'source'),str(PROJECT/'source/precise/hongkou-general-post-office/source/common')]
from build_model import META, ID
from photo_architecture import Builder
from social_hall import PALETTE, building
from lawn_return import add_lawn_return

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--lod',action='store_true')
    p.add_argument('--component',action='store_true')
    p.add_argument('--verify-previous',type=Path,help='Read metadata from the fixed original GLB and exactly rebuild its complete historic binary.')
    args=p.parse_args()
    b=Builder(PALETTE)
    (add_lawn_return if args.component else building)(b,args.lod)
    metadata=dict(META)
    if args.verify_previous:
        if args.component: p.error('The previous issue contains the main facade only.')
        keep = next(i for i,part in enumerate(b.parts) if part['label'].startswith('southeast lawn return/'))
        b.parts = b.parts[:keep]
        raw = args.verify_previous.read_bytes()
        json_size = struct.unpack_from('<I',raw,12)[0]
        metadata=json.loads(raw[20:20+json_size])['extras']
    stats = b.save(args.output,metadata)
    if args.verify_previous and stats['sha256']!=hashlib.sha256(raw).hexdigest():
        raise SystemExit('The existing geometry did not reproduce exactly')
    print(json.dumps({k:stats[k] for k in ('sha256','bytes','parts','triangles')}))
if __name__=='__main__':main()
