"""Inspect the three actual exported garden-front meshes."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parents[2]/'source/precise/hongkou-shanyin-209-brick-arched-front/measurements'))
from check_garden_front import check

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('models',type=Path,nargs=3);p.add_argument('output',type=Path);a=p.parse_args()
    report={role:check(path) for role,path in zip(('raw','full','lod'),a.models)}
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if not all(row['passed'] for row in report.values()):raise SystemExit(1)
