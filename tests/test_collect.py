import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('collect',Path(__file__).resolve().parents[1]/'scripts/collect.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

RSS='''<rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:o="https://www.ozbargain.com.au"><channel><title>Deals</title><item><title>SSD $1,099.50 Delivered &amp; Bonus</title><link>https://www.ozbargain.com.au/node/123</link><description>&lt;p&gt;Offer&lt;/p&gt;&lt;script&gt;secret()&lt;/script&gt;</description><dc:creator>Someone</dc:creator><o:meta votes-pos="20" votes-neg="2" comment-count="7" url="https://shop.example/product"/><pubDate>Mon, 12 Oct 2026 10:00:00 +1100</pubDate></item><item><title>Bad URL</title><link>javascript:alert(1)</link></item></channel></rss>'''
ATOM='''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>t3_abc</id><title>Post</title><author><name>/u/name</name></author><link href="https://www.reddit.com/r/all/comments/abc/"/><content type="html">&lt;p&gt;Hello&lt;/p&gt;</content><updated>2026-10-11T23:00:00Z</updated></entry></feed>'''

class CollectTests(unittest.TestCase):
    def item(self,price=100,checked='2026-10-11T00:00:00+00:00'):
        return c.identify({'group':'jbhifi','url':'https://www.jbhifi.com.au/products/ipad','title':'iPad Pro','price':price,'source_ids':['jb'],'checked_at':checked})
    def test_rss_metadata_and_unsafe_link(self):
        a=c.parse_feed(RSS,{'kind':'rss','group':'ozbargain','id':'oz'})
        self.assertEqual(len(a),1);self.assertEqual(a[0]['price'],1099.50)
        self.assertEqual(a[0]['votes'],18);self.assertEqual(a[0]['comments'],7)
        self.assertNotIn('secret',a[0]['text']);self.assertIn('& Bonus',a[0]['title'])
    def test_atom_is_not_assumed_to_have_votes(self):
        a=c.parse_feed(ATOM,{'kind':'atom','group':'reddit','id':'r','name':'All'})[0]
        self.assertIsNone(a['votes']);self.assertEqual(a['text'],'Hello')
    def test_block_page_is_rejected(self):
        with self.assertRaises(ValueError):c.parse_feed('<html/>',{'kind':'rss','group':'ozbargain','id':'oz'})
    def test_failure_preserves_previous_price_and_scan_time(self):
        old=self.item();old['last_seen']='2026-10-11T00:00:00+00:00'
        out=c.merge({'items':[old]},[],[{'id':'jb','status':'error'}],'2026-10-12T00:00:00+00:00')['items'][0]
        self.assertEqual(out['checked_at'],old['checked_at']);self.assertEqual(out['price'],100);self.assertTrue(out['stale'])
    def test_dedupe_combines_feed_membership(self):
        a=self.item();b={**a,'source_ids':['popular']}
        out=c.merge({'items':[]},[a,b],[],'2026-10-12T00:00:00+00:00')['items']
        self.assertEqual(len(out),1);self.assertEqual(set(out[0]['source_ids']),{'jb','popular'})
    def test_price_history_requires_observation(self):
        old=self.item();old.update(last_seen='2026-10-11T00:00:00+00:00',price_history=[{'at':'2026-10-11T00:00:00+00:00','price':100}])
        now=self.item(80,'2026-10-12T00:00:00+00:00')
        out=c.merge({'items':[old]},[now],[{'id':'jb','status':'ok'}],'2026-10-12T00:00:00+00:00')['items'][0]
        self.assertEqual(out['previous_price'],100);self.assertEqual([h['price'] for h in out['price_history']],[100,80])
    def test_missing_price_is_not_zero_or_a_drop(self):
        old=self.item();now=self.item(None)
        out=c.merge({'items':[old]},[now],[],'2026-10-12T00:00:00+00:00')['items'][0]
        self.assertIsNone(out['price']);self.assertEqual(out['price_history'],[])
    def test_absent_listing_is_not_called_expired(self):
        old=self.item();old['last_seen']='2026-10-11T00:00:00+00:00'
        out=c.merge({'items':[old]},[],[{'id':'jb','status':'ok'}],'2026-10-12T00:00:00+00:00')['items'][0]
        self.assertEqual(out['stale_reason'],'No longer in latest listing')
    def test_old_snapshots_pruned(self):
        old=self.item();old['last_seen']='2026-09-01T00:00:00+00:00'
        self.assertEqual(c.merge({'items':[old]},[],[],'2026-10-12T00:00:00+00:00')['items'],[])
    def test_safe_links(self):
        for url in ['javascript:alert(1)','file:///tmp/a','https://user:pass@example.com/']:
            self.assertEqual(c.safe_url(url),'')
    def test_feed_images_are_optional_and_deduplicated(self):
        content='<img src="https://preview.redd.it/a.jpg?width=640"><a href="https://i.redd.it/b.png">image</a><a href="https://i.redd.it/b.png">same</a><a href="https://example.com/article">article</a>'
        images=c.feed_images(content)
        self.assertEqual(len(images),2)
        self.assertEqual(images[0]['url'],'https://preview.redd.it/a.jpg?width=640')
        self.assertEqual(images[1]['name'],'b.png')
    def test_unsafe_image_addresses_and_hidden_markup_rejected(self):
        content='<img src="javascript:alert(1)"><img src="file:///etc/passwd"><img src="https://user:pass@example.com/a.jpg"><script><img src="https://example.com/a.jpg"></script>'
        self.assertEqual(c.feed_images(content),[])
    def test_reddit_atom_preserves_image_link(self):
        atom=ATOM.replace('&lt;p&gt;Hello&lt;/p&gt;','&lt;p&gt;Hello&lt;/p&gt;&lt;a href="https://i.redd.it/a.png"&gt;[link]&lt;/a&gt;')
        item=c.parse_feed(atom,{'kind':'atom','group':'reddit','id':'r','name':'All'})[0]
        self.assertEqual(item['attachments'][0]['url'],'https://i.redd.it/a.png')

if __name__=='__main__':unittest.main()
