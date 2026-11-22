"""Reopen all three delivery meshes and probe the southern elevation and its roof."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
M=ROOT/'source/precise/jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements'
sys.path.insert(0,str(M))
from check_riverfront import check

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models',nargs=3,type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    reports={role:check(path)for role,path in zip(('raw','full','lod'),args.models)}
    args.output.write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
    if not all(r['passed']for r in reports.values()):raise SystemExit(1)
if __name__=='__main__':main()
