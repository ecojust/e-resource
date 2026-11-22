"""Check the delivered original and the decoded near and distant meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("project","source","packaged","controls","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    here=Path(__file__).parent
    photo_review=runpy.run_path(here/"check-entrance-details.py")["measure"]
    rebate_review=runpy.run_path(here/"check-pane-seats.py")["review"]
    observations=json.loads(args.controls.read_bytes())
    results={}
    for role,decoded in [("raw","raw"),("full","decoded-full"),("lod","decoded-lod")]:
        mesh=args.packaged/(decoded+".glb")
        entry=photo_review(args.project,args.source,mesh,observations,False)
        entry["rebates"]=rebate_review(args.project,args.source,mesh)["views"]
        with (args.packaged/(role+".glb")).open("rb") as stream:
            entry["delivered_asset_sha256"]=hashlib.file_digest(stream,"sha256").hexdigest()
        results[role]=entry
        print(role,entry["passed"],entry["count"],[(k,v["passed"],v["samples"])for k,v in entry["rebates"].items()],flush=True)
    report={"photograph_sha256":observations["photograph_sha256"],"roles":results}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    for role,entry in results.items():
        if entry["passed"]!=111 or entry["count"]!=111:
            raise ValueError(f"{role} failed a photographed material or opening")
        if len(entry["grooves"])!=20 or min(g["source_dark_groove_deeper_by_m"]for g in entry["grooves"])<=0:
            raise ValueError(f"{role} failed a measured stone groove")
        if any(v["passed"]!=346 or v["samples"]!=346 for v in entry["rebates"].values()):
            raise ValueError(f"{role} has an open or recessed glazing joint")


if __name__=="__main__":
    main()
