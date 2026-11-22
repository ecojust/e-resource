"""Fetch a study copy of the district photograph and verify the photographed version."""
import argparse,hashlib,io
from pathlib import Path
import requests
from PIL import Image

url='https://www.shcn.gov.cn:443/cncms/gtj/20101231153446218412637.jpg'
page='https://www.shcn.gov.cn/col7698/20211207/1152633.html'
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);args=p.parse_args()
    resp=requests.get(url,headers={'User-Agent':'Mozilla/5.0','Referer':page},timeout=30);resp.raise_for_status()
    raw=resp.content
    assert len(raw)==68314 and hashlib.sha256(raw).hexdigest()=='f56bbaf9906f0c680e0bc55be216c207796277a9d51f1bf212bf7be7a163551e'
    assert Image.open(io.BytesIO(raw)).size==(608,686)
    if args.output.exists():
        assert args.output.read_bytes()==raw
    else:
        with args.output.open('xb')as f:f.write(raw)
