import importlib.util
import json
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('add_source',Path(__file__).resolve().parents[1]/'scripts/add_source.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class SourceTests(unittest.TestCase):
    def test_reddit_hot_new_top(self):
        for order in ['hot','new','top']:
            s=a.source_for({'type':'subreddit','subreddit':'AskReddit','order':order})
            self.assertIn('/r/askreddit/'+order+'/.rss',s['url']);self.assertEqual(s['kind'],'atom')
    def test_all_category_urls(self):
        for cat in a.CATEGORIES:
            s=a.source_for({'type':'ozbargain','category':cat});self.assertEqual(s['url'],'https://www.ozbargain.com.au/cat/'+cat+'/feed')
    def test_invalid_requests_cannot_control_urls(self):
        for req in [None,{'type':'subreddit','subreddit':'../x'},{'type':'subreddit','subreddit':'example','order':'new;echo bad'}, {'type':'subreddit','subreddit':'example','url':'http://localhost'}, {'type':'ozbargain','category':'unknown'},{'type':'other','url':'https://example.com'}]:
            with self.assertRaises(ValueError):a.source_for(req)
    def test_owner_only(self):
        req={'type':'subreddit','subreddit':'AskReddit','order':'new'}
        event={'repository':{'full_name':'Owner/Reader'},'issue':{'user':{'login':'Owner'},'title':'WorkReader: add source · r/askreddit','body':'<!-- workreader-source-v1 -->\n```json\n'+json.dumps(req)+'\n```'}}
        self.assertEqual(a.request_from_event(event,'Owner/Reader')['id'],'reddit-askreddit-new')
        event['issue']['user']['login']='SomeoneElse'
        with self.assertRaises(ValueError):a.request_from_event(event,'Owner/Reader')
    def test_duplicate_and_limit(self):
        source=a.source_for({'type':'ozbargain','category':'computing'});cfg={'sources':[]}
        self.assertTrue(a.apply_source(cfg,source));self.assertFalse(a.apply_source(cfg,source))
        cfg={'sources':[{'id':str(i)} for i in range(60)]}
        with self.assertRaises(ValueError):a.apply_source(cfg,source)

if __name__=='__main__':unittest.main()
