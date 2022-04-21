from os import environ
from io import BytesIO
from telethon import TelegramClient
from asyncio import run, get_event_loop

client = TelegramClient(
	"PepegaBot",
    api_id=int(environ.get("API_ID")),
    api_hash=environ.get("API_HASH")
)
#client.start(bot_token=environ.get("TG_BOT_TOKEN"))

class Utils:
	@staticmethod
	async def get_file(file_id):
		async with _bot:
			f = await File.from_fileid(_bot, file_id)
			async for c in f.stream():
				yield c

	@staticmethod
	async def send_file(data):
		async with _bot:
			m = await _bot.send_document(492693958, data)
		return m.media.file_id

async def main():
	#BQACAgIAAxkDAAMWYmFrURVS-sNy5O6YEqfx2jVT8xEAAnQYAALTaRFLKcaLfG6xzxoeBA
	await client.connect()
	async for ch in client.iter_download("BQACAgIAAxkDAAMWYmFrURVS-sNy5O6YEqfx2jVT8xEAAnQYAALTaRFLKcaLfG6xzxoeBA"):
		print(ch)

if __name__ == "__main__":
	client.loop.run_until_complete(main())