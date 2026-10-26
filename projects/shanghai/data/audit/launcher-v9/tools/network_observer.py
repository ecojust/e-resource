"""Passive Chromium network evidence and explicit Overture-outage injection.
No Playwright routes, fetch monkeypatch, cache control, successful response mocks,
or changes to application/network deadlines are used.
"""
from urllib.parse import urlsplit
OUTAGE_HOSTS=frozenset(('tiles.overturemaps.org','stac.overturemaps.org'))
OUTAGE_PATTERNS=['https://tiles.overturemaps.org/*','https://stac.overturemaps.org/*']
def is_outage_url(url):
    p=urlsplit(url);return p.scheme=='https' and p.netloc in OUTAGE_HOSTS

def is_expected_outage_request(url,error,force):
    return bool(force and is_outage_url(url) and error in ('inspector','net::ERR_BLOCKED_BY_CLIENT'))

def is_confirmed_cdp_outage(row):
    return bool(row.get('kind')=='injected-outage' and is_outage_url(row.get('url',''))
        and row.get('blocked_reason')=='inspector'
        and row.get('error_text') in ('','net::ERR_BLOCKED_BY_CLIENT'))

def is_expected_outage_console(message,force):
    return bool(force and message.type=='error' and 'ERR_BLOCKED_BY_CLIENT' in message.text
        and is_outage_url(message.location.get('url','')))

def install_network_observer(context,page,report,save,target_urls,force):
    session=context.new_cdp_session(page);rows={};targets=set(target_urls)
    report['target_network']=[];report['cdp_outage_failures']=[]
    report['network_fault_injection']={'method':'Chromium Network.setBlockedURLs' if force else 'none',
        'patterns':OUTAGE_PATTERNS if force else [],'playwright_routes_installed':False,
        'cache_disabled_by_qa':False,'fetch_replaced':False,'runtime_deadline_changed':False,
        'scope':'Known Overture tile/STAC service outage only. Native browser cache policy remains in effect; cache use is observed, not forced. No claim that this resolves a production network failure.'}
    def request(event):
        url=event['request']['url'];identity=event['requestId']
        if url not in targets and not (force and is_outage_url(url)):return
        row={'request_id':identity,'url':url,'request_timestamp':event.get('timestamp'),
            'wall_time':event.get('wallTime'),'kind':'target-asset' if url in targets else 'injected-outage',
            'served_from_cache_event':False,'finished':False}
        rows[identity]=row
        if row['kind']=='target-asset':report['target_network'].append(row)
    def response(event):
        row=rows.get(event['requestId'])
        if row is None:return
        r=event['response'];row.update(response_timestamp=event.get('timestamp'),status=r['status'],
            from_disk_cache=bool(r.get('fromDiskCache')),from_prefetch_cache=bool(r.get('fromPrefetchCache')),
            from_service_worker=bool(r.get('fromServiceWorker')),protocol=r.get('protocol'),timing=r.get('timing'))
        save()
    def cached(event):
        row=rows.get(event['requestId'])
        if row is not None:row['served_from_cache_event']=True
    def completed(event):
        row=rows.get(event['requestId'])
        if row is None:return
        row.update(finished=True,finished_timestamp=event.get('timestamp'),encoded_data_length=event.get('encodedDataLength'))
        if row.get('request_timestamp') is not None and row['finished_timestamp'] is not None:row['network_elapsed_seconds']=row['finished_timestamp']-row['request_timestamp']
        save()
    def failed(event):
        row=rows.get(event['requestId'])
        if row is None:return
        row.update(failed_timestamp=event.get('timestamp'),error_text=event.get('errorText'),cancelled=bool(event.get('canceled')),blocked_reason=event.get('blockedReason'))
        if row['kind']=='injected-outage':
            report['cdp_outage_failures'].append(dict(row))
            if force and is_confirmed_cdp_outage(row):report.setdefault('forced_outage_requests',[]).append(row['url'])
        save()
    for event,handler in [('Network.requestWillBeSent',request),('Network.responseReceived',response),('Network.requestServedFromCache',cached),('Network.loadingFinished',completed),('Network.loadingFailed',failed)]:session.on(event,handler)
    session.send('Network.enable')
    if force:session.send('Network.setBlockedURLs',{'urls':OUTAGE_PATTERNS})
    save();return session
