"""Observe Chromium descendants by kernel process lineage, including a browser without an explicit profile argument."""
from pathlib import Path

def chrome_descendants(root_pid):
    root_pid=int(root_pid)
    children={}
    chromes={}
    tagged={}
    for statfile in Path('/proc').glob('[0-9]*/stat'):
        try:
            pid=int(statfile.parent.name)
            fields=statfile.read_text().rsplit(')',1)[1].split()
            if fields[0] in ('X','Z'):
                continue
            children.setdefault(int(fields[1]),[]).append(pid)
            if (statfile.parent/'comm').read_text().strip() not in ('chrome','chromium'):
                continue
            birth=int(fields[19])
            chromes[pid]=birth
            token=('PICARDIE_208_AUDIT_PARENT='+str(root_pid)).encode()
            if token in (statfile.parent/'environ').read_bytes().split(bytes([0])):
                tagged[pid]=birth
        except (OSError,ValueError,IndexError):
            continue
    pending=[root_pid]
    visited=set()
    while pending:
        pid=pending.pop()
        if pid in visited:
            continue
        visited.add(pid)
        pending.extend(children.get(pid,[]))
    return {**{pid:chromes[pid] for pid in visited if pid in chromes},**tagged}

def still_alive(observed):
    result=[]
    for pid,start in observed.items():
        try:stat=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
        except (FileNotFoundError,ProcessLookupError):continue
        if int(stat[19])==start and stat[0] not in ('X','Z'):result.append(pid)
    return result
