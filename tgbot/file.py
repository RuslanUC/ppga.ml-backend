from aiohttp import ClientSession
from magic import from_buffer

class File:
    def __init__(self, id, path, api):
        self.id = id
        self.path = path
        self._api = api
        
    async def getStream(self):
        async with ClientSession() as sess:
            async with sess.get(f"{self._api.file_url}/{self.path}") as r:
                ch = await r.content.read(1024)
                yield from_buffer(ch, mime=True)
                yield ch
                async for chunk in r.content.iter_chunked(1024):
                    yield chunk