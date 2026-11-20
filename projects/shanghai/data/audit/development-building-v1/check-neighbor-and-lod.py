"""Resume the real city check at the first failed witness and verify the distant model.

The first pass retains both default screens, the close facade and the roof. This
run opens the same release, waits for the same near group and Hamilton House,
then checks both sides of the old collision boundary before the normal LOD test.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
DRIVER = '94bbc99e1ce1ee88308dcfee1514e8557275a7d74014c0e3ead8089e5f44e2e9'
BLOB = '467a2b531daaf87680d3cb2c00445630b1f88ad8'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--site', type=Path, required=True, help='Frozen projects/shanghai directory')
parser.add_argument('--url', required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
root = AUDIT.parents[2]
driver = subprocess.check_output(['git', '-C', root, 'cat-file', 'blob', BLOB])
assert hashlib.sha256(driver).hexdigest() == DRIVER
script = driver.decode()
start = script.index('      if(!desktopOnly){')
end = script.index('      result.ground=', start)
script = script[:start] + """      await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
      await closePanel();await jump(camera);await settle('full',true);
      result.previousProbe=JSON.parse(fs.readFileSync(path.join(audit,'initial-neighbor-witness/witness-review.json')));
""" + script[end:]
start = script.index("        ...neighbors.map(n=>({name:'retained neighbor '")
end = script.index(']);', start)
script = script[:start] + """        ...Object.entries(spec.neighborGround).map(([owner,position])=>({name:'retained neighbor '+owner,position,expected:'building'})),
        {name:'Hamilton original source representative point outside its solid',position:result.previousProbe.initial_xy_wgs84,expected:null}""" + script[end:]
with tempfile.TemporaryDirectory() as tmp:
    file = Path(tmp)/'resume-neighbor-and-lod.cjs'
    file.write_text(script)
    subprocess.run(['node',file,AUDIT/'map-case.json','--after-mobile'],
                   env={**os.environ,'SHANGHAI_PROJECT_ROOT':str(args.site.resolve()),
                        'MODEL_BASE_URL':args.url,'QA_OUTPUT_DIR':str(args.out.resolve())},
                   check=True)
