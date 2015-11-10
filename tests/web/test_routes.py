import unittest

from willtherebespace.web import app


class TestCase(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def assertStatus(self, response, status_code, message=None):
        message = message or 'HTTP Status %s expected but got %s' \
                             % (status_code, response.status_code)
        self.assertEqual(response.status_code, status_code, message)


class TestRobotsTxt(TestCase):
    def test_status_ok(self):
        res = self.client.get('/robots.txt')
        self.assertStatus(res, 200)

    def test_contains_sitemap(self):
        res = self.client.get('/robots.txt')
        self.assertIn(b'Sitemap: ', res.data)
        self.assertIn(b'sitemap.xml', res.data)


class TestSitemapXml(TestCase):
    def test_status_ok(self):
        res = self.client.get('/sitemap.xml')
        self.assertStatus(res, 200)

    def test_contains_information(self):
        res = self.client.get('/sitemap.xml')
        self.assertIn(b'urlset', res.data)
        self.assertIn(b'/', res.data)
        self.assertIn(b'/sitemap.xml', res.data)
        self.assertIn(b'http', res.data)  # to check for absolute URLs
