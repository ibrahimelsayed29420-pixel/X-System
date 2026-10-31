import subprocess
import socket
import unittest
from unittest.mock import patch
from x_personal.public_pages import public_url,read_public_page

class PublicPageTests(unittest.TestCase):
    def test_local_or_private_network_is_rejected(self):
        for url,address in [('http://localhost/','127.0.0.1'),('http://10.0.0.1/','10.0.0.1'),('https://host.invalid/','169.254.169.254')]:
            with self.subTest(url=url),patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',(address,80))]):
                with self.assertRaises(ValueError):public_url(url)

    def test_file_credentials_and_session_links_are_rejected(self):
        for url in ('file:///C:/secret','https://user:pass@example.com/','https://example.com/?access_token=private','http://example.com:18764/'):
            with self.subTest(url=url),self.assertRaises(ValueError):public_url(url)

    def test_public_link_is_normalized_without_fragment(self):
        with patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.215.14',443))]):
            self.assertEqual(public_url('https://example.com#part'),'https://example.com/')

    def test_page_reader_reports_worker_timeout(self):
        timeout=subprocess.TimeoutExpired(cmd='crawl_worker.py',timeout=65)
        with patch('x_personal.public_pages.public_url',return_value='https://example.com/'), \
             patch('x_personal.public_pages.subprocess.run',side_effect=timeout):
            with self.assertRaisesRegex(TimeoutError,'65'):
                read_public_page('https://example.com/')
