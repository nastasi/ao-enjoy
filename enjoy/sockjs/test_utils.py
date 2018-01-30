import json
import asyncio


class SockjsTest():
    TRANS_NONE = 0
    TRANS_XHR_STREAMING = 1

    def __init__(self, client):
        self.client = client
        self.request_stream_in = None
        self.stream = 666
        self.transport = self.TRANS_NONE

    def __enter__(self):
        pass

    def __exit__(self, *args):
        if self.request_stream_in:
            self.request_stream_in.close()

    async def connect(self, transport_list, stream=666, loop=None):
        self.stream = stream
        for transport in transport_list:
            if transport == "xhr_streaming":
                self.request_stream_in = await self.client.request(
                    "POST", ("/sockjs/%d/sockjsss/xhr_streaming" % stream),
                    read_until_eof=False, chunked=True)
                print("CIN: %d %s" % (self.stream, self.request_stream_in.closed))
                assert self.request_stream_in.status == 200
                await self.readchunks(3, 10, loop=loop)

                self.transport = self.TRANS_XHR_STREAMING

                print("COU: %d %s" % (self.stream, self.request_stream_in.closed))
                return True

        # FIXME: raise proper exception
        raise Exception

    async def send(self, msg):
        if self.transport == self.TRANS_XHR_STREAMING:
            self.request_stream_out = await self.client.request(
                "POST", ("/sockjs/%d/sockjsss/xhr_send" % self.stream),
                data=json.dumps(msg))
            assert self.request_stream_out.status == 204
            return True

    async def _readchunks_blk(self, chunks_n):
        print("IN: %d %s" % (self.stream, self.request_stream_in.closed))
        ret = []
        for i in range(chunks_n):
            ret.append(
                await self.request_stream_in.content.readchunk())
        print("OU: %d %s" % (self.stream, self.request_stream_in.closed))
        return ret

    async def readchunks(self, chunks_n, timeout=0, loop=None):
        ret = []
        try:
            ret = await asyncio.wait_for(
                self._readchunks_blk(chunks_n), timeout, loop=loop)
            return ret
        except asyncio.TimeoutError:
            return None
