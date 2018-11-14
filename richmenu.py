import json
import os
import requests
from pprint import pprint

CAT = os.environ.get('CHANNEL_ACCESS_TOKEN')
HEADER = {'Content-Type': 'application/json',
          'Authorization': f"Bearer {CAT}"}
RICHMENU_ID = "richmenu-fb8628e8fb634be5ace65b6adb0f2ddf"
EP = f"https://api.line.me/v2/bot/richmenu/{RICHMENU_ID}"

req = requests.delete(EP, headers=HEADER)
print(req.status_code)
pprint(req.json())
