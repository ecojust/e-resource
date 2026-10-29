"""Discover factual Shanghai heritage register entries. No images are downloaded.
Requires beautifulsoup4. Responses remain in --cache, outside the repository.
Writes a discovery snapshot only; review and merge without replacing completion
states. The UTC date denotes snapshot creation when reading an offline cache.
Only 5th batch official list is required to be readable; earlier unavailable
archives are explicitly recorded. Wikipedia photo links remain unreviewed.
"""
import argparse,concurrent.futures,urllib.request,hashlib,json,re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
p=argparse.ArgumentParser()
p.add_argument('--cache',type=Path,default=Path('/tmp/shanghai-heritage-discovery'))
p.add_argument('--output',type=Path,required=True)
p.add_argument('--offline',action='store_true',help='Parse saved raw responses and fetch metadata without network')
a=p.parse_args();cache=a.cache;cache.mkdir(parents=True,exist_ok=True)
wiki='https://zh.wikipedia.org/wiki/%E4%B8%8A%E6%B5%B7%E5%B8%82%E4%BC%98%E7%A7%80%E5%8E%86%E5%8F%B2%E5%BB%BA%E7%AD%91'
if not a.offline:
 urls={1:'https://web.archive.org/web/20200604140204id_/http://ghzyj.sh.gov.cn/bxzc/zsc/lsfm/lsjz/200905/t20090521_301678.htm',2:'https://web.archive.org/web/20231102060936id_/http://hd.ghzyj.sh.gov.cn/bxzc/zsc/lsfm/lsjz/200905/t20090521_301677.html',3:'https://web.archive.org/web/20200604140213id_/http://ghzyj.sh.gov.cn/bxzc/zsc/lsfm/lsjz/200905/t20090521_301676.htm',4:'https://web.archive.org/web/20200604140213id_/http://ghzyj.sh.gov.cn/bxzc/zsc/lsfm/lsjz/200905/t20090521_301675.htm',5:'https://web.archive.org/web/20190524082636id_/http://ghzyj.sh.gov.cn/gsgg/qtgg/201509/t20150922_666291.html'}
 def f(k,u):
  try:
   r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25);b=r.read();(cache/f'street-official-{k}.html').write_bytes(b);return {'batch':k,'url':u,'final_url':r.url,'status':r.status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
  except Exception as e:return {'batch':k,'url':u,'error':str(e)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:out=list(ex.map(lambda kv:f(*kv),urls.items()))
 (cache/'street-official-fetch.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 r=urllib.request.urlopen(urllib.request.Request(wiki,headers={'User-Agent':'Mozilla/5.0'}),timeout=30)
 (cache/'street-wiki.html').write_bytes(r.read())
soup=BeautifulSoup((cache/'street-wiki.html').read_bytes(),'html.parser')
revision=re.search(r'wgRevisionId":(\d+)',(cache/'street-wiki.html').read_text()).group(1)

def expanded(table):
 grid=[];spans={}
 for tr in table.find_all('tr'):
  if tr.find_parent('table') is not table:continue
  cells=tr.find_all(['td','th'],recursive=False);row=[];col=0
  def existing():
   nonlocal col
   while col in spans:
    cell,n=spans[col];row.append(cell)
    if n==1:del spans[col]
    else:spans[col]=(cell,n-1)
    col+=1
  for cell in cells:
   existing()
   for _ in range(int(cell.get('colspan',1))):
    row.append(cell)
    if int(cell.get('rowspan',1))>1:spans[col]=(cell,int(cell['rowspan'])-1)
    col+=1
  existing();grid.append(row)
 return grid

from collections import Counter
wiki_pinned='https://zh.wikipedia.org/w/index.php?title='+__import__('urllib.parse',fromlist=['quote']).quote('上海市优秀历史建筑')+'&oldid='+revision
old_district={'A':'黄浦区','B':'静安区','C':'黄浦区','D':'徐汇区','E':'黄浦区','F':'虹口区','G':'杨浦区','H':'静安区','M':'长宁区','N':'普陀区','O':'浦东新区','P':'闵行区','Q':'宝山区','R':'崇明区'}
new_district={'HP':'黄浦区','JA':'静安区','ZB':'静安区','HK':'虹口区','YP':'杨浦区','PT':'普陀区','CN':'长宁区','XH':'徐汇区','BS':'宝山区','JD':'嘉定区','PD':'浦东新区','JS':'金山区','SJ':'松江区','QP':'青浦区','FX':'奉贤区','CM':'崇明区'}
fetch=json.load((cache/'street-official-fetch.json').open())
def uniq(vals):return list(dict.fromkeys(v for v in vals if v))
def celltext(c):return re.sub(r'\s+',' ',c.get_text(' ',strip=True))
def field(row,header,name):return ' / '.join(uniq(celltext(row[i]) for i,h in enumerate(header) if h==name and i<len(row)))
def details(row):
 cells=list(dict.fromkeys(row));links=[];photos=[]
 for c in cells:
  for a in c.find_all('a',href=True):
   u=urljoin('https://zh.wikipedia.org',a['href'])
   if a.find('img') or '/wiki/File:' in u or '/wiki/文件:' in u:photos.append(u)
   elif '/wiki/' in u and not 'action=edit' in u and not 'cite_note' in u:links.append(u)
 return uniq(links),uniq(photos)
records=[]
for k in range(1,5):
 rows=expanded(soup.select('table')[k]);header=[celltext(c) for c in rows[0]];groups={}
 for row in rows[1:]:
  if row and celltext(row[0]).isdigit():groups.setdefault(int(celltext(row[0])),[]).append(row)
 for n,group in groups.items():
  subs=[];alllinks=[];allphotos=[]
  for row in group:
   vals={h:field(row,header,h) for h in uniq(header)}
   links,photos=details(row);alllinks+=links;allphotos+=photos
   subs.append({key:val for key,val in vals.items() if key not in ['照片','序号'] and val})
  code=field(group[0],header,'编号')
  names=uniq(sub.get('落成时名称') or sub.get('原名称/原使用单位','') for sub in subs)
  current=uniq(sub.get('现在名称') or sub.get('公布时名称/使用单位') or sub.get('现名称/现使用单位','') for sub in subs)
  addresses=uniq(sub.get('地址','') for sub in subs)
  district=field(group[0],header,'所在区') if k==1 else old_district[re.search('[A-Z]',code).group()]
  district=district.replace('卢湾区','黄浦区').replace('南市区','黄浦区').replace('闸北区','静安区').replace('崇明县','崇明区')
  records.append({'id':f'sh-historic-b{k}-{n:03}','batch':k,'list_number':n,'official_code':code or None,'name':' / '.join(names),'listed_current_name':' / '.join(current),'district':district,'addresses':addresses,'status':'todo-source-review','source_kind':'secondary-register-text','source_url':wiki_pinned+['','#第一批','#第二批','#第三批','#第四批'][k],'official_source_url':fetch[k-1]['url'],'official_source_fetch_status':'unavailable: archive challenge (202)' if fetch[k-1].get('status')==202 else 'not parsed; inspect source fetch metadata','record_scope':'listed-place; may contain multiple buildings; split before modeling','subentries':subs,'article_links':uniq(alllinks),'photo_page_links':uniq(allphotos),'photo_review_status':'indexed-not-reviewed' if allphotos else 'not-indexed','demolition_or_condition_note': '原表含已拆或拆除记载，需历史时点核验' if any(re.search('已拆|拆除',str(v)) for v in subs) else None})
# Parse the independently retrieved official 5th batch list (426 places).
wiki_fifth={}
for table in soup.select('table')[5:21]:
 rows=expanded(table)
 for row in rows[1:]:
  if not row:continue
  code=celltext(row[0])
  if not re.fullmatch(r'[A-Z]{2}-J-\d{3}-V',code):continue
  links,photos=details(row)
  wiki_fifth.setdefault(code,{'links':[],'photos':[]});wiki_fifth[code]['links']+=links;wiki_fifth[code]['photos']+=photos
os=BeautifulSoup((cache/'street-official-5.html').read_bytes(),'html.parser');seen=set()
for table in os.select('table'):
 for row in expanded(table):
  vals=[re.sub(r'\s+','',celltext(c)) for c in row]
  if len(vals)<3 or not re.fullmatch(r'[A-Z]{2}-J-\d{3}-V',vals[0]):continue
  code,name,address=vals[:3];assert code not in seen;seen.add(code);w=wiki_fifth.get(code,{'links':[],'photos':[]})
  records.append({'id':'sh-historic-b5-'+code.lower(),'batch':5,'list_number':len(seen),'official_code':code,'name':name,'listed_current_name':name,'district':new_district[code[:2]],'addresses':[address],'status':'todo-source-review','source_kind':'official-register-text','source_url':fetch[4]['url'],'secondary_source_url':wiki_pinned+'#第五批','official_source_fetch_status':'verified-HTTP-200-list','record_scope':'listed-place; may contain multiple buildings; split before modeling','article_links':uniq(w['links']),'photo_page_links':uniq(w['photos']),'photo_review_status':'indexed-not-reviewed' if w['photos'] else 'not-indexed','demolition_or_condition_note':None})
assert len(records)==1058,(len(records),len(seen));assert len({r['id'] for r in records})==1058
out={'schema':'shanghai-reference-discovery-v1','retrieved_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).date().isoformat(),'scope':'Five heritage registers; 1058 listed places, not all city streets, not 1058 individual buildings and not model-ready acceptance. 632 records parsed from secondary Wikipedia register; 426 parsed from retrieved official list. Article/image links indexed but not individually verified.','attribution':{'secondary':'Wikipedia contributors, 上海市优秀历史建筑, revision '+revision,'secondary_license':'CC BY-SA 4.0 (page footer); derived factual register fields with attribution, no images or narrative copied','secondary_url':wiki_pinned,'official':'上海市规划和国土资源管理局：上海市第五批优秀历史建筑名单','official_url':fetch[4]['url'],'redistributed':'Factual name/address/list identifiers only; no whole HTML or photographs'},'sources':[{'url':wiki_pinned,'bytes':(cache/'street-wiki.html').stat().st_size,'sha256':hashlib.sha256((cache/'street-wiki.html').read_bytes()).hexdigest(),'status':'HTTP-200','retrieved_url':wiki,'revision_id_from_page':int(revision)}]+fetch,'counts':{'listed_places':len(records),'districts':dict(Counter(r['district'] for r in records)),'batches':dict(Counter(r['batch'] for r in records)),'places_with_indexed_photo_links':sum(bool(r['photo_page_links']) for r in records),'places_with_condition_note':sum(bool(r['demolition_or_condition_note']) for r in records)},'records':records}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out['counts'],ensure_ascii=False,indent=2))
