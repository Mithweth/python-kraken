import urllib2
import configparser
import json
import time
import hashlib
import urllib
import hmac
import base64


class DecodeError(Exception):
    def __init__(self, body, message):
        self.message = message
        self.text = str(body)

    def __str__(self):
        return self.message


class HTTPError(Exception):
    def __init__(self, url, code, msg):
        self.url = url
        self.code = code if isinstance(code, int) else -1
        self.message = msg

    def __str__(self):
        return 'HTTP Error %s: %s' % (self.code, self.message)


class Kraken(object):
    def __init__(self, api_key=None, secret_key=None, proxy=None):
        self.api_key = api_key
        self.secret_key = secret_key
        proxies = {'https': proxy} if proxy else {}
        self._opener = urllib2.build_opener(urllib2.ProxyHandler(proxies))
        self.api_version = 0
        self.base_url = 'https://api.kraken.com'
        self.server_time = lambda: self._public('Time')
        self.assets = lambda opts={}: self._public('Assets', opts)
        self.asset_pairs = lambda opts={}: self._public('AssetPairs', opts)
        self.ticker = lambda pair: self._public('Ticker', {"pair": pair})
        self.order_book = lambda pair, opts={}: \
            self._public('Depth', dict(opts, pair=pair))
        self.trades = lambda pair, opts={}: \
            self._public('Trades', dict(opts, pair=pair))
        self.spread = lambda pair, opts={}: \
            self._public('Spread', dict(opts, pair=pair))
        self.balance = lambda opts={}: self._private('Balance', opts)
        self.trade_balance = lambda opts={}: \
            self._private('TradeBalance', opts)
        self.open_orders = lambda opts={}: self._private('OpenOrders', opts)
        self.closed_orders = lambda opts={}: \
            self._private('ClosedOrders', opts)
        self.query_orders = lambda opts={}: self._private('QueryOrders', opts)
        self.trade_history = lambda opts={}: \
            self._private('TradesHistory', opts)
        self.query_trades = lambda txid, opts={}: \
            self._private('QueryTrades', dict(opts, txid=txid))
        self.open_positions = lambda txid, opts={}: \
            self._private('OpenPositions', dict(opts, txid=txid))
        self.ledgers_info = lambda opts={}: self._private('Ledgers', opts)
        self.query_ledgers = lambda id, opts={}: \
            self._private('QueryLedgers', dict(opts, id=id))
        self.trade_volume = lambda pair, opts={}: \
            self._private('TradeVolume', dict(opts, pair=pair))
        self.add_order = lambda pair, type, ordertype, volume, opts={}: \
            self._private('AddOrder', dict(opts,
                                           pair=pair,
                                           type=type,
                                           ordertype=ordertype,
                                           volume=volume))
        self.cancel_order = lambda txid: \
            self._private('CancelOrder', {"txid": txid})

    def load_keys(self, path):
        config = configparser.ConfigParser()
        config.read(path)
        self.api_key = config.get('kraken', 'api_key')
        self.secret_key = config.get('kraken', 'secret_key')

    def _query(self, url, data={}, headers={}):
        api_url = self.base_url + url
        request = urllib2.Request(api_url)
        if data:
            request.add_data(urllib.urlencode(data))
        request.headers = headers
        request.headers['Accept'] = "application/json"
        result = response = None
        try:
            response = self._opener.open(request)
        except urllib2.HTTPError as e:
            raise HTTPError(request.get_full_url(), e.code, e.msg)
        except urllib2.URLError as e:
            raise HTTPError(request.get_full_url(), None, e.reason)
        if response.getcode() not in (200,):
            return {'error': {
                'code': response.getcode(),
                'message': response.msg
            }}
        response_data = response.read().decode('utf-8', 'ignore')
        if len(response_data) == 0:
            return None
        try:
            result = json.loads(response_data)
        except ValueError as e:
            raise DecodeError(response_data, e.message)
        if 'result' in result:
            result = result['result']
        return result

    def _public(self, url, data={}):
        return self._query('/%d/public/%s' % (self.api_version, url),
                           data)

    def _private(self, url, data={}):
        if not self.api_key or not self.secret_key:
            raise ValueError('api_key or secret_key are empty')
        urlpath = '/%d/private/%s' % (self.api_version, url)
        data['nonce'] = int(time.time()*10000)
        body = urllib.urlencode(data)
        message = urlpath + hashlib.sha256(str(data['nonce']) +
                                           body).digest()
        signature = hmac.new(base64.b64decode(self.secret_key),
                             message, hashlib.sha512)
        headers = {
          'API-Key': self.api_key,
          'API-Sign': base64.b64encode(signature.digest())
        }
        return self._query(urlpath, data, headers)

API = Kraken
