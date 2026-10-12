#!/usr/bin/env python3
"""Apply a constrained feed request submitted by this repository's owner."""
import json
import os
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=json.loads((ROOT/'assets/source-categories.json').read_text())


def source_for(request):
    if not isinstance(request,dict):raise ValueError('Expected a source request object')
    if request.get('type')=='subreddit':
        if set(request)-{'type','subreddit','order'}:raise ValueError('Unsupported request fields')
        name=request.get('subreddit','')
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_]{2,21}',name):raise ValueError('Invalid subreddit name')
        name=name.lower();order=request.get('order','hot')
        if order not in ('hot','new','top'):raise ValueError('Invalid subreddit order')
        query='limit=25'+('&t=week' if order=='top' else '')
        return {'id':'reddit-'+name+'-'+order,'group':'reddit','name':'r/'+name+' · '+order.capitalize(),'kind':'atom','url':f'https://www.reddit.com/r/{name}/{order}/.rss?{query}','page_url':f'https://www.reddit.com/r/{name}/{order}'}
    if request.get('type')=='ozbargain':
        if set(request)-{'type','category'}:raise ValueError('Unsupported request fields')
        category=request.get('category')
        if not isinstance(category,str) or category not in CATEGORIES:raise ValueError('Invalid category')
        return {'id':'oz-cat-'+category,'group':'ozbargain','name':CATEGORIES[category],'kind':'rss','url':'https://www.ozbargain.com.au/cat/'+category+'/feed','page_url':'https://www.ozbargain.com.au/cat/'+category}
    raise ValueError('Unsupported source type')


def request_from_event(event,repository):
    owner=repository.split('/')[0]
    if event.get('repository',{}).get('full_name','').lower()!=repository.lower():raise ValueError('Repository mismatch')
    issue=event.get('issue',{})
    if issue.get('user',{}).get('login','').lower()!=owner.lower():raise ValueError('Only the repository owner can add sources')
    if 'pull_request' in issue or not issue.get('title','').startswith('WorkReader: add source'):raise ValueError('Not a WorkReader source request')
    body=issue.get('body') or ''
    if len(body)>4000 or '<!-- workreader-source-v1 -->' not in body:raise ValueError('Invalid source request body')
    match=re.search(r'```json\s*\n(.*?)\n```',body,re.S)
    if not match:raise ValueError('Missing source JSON')
    return source_for(json.loads(match.group(1)))


def apply_source(config,source):
    if any(s.get('id')==source['id'] or s.get('url')==source['url'] for s in config['sources']):return False
    if len(config['sources'])>=60:raise ValueError('Maximum of 60 sources reached')
    config['sources'].append(source);return True


def main():
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    source=request_from_event(event,os.environ['GITHUB_REPOSITORY'])
    path=ROOT/'config.json';config=json.loads(path.read_text());changed=apply_source(config,source)
    if changed:path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    print(('Added ' if changed else 'Already configured: ')+source['id'])
    output=os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output,'a') as f:f.write('source_id='+source['id']+'\n')


if __name__=='__main__':main()
