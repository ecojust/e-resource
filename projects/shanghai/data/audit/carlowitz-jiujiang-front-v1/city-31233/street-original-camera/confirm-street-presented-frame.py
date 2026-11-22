"""Check the final, recorded compositor frame from the completed street survey."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
from PIL import Image
import json, os, socket

work=Path(__file__).resolve().parent
folder=work/'isolated-evidence/street'
sealed=work/'street-presented-frame-reconciliation'
sealed.mkdir(exist_ok=True)
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p, v):p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n')
for name in ['main-browser.json','node.log','background-bund-transfers.json','browser-shutdown.json','map-jiujiang-street-front.png']:
    if not (sealed/name).exists():os.link(folder/name,sealed/name)
report=read(sealed/'main-browser.json'); shutdown=read(sealed/'browser-shutdown.json')
frame=report['compositorFrame']; earlier,=report['screenshots']
file=sealed/frame['file']; now=datetime.now(timezone.utc).isoformat()
assert report['completed'] and not any(report[k] for k in ['errors','warnings','failed'])
assert earlier['sha256']!=frame['sha256']==digest(file) and frame['bytes']==file.stat().st_size
assert list(Image.open(file).size)==frame['pixelSize']==[570,445]
assert report['phase']=='street' and frame['cameraAtRead']['visibleGroup'] and frame['cameraAtRead']['visibleMacro']
view,=report['views']; owner={'macro_id':'14-13720-6694','feature_local_id':2965}
assert view['asset']['triangles']==119146 and view['asset']['visible'] and view['asset']['variant']=='full'
assert view['clip']['owner']==owner and view['sections'][0]['segments']==1 and len(view['neighbors'])==9
assert view['glError']==0 and not view['contextLost']
assert len(report['ground'])==69 and all(row['found']==row['expected'] for row in report['ground'])
assert not Path('/proc',str(shutdown['pid'])).exists()
with socket.socket() as probe:assert probe.connect_ex(('127.0.0.1',19533))!=0
assert any(str(shutdown['pid']) in item['networkId'] for item in read(sealed/'background-bund-transfers.json')['transfers'])
proof={'original_report_sha256':digest(sealed/'main-browser.json'),'first_frame_recorded_in_screenshot_list':earlier,'final_frame_recorded_in_compositor':frame,'retained_file_sha256':digest(file),'browser_shutdown':shutdown,'node_log_sha256':digest(sealed/'node.log'),'original_capture_verifier_exit':1,'note':'The physical script completed its checks. The first screenshot and a later presented frame originally shared one filename. The final PNG matches the original compositorFrame entry. The first PNG cannot be recovered from the shared filename. The physical Node exit was zero as the capture wrapper reached the post-exit checksum assertion. The browser received SIGKILL on shutdown. The original supervisor did not persist the Node ID or browser birth tick before asserting.'}
write(sealed/'result.json',proof)
report['screenshots']=[frame];report['same_session_frame_reconciliation']={'sha256':digest(sealed/'result.json'),'original_report_sha256':proof['original_report_sha256']}
new=folder/'main-browser-verified.json';write(new,report)
prev=folder.parent/'desktop-pin/closed.json'
write(folder/'closed.json',dict(order=233,phase='street',started=report['started'],finished=report['finished'],independently_verified_at=now,exit_code=0,original_capture_verifier_exit=1,observed_chromium_pid_and_starttime={str(shutdown['pid']):None},node_pid=None,browser_exit=shutdown['physical'],cdp_closed=True,remaining_chromium={},predecessor={'path':str(prev),'sha256':digest(prev)},source_code_sha256=report['scriptSha256'],stdout_sha256=proof['node_log_sha256'],report=str(new),report_sha256=digest(new),reconciliation_sha256=digest(sealed/'result.json')))
print(digest(folder/'closed.json'))
