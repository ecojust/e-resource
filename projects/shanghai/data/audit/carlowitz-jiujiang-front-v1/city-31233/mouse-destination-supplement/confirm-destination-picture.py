"""Read the actual corrected desktop pin image and the earlier physical receipt."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
def read(work=ROOT):
 from PIL import Image
 base=work/'desktop-pin-visual-supplement';new=base/'selected.json'
 verified=json.loads(new.read_bytes());phase=base/verified['session'];closure=phase/'closed.json';report=phase/'main-browser.json'
 def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
 assert sha(closure)==verified['close_sha256'] and sha(report)==verified['report_sha256']
 r=json.loads(report.read_bytes());c=json.loads(closure.read_bytes())
 assert c['report_sha256']==sha(report) and c['exit_code']==0 and c['cdp_closed'] and not c['remaining_chromium'] and c['observed_chromium_pid_and_starttime']
 old=work/'isolated-evidence/desktop-pin/closed.json';assert c['predecessor']['sha256']==sha(old)
 im,=r['screenshots'];f=phase/im['file'];assert im['sha256']==sha(f) and im['cameraAtRead']['assetShown'] and im['mapPixelMeasure']['measuredFraction']>.075
 assert im['cameraAtRead']['assetSHA256']==r['views'][0]['asset']['verifiedAsset']['sha256']
 with Image.open(f)as image:
  assert list(image.size)==im['pixelSize'];w,h=image.size
  sample=image.convert('RGB').crop((0,h//4,w,h*7//8)).resize((70,45))
  assert sum(max(p)<176 for p in sample.getdata())>230
 return phase,c,r,im
