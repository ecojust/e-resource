"""Copy the actual bytes of a retained evidence file, resolving its storage link first."""
import hashlib,os,shutil,tempfile
from pathlib import Path
def sha(p):
 with p.open('rb')as s:return hashlib.file_digest(s,'sha256').hexdigest()
def copy(src,dst):
 src=Path(src)
 visited=set()
 while src.is_symlink():
  marker=(src.lstat().st_dev,src.lstat().st_ino)
  if marker in visited:raise OSError('Cyclic evidence link: '+str(src))
  visited.add(marker);source=src.readlink();src=source if source.is_absolute() else src.parent/source
 assert src.is_file(),src
 dst=Path(dst);dst.parent.mkdir(exist_ok=True,parents=True)
 if dst.exists():
  assert not dst.is_symlink() and sha(src)==sha(dst),dst
  return
 with tempfile.TemporaryDirectory(prefix='.retaining-',dir=dst.parent)as tmp:
  pending=Path(tmp)/'evidence'
  try:os.link(src,pending)
  except OSError:shutil.copyfile(src,pending)
  assert pending.stat().st_size==src.stat().st_size and sha(pending)==sha(src)
  os.replace(pending,dst)
