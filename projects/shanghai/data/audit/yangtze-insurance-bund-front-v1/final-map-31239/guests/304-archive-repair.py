"""Finish the original archive-only portion after its mkdir failed, using the recorded real browser process."""
from pathlib import Path
from types import SimpleNamespace
import sys, os, shutil, textwrap, json, hashlib, datetime
from datetime import timezone

home=Path('/tmp/soong304')
here=home/'mapping/handoff'
sys.path.insert(0,str(here))
import receipts as checks

digest=checks.digest
read=checks.read
first=home/'distant-304-ordinary-result.json'
failed=read(first)
assert failed['exit_code']==1 and failed['all_children_exited'] and not failed['remaining_children']
attempt=Path(failed['attempts'][0])
common=read(attempt/'process-exit.json')
assert common['exit_code']==0 and common['wrapper_closed'] and not common['remaining'] and digest(attempt/'run.log')==common['log_sha256']
driver=here/'run-phase.py'
assert digest(driver)=='31cad3cea2363379c48bf5dc2193762d6fa200388c7ed2f6a8439e7595a31815'
assert not Path('/proc',str(common['wrapper_pid'])).exists()
children={int(pid):name for pid,name in common['observed_processes'].items()}
import psutil
for pid in children:
    try:
        current=psutil.Process(pid)
        assert current.create_time()!=common['observed_process_births'][str(pid)] or current.status() in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD)
    except psutil.NoSuchProcess:
        pass
assert 'Errno 28' in (here/'viewer-20261122T065719486148Z.log').read_text()
grant=read(here/'viewer-window.json')
assert checks.prereqs('viewer',Path(grant['receipt']))==grant
def publish(file,target):
    if not target.is_file():
        try:os.link(file,target)
        except OSError:shutil.copyfile(file,target)
    assert digest(file)==digest(target)

script=driver.read_text()
tail=textwrap.dedent(script[script.index("    done=read(ASSETS/'manifest.json')"):])
namespace={name:getattr(checks,name) for name in ['ASSETS','AUDIT','HERE','ID','PROJECT','WORK','digest','read','write']}
namespace.update(kind='viewer',grant=grant,ref=read(Path(read(here/'dispatch-contract.json')['accepted_manifest']))['assets'],
                 attempt=attempt,common=common,children=children,child=SimpleNamespace(pid=common['wrapper_pid']),
                 publish=publish,env={'MODEL_BASE_URL':'http://127.0.0.1:31304/'})
exec(compile(tail,str(driver)+' [original archive checks only]','exec'),namespace)
actual=home/'viewer-closed.json';close=checks.completed_viewer(actual,304)
receipt=home/'distant-304-archive-recovered.json'
info={'order':304,'host':239,'passed':True,'original_deferral_sha256':failed['original_deferral_sha256'],'host_sha256':failed['host_sha256'],
      'host_report_sha256':failed['host_report_sha256'],'first_wrapper_exit':1,'original_wrapper_result_sha256':digest(first),'physical_browser_exit':0,
      'process_exit_sha256':digest(attempt/'process-exit.json'),'original_program_sha256':digest(driver),'archive_repair_sha256':digest(Path(__file__)),
      'physical_sha256':digest(actual),'report_sha256':close['report_sha256'],'views':6,'downloads':read(Path(close['report']))['downloads'],
      'new_browser_started':False,'all_children_exited':True,'remaining_children':[]}
checks.write(receipt,info)
print(digest(actual),digest(receipt))
