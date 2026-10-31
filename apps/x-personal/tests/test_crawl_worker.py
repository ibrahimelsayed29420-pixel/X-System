import unittest

from crawl_worker import make_browser_config


class CrawlWorkerTests(unittest.TestCase):
    def test_browser_uses_installed_edge_channel(self):
        config=make_browser_config()
        self.assertEqual(config.chrome_channel,'msedge')
        self.assertTrue(config.headless)


if __name__=='__main__':unittest.main()
