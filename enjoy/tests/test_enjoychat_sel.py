from multiprocessing import Process
import unittest
from aiohttp import web
from selenium import webdriver
import time

from .. import EnjoyChat


def enjoy_chat_runner():
    enjoy_chat = EnjoyChat(use_real_db=False)

    app = web.Application()
    app.on_startup.append(enjoy_chat.setup)

    web.run_app(app, host='127.0.0.1', port=8080)

p = None


def setUpModule():
    global p
    p = Process(target=enjoy_chat_runner)
    p.start()


def tearDownModule():
    p.terminate()
    p.join()


class EnjoyChatSelTestCase(unittest.TestCase):
    HOST = "http://127.0.0.1:8080"

    def setUp(self):
        self.drivers = []

    def tearDown(self):
        for d in self.drivers:
            d.close()
        self.drivers = []

    def _find_xpath(self, d, s):
        elem = d.find_elements_by_xpath(s)
        self.assertEqual(len(elem), 1)
        return elem[0]

    def _login(self, d, user, passwd):
        d.get(self.HOST)
        elem = self._find_xpath(d, "//form[@action='/login']"
                                "/input[@name='login']")
        elem.send_keys(user)

        elem = self._find_xpath(d, "//form[@action='/login']/"
                                "input[@name='password']")
        elem.send_keys(passwd)

        elem = self._find_xpath(d, "//form[@action='/login']/"
                                "input[@type='submit']")
        elem.submit()

    def _staminal_stream_tst(self, stream_type):
        transports = ["websocket", "xhr-streaming", "iframe-eventsource",
                      "iframe-htmlfile", "xhr-polling", "iframe-xhr-polling",
                      "jsonp-polling"]
        d1 = webdriver.Firefox()
        d2 = webdriver.Firefox()
        self.drivers.append(d1)
        self.drivers.append(d2)

        self._login(d1, 'user', 'password')
        self._login(d2, 'admin', 'password')

        for d in [d1, d2]:
            d.get(self.HOST + '/chat')
            for transport in transports:
                if transport == stream_type:
                    continue

                elem = self._find_xpath(
                    d, "//input[@type='checkbox'][@id='%s']" % transport)
                if elem.is_selected():
                    elem.click()

            elem = self._find_xpath(
                d, "//a[@id='connect']")
            elem.click()
        text = self._find_xpath(d1, "//input[@type='text'][@id='text']")
        text.send_keys('MyNewMessage')

        sub = self._find_xpath(d1, "//input[@type='submit']")
        sub.click()

        log = self._find_xpath(d2, "//div[@id='log']")
        self.assertNotEqual(log.text.find("Received: MyNewMessage"), -1)

    def test_websocket(self):
        self._staminal_stream_tst('websocket')

    def test_xhr_streaming(self):
        self._staminal_stream_tst('xhr-streaming')

    def test_iframe_eventsource(self):
        self._staminal_stream_tst('iframe-eventsource')

    def test_iframe_htmlfile(self):
        self._staminal_stream_tst('iframe-htmlfile')

    def test_xhr_polling(self):
        self._staminal_stream_tst('xhr-polling')

    def test_iframe_xhr_polling(self):
        self._staminal_stream_tst('iframe-xhr-polling')

    def test_jsonp_polling(self):
        self._staminal_stream_tst('jsonp-polling')
