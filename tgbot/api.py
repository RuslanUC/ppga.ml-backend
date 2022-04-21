from aiohttp import ClientSession
from io import BytesIO
from .file import File

class Api:
    def __init__(self, token):
        self._token = token
        
    @property
    def file_url(self):
        return f"https://api.telegram.org/file/bot{self._token}"
        
    @property
    def api_base(self):
        return f"https://api.telegram.org/bot{self._token}"
        
    async def getFile(self, id):
        async with ClientSession() as sess:
            async with sess.get(f"{self.api_base}/getFile?file_id={id}") as r:
                assert r.status == 200, f"Error while getting file, code: {r.status}"
                j = await r.json()
                return File(id, j["result"]["file_path"], self)

    async def sendFile(self, fp, chat_id):
        assert isinstance(fp, BytesIO), "fp must be BytesIO (server error)"
        assert fp.getbuffer().nbytes < 15*1024**2, "File size must be less then 15MB"
        async with ClientSession() as sess:
            async with sess.post(f"{self.api_base}/sendDocument?chat_id={chat_id}&disable_notification=true", data={"document": fp}) as r:
                assert r.status == 200, f"Error while saving file, code: {r.status}"
                j = await r.json()
                return File(j["result"]["document"]["file_id"], None, self)

    async def auth(self):
        async with ClientSession() as sess:
            async with sess.get(f"{self.api_base}/getMe") as r:
                if r.status != 200:
                    return None
        return self

    def __eq__(self, other):
        return self._token == other._token