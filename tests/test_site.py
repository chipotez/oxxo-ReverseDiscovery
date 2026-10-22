import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build', ROOT/'scripts/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.ids, self.links, self.assets = [], [], []
        self.headings, self.images = [], []
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])
        if tag == 'a': self.links.append(attrs.get('href', ''))
        if tag == 'script' and 'src' in attrs: self.assets.append(attrs['src'])
        if tag == 'link' and 'href' in attrs: self.assets.append(attrs['href'])
        if tag == 'h1': self.headings.append(tag)

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build.build()
        cls.html = (ROOT/'dist/index.html').read_text()
        cls.doc = Document(cls.html)
    def test_all_navigation_resolves_to_real_sections(self):
        self.assertEqual(len(self.doc.ids), len(set(self.doc.ids)))
        for href in self.doc.links:
            self.assertTrue(href.startswith('#') and len(href)>1, href)
            self.assertIn(href[1:], self.doc.ids)
    def test_assets_are_local_and_present(self):
        for url in self.doc.assets:
            self.assertTrue(url.startswith('/assets/'))
            self.assertTrue((ROOT/'dist'/url.lstrip('/')).is_file())
        self.assertNotIn('https://', self.html)
    def test_private_routes_are_not_published(self):
        for name in ['enterprise.html','workspace.html','login.html','enterprise','workspace','login']:
            self.assertFalse((ROOT/'dist'/name).exists())
        self.assertEqual(len(self.doc.headings), 1)
        self.assertNotIn('<iframe', self.html)
        self.assertNotIn('<form', self.html)
    def test_catalog_schema_and_complete_no_js_content(self):
        data=json.loads((ROOT/'src/content/es.json').read_text())
        self.assertEqual([len(g['items']) for g in data['catalog']], [6,3,3])
        for group in data['catalog']:
            self.assertIn('panel-'+group['id'], self.doc.ids)
            for item in group['items']:
                self.assertIn(build.text(item['title']), self.html)
                self.assertTrue(item['topics'])
                self.assertTrue((ROOT/'src/assets/icons'/(item['icon']+'.svg')).exists())
    def test_editorial_content_is_escaped(self):
        self.assertEqual(build.text('<script>"&'), '&lt;script&gt;&quot;&amp;')
        with self.assertRaises(ValueError): build.icon('../secret')
    def test_build_is_deterministic(self):
        first = (ROOT/'dist/index.html').read_bytes()
        build.build()
        self.assertEqual(first,(ROOT/'dist/index.html').read_bytes())

if __name__ == '__main__': unittest.main()
