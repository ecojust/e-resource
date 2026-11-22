from pathlib import Path
import os,time
f=Path('/run/codex-docker/user/shi-tongren305/pilot/geometry-input.json')
while not f.is_file():time.sleep(1)
os.execl('/bin/bash','bash','/tmp/shanghai-main-240/wait-239.sh')
