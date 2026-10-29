"""Index Shanghai road-name research leads; no photographs are downloaded.

Write a discovery snapshot for review, then merge it into the model queue.
This script never reads or changes model completion states. --offline uses
raw responses in --cache without network; timestamps denote snapshot creation.
Requires beautifulsoup4 and opencc-python-reimplemented.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import quote,unquote,urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import json,re,hashlib
from opencc import OpenCC
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--cache',type=Path,default=Path('/tmp/shanghai-road-discovery'))
p.add_argument('--output',type=Path,required=True)
p.add_argument('--offline',action='store_true',help='Read saved source responses without network access')
args=p.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
cc=OpenCC("t2s")
base='https://zh.wikipedia.org'
queue=['Category:上海道路','Category:上海街道'];seen=set();sources=[];roads={}

def fetch(title):
 path=args.cache/('roads-'+title.replace(':','-').replace('/','_')+'.html')
 u=base+'/wiki/'+quote(title)
 try:
  if args.offline:b=path.read_bytes()
  else:
   r=urlopen(Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20);b=r.read();path.write_bytes(b)
  return title,u,b,None
 except Exception as e:return title,u,None,str(e)

while queue:
 current=list(dict.fromkeys(x for x in queue if x not in seen));queue=[];seen.update(current)
 with ThreadPoolExecutor(max_workers=6) as ex:results=list(ex.map(fetch,current))
 for title,u,b,error in results:
  if error:sources.append({'title':title,'url':u,'error':error});continue
  s=BeautifulSoup(b,'html.parser');sources.append({'title':title,'url':u,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
  district=re.search('(黄浦|徐汇|长宁|静安|普陀|虹口|杨浦|闵行|宝山|嘉定|浦东新|金山|松江|青浦|奉贤|崇明)区',title)
  district=district.group() if district else None
  for a in s.select('#mw-pages .mw-category a'):
   name=a.get_text(' ',strip=True);href=a.get('href','')
   if re.search(r'(?:路|街|大道|公路|高速|隧道|通道|弄)(?:\s*[（(][^）)]*[）)])?$',name) and not name.startswith(('Category:','Template:','User:')):
    article=urljoin(base,href);row=roads.setdefault(article,{'name':name,'name_simplified':cc.convert(name),'article_url':article,'category_sources':[],'districts_indexed':[],'reference_status':'article-link-indexed-not-reviewed','model_status':'research-needed'})
    row['category_sources'].append(u)
    if district and district not in row['districts_indexed']:row['districts_indexed'].append(district)
  for a in s.select('#mw-subcategories .CategoryTreeItem a'):
   h=a.get('href','');st=unquote(h.split('/wiki/')[-1])
   if st.startswith('Category:') and not any(z in st for z in ['模板','小作品']):queue.append(st)
  # Count visible and detect unvisited pagination instead of assuming complete.
  if s.select_one('#mw-pages'):
   for a in s.select('#mw-pages > a'):
    if '下一页' in a.get_text():sources[-1]['unfollowed_next_page']=urljoin(base,a.get('href',''))

# Fetch the explicit list too: it must not depend on a previous manual request.
list_title,list_url,list_bytes,list_error=fetch('上海市道路列表')
if list_error:
 raise RuntimeError('Cannot read explicit road list: '+list_error)
s=BeautifulSoup(list_bytes,'html.parser');main=s.select_one('.mw-parser-output')
if main is None:raise RuntimeError('Road list response has no article body')
sources.append({'title':list_title,'url':list_url,'sha256':hashlib.sha256(list_bytes).hexdigest(),'bytes':len(list_bytes)})
for ul in main.find_all('ul',recursive=False):
 for li in ul.find_all('li',recursive=False):
  name=re.match('[\u4e00-\u9fff]+',li.get_text(' ',strip=True))
  if not name:continue
  name=name.group();same=next((x for x in roads.values() if cc.convert(re.sub(r'\s*[（(].*','',x['name']))==cc.convert(name)),None)
  if same:
   same.setdefault('list_sources',[]).append(list_url);continue
  a=next((a for a in li.select('a') if a.get_text(' ',strip=True)==name),None)
  article=urljoin(base,a['href']) if a else None
  key=article or 'name:'+name
  roads[key]={'name':name,'name_simplified':cc.convert(name),'article_url':article,'list_sources':[list_url],'districts_indexed':[],'reference_status':'list-name-indexed-not-reviewed','model_status':'research-needed'}
rows=sorted(roads.values(),key=lambda r:(r['districts_indexed'] or ['待核实'],r['name']))
out={'schema':'shanghai-road-reference-discovery-v1','accessed_utc':datetime.now(timezone.utc).date().isoformat(),'scope':'Named roads from Wikipedia road list and reachable road categories; not a complete city road census, not a building/photo reference acceptance','license_note':'Factual names/links indexed from Wikipedia; source pages CC BY-SA, image permissions require per-file verification. No images copied.','limitations':['Wikipedia explicitly marks road list incomplete','Category membership is editorial, may include historical roads or multiple districts','Article links indexed only; building identities/photographs must be inspected before modeling','No road geometry, authoritative current district assignment or all-city coverage claimed'],'sources':sources,'road_count':len(rows),'roads':rows}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'roads':len(rows),'source_pages':len(sources),'failed':[s for s in sources if s.get('error')],'pending_pages':[s for s in sources if s.get('unfollowed_next_page')]},ensure_ascii=False,indent=2))
