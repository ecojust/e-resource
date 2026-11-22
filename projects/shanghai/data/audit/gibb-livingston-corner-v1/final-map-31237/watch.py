"""Wait for the completed Gascogne Apartments city test and run the verified 237 cases in series."""
from pathlib import Path
import datetime, fcntl, hashlib, json, subprocess, time
w=Path(__file__).parent/'final-map-31237'
prior=Path('/tmp/shanghai-main-236/236-map-slot-released.json')
with (w/'gate.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    while not prior.is_file():time.sleep(4)
    with prior.open()as f:row=json.load(f)
    assert row['order']==236 and row['passed'] and row['exit_code']==0 and row['remaining_chromium']==[],row
    assert row['all_captures_visually_reviewed'] and len(row['manual_sha256'])==64 and row['reports'] and row['real_browser_process_exits'] and row['finished'],row
    (w/'prior-release.json').write_text(json.dumps({'file':str(prior),'sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'release':row},ensure_ascii=False,indent=2)+'\n')
    for script in ('sequence.py','archive.py'):
        command=subprocess.run(['python','-B',str(w/script)],cwd=w)
        if command.returncode:raise SystemExit(command.returncode)
