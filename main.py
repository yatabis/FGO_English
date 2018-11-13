from bottle import route, run
import json
import os
from pprint import pprint
import requests

CAT = os.environ['CHANNEL_ACCESS_TOKEN']
HEADER = {'Content-Type': 'application/json',
          'Authorization': f"Bearer {CAT}"}
REPLY_EP = "https://api.line.me/v2/bot/message/reply"


def reply_message(token, messages):
    body = json.dumps({'replyToken': token, 'messages': messages})
    req = requests.post(REPLY_EP, data=body, headers=HEADER)
    if req.status_code == 200:
        pprint(req.json())
    else:
        print(f"Error: {req.status_code}")
        pprint(req.json())


CONTINUE = {
   "type": "postback",
   "label": "Continue",
   "data": "action=continue",
}

SKIP = {
   "type": "postback",
   "label": "Skip",
   "data": "action=skip",
}

CONFIRM = {
  "type": "template",
  "altText": "Story text",
  "template": {
      "type": "confirm",
      "text": "text",
      "actions": [
          CONTINUE,
          SKIP
      ]
  }
}


@route('/callback', method='POST')
def callback():
    events = request.json['events']
    for event in events:
        pprint(event)
        if event['type'] == 'postback':
            postback_token = event['replyToken']
            postback_data = event['postback']['data']
            if postback_data == 'Continue':
                reply_message(postback_token, CONFIRM)


if __name__ == '__main__':
    run(host="0.0.0.0", port=int(os.environ.get('PORT', 443)))
