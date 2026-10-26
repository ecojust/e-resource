#!/usr/bin/env python3
"""APIRequestContext preflight only: never creates a browser or browser page."""
import asyncio,datetime,hashlib,importlib.util,json
from pathlib import Path
from playwright.async_api import async_playwright
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('catalog_proxy_qa',HERE/'browser-catalog.py');qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
async def main():
 registry=HERE.parent/'extracted/shanghai/data/precise-buildings-v6.json'
 descriptor=json.loads(registry.read_text())['ordinary_catalog']
 proxy,safe=qa.environment_proxy()
 report={'schema':'launcher-proxy-api-preflight-v1','passed':False,'browser_started':False,'browser_page_created':False,
  'network':safe,'url':descriptor['file'],'expected_bytes':descriptor['bytes'],'expected_sha256':descriptor['sha256'],
  'registry_sha256':hashlib.sha256(registry.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256((HERE/'browser-catalog.py').read_bytes()).hexdigest()}
 try:
  async with async_playwright() as p:
   context=await p.request.new_context(proxy=proxy,timeout=30000)
   try:
    response=await context.get(descriptor['file']);body=await response.body()
    report.update(status=response.status,actual_bytes=len(body),actual_sha256=hashlib.sha256(body).hexdigest())
    qa.require(response.status==200,'Actual remote catalog did not return HTTP 200')
    qa.require(len(body)==descriptor['bytes'] and report['actual_sha256']==descriptor['sha256'],'Remote catalog bytes/SHA differ from extracted launcher')
    # The same explicit bypass must leave the actual extracted localhost server reachable.
    local='http://127.0.0.1:8874/shanghai_expansion/building-by-building-v6/next/launcher-release/extracted/shanghai/data/precise-buildings-v6.json'
    res=await context.get(local);raw=await res.body()
    report['localhost']={'url':local,'status':res.status,'actual_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    qa.require(res.status==200 and raw==registry.read_bytes(),'Proxy bypass did not reach exact local launcher registry')
    report['passed']=True
   finally:await context.dispose()
 except Exception as error:
  # Proxy server option contains no userinfo; redact explicit credential values
  # defensively if a transport diagnostic includes one.
  message=str(error)
  for key in ('username','password'):
   if proxy.get(key):message=message.replace(proxy[key],'[redacted]')
  report['error']={'type':type(error).__name__,'message':message}
 finally:
  report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  (HERE/'api-preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False))
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
