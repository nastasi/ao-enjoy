import json
import asyncio


class SockjsTest():
    TRANS_NONE = 0
    TRANS_XHR_STREAMING = 1

    def __init__(self, client):
        self.client = client
        self.request_stream_in = None
        self.transport = self.TRANS_NONE

    def __enter__(self):
        pass

    def __exit__(self, *args):
        if self.request_stream_in:
            self.request_stream_in.close()

    async def connect(self, transport_list, loop=None):
        for transport in transport_list:
            if transport == "xhr_streaming":
                self.request_stream_in = await self.client.request(
                    "POST", "/sockjs/666/sockjsss/xhr_streaming",
                    read_until_eof=False, chunked=True)
                assert self.request_stream_in.status == 200
                self.transport = self.TRANS_XHR_STREAMING

                return True

        # FIXME: raise proper exception
        raise Exception

    async def send(self, msg):
        if self.transport == self.TRANS_XHR_STREAMING:
            self.request_stream_out = await self.client.request(
                "POST", "/sockjs/666/sockjsss/xhr_send",
                data=json.dumps(msg))
            assert self.request_stream_out.status == 204
            return True

    async def _readchunks_blk(self, chunks_n):
        ret = []
        for i in range(chunks_n):
            ret.append(
                await self.request_stream_in.content.readchunk())
        return ret

    async def readchunks(self, chunks_n, timeout=0, loop=None):
        ret = []
        try:
            ret = await asyncio.wait_for(
                self._readchunks_blk(chunks_n), timeout, loop=loop)
            return ret
        except asyncio.TimeoutError:
            return None
