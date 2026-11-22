"""Test the cut, recesses, pale ribs and silhouette of the exported crown."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parents[2]/'source/precise/hongkou-tanggu-road-apartment-dated-crown/measurements'))
from check_crown_masonry import check
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('models',type=Path,nargs=3);parser.add_argument('output',type=Path)
    a=parser.parse_args();reports={role:check(path)for role,path in zip(('raw','full','lod'),a.models)}
    a.output.write_text(json.dumps(reports,indent=2,ensure_ascii=False)+'\n')
    if not all(r['passed']for r in reports.values()):raise SystemExit(1)
