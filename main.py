from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from currysniper import CurrySniper

# Telegram ID of the account you wish to snipe with
id = 000000000

# CurrySniperBot TG API
# Create a new telegram bot and assign the values of the telegram account you used to create the bot
currybot_api_id = 'YOUR_API_ID'
currybot_api_hash = 'YOUR_API_HASH'
currybot_token = 'YOUR_API_TOKEN'
currybot = Client('{}'.format(id), api_id=currybot_api_id, api_hash=currybot_api_hash, bot_token=currybot_token)
currybot.start()

licensed_user = CurrySniper(id, currybot, 1)

idle()
