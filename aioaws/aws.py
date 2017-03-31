import hashlib
import hmac
import urllib
import datetime

from lxml import objectify
from aiohttp import ClientSession


def url_encode(v):
    """URL-encode a given string. No special characters are allowed
    space == %20.

    :param v: string
    :return: string -- URL-encoded string
    """
    return urllib.parse.quote_from_bytes(v.encode('utf-8'), safe='')


def sign(key, msg):
    """Sign a given message using a given key.

    :param key: key data (bytes)
    :param msg: message (string)
    :return: signature (bytes)
    """
    data = msg.encode('utf-8')
    sig = hmac.new(key, data, hashlib.sha256)
    return sig.digest()


class AWSException(Exception):
    """AWS errors.
    """

    def __init__(self, status, reason):
        """Create a new AWS exception for a given status code and reason.

        :param status: status code
        :param reason: error message
        """
        Exception.__init__(self, '%d: %s' % (status, reason))

        self.status = status
        self.reason = reason


class AWS:
    """Generic AWS client.
    """

    def __init__(self, region, service, access_key, secret_key, loop=None):
        """Create a new AWS client. The client should be created only within
        a coroutine as it contains an aiohttp ClientSession.

        :param region: AWS region
        :param service: AWS service name (e.g. sqs, sns)
        :param access_key: AWS access key
        :param secret_key: AWS secret access key
        :param loop: asyncio event loop
        """
        self.__region = region
        self.__service = service
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__event_loop = loop

    def __get_signature_key(self, key, date):
        """Get signature key for a given date-stamp.

        :param key: secret access key
        :param data: date stamp
        :return: key (bytes)
        """
        iv = 'AWS4' + key
        iv = iv.encode('utf-8')
        kdate = sign(iv, date)
        kregion = sign(kdate, self.__region)
        kservice = sign(kregion, self.__service)
        return sign(kservice, 'aws4_request')

    async def get(self, url, params):
        """Send a given AWS request using the GET method.

        :param url: request endpoint
        :param params: request params
        :return: response (lxml object)
        """
        timestamp = datetime.datetime.utcnow()
        amz_date = timestamp.strftime('%Y%m%dT%H%M%SZ')
        date = timestamp.strftime('%Y%m%d')

        tmp = urllib.parse.urlparse(url)

        canonical_uri = tmp.path
        canonical_headers = 'host:%s\n' % tmp.netloc
        signed_headers = 'host'

        alg = 'AWS4-HMAC-SHA256'
        region = self.__region
        service = self.__service
        access_key = self.__access_key
        scope = '%s/%s/%s/aws4_request' % (date, region, service)
        credential = '%s/%s' % (access_key, scope)

        params['X-Amz-Algorithm'] = alg
        params['X-Amz-Credential'] = credential
        params['X-Amz-Date'] = amz_date
        params['X-Amz-SignedHeaders'] = signed_headers

        params = [(k, url_encode(str(v))) for k, v in params.items()]
        params = sorted(params, key=lambda p: p[0])
        params = map(lambda p: '%s=%s' % (p[0], p[1]), params)

        canonical_query = '&'.join(params)

        payload_hash = hashlib.sha256(b"")

        canonical_request = 'GET\n%s\n%s\n%s\n%s\n%s' % (
            canonical_uri,
            canonical_query,
            canonical_headers,
            signed_headers,
            payload_hash.hexdigest())

        crhash = hashlib.sha256(canonical_request.encode('utf-8'))

        sdata = '%s\n%s\n%s\n%s' % (alg, amz_date, scope, crhash.hexdigest())
        key = self.__get_signature_key(self.__secret_key, date)
        sig = hmac.new(key, sdata.encode('utf-8'), hashlib.sha256)

        canonical_query += '&X-Amz-Signature=' + sig.hexdigest()
        url += '?' + canonical_query

        async with ClientSession(loop=self.__event_loop) as http_client:
            async with http_client.get(url) as response:
                if response.status != 200:
                    raise AWSException(response.status, response.reason)
                body = await response.text()
                return objectify.fromstring(body)
