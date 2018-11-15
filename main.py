from bottle import request, route, run
from copy import deepcopy
from datetime import datetime
import json
import numpy as np
import os
import pandas as pd
from pprint import pprint
import pymysql.cursors
import requests
from urllib.parse import parse_qs

CAT = os.environ['CHANNEL_ACCESS_TOKEN']
HEADER = {'Content-Type': 'application/json',
          'Authorization': f"Bearer {CAT}"}
REPLY_EP = "https://api.line.me/v2/bot/message/reply"

with open("main_story_carousel.json") as j:
    carousels = json.load(j)

with open("section_list.json") as j:
    section_list = json.load(j)


def reply_message(token, messages):
    body = {'replyToken': token, 'messages': messages}
    req = requests.post(REPLY_EP, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=HEADER)
    if req.status_code == 200:
        pprint(req.json())
    else:
        print(f"Error: {req.status_code}")
        pprint(req.json())


def reply_text(token, text):
    message = [{
        "type": "text",
        "text": text
    }]
    reply_message(token, message)


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

SECTION_BUTTON = {
    'type': 'button',
    'action': {
        'type': 'postback',
        'label': 'セクション名',
        'data': 'section=1'
    },
    'height': 'sm',
    'style': 'secondary'
}


def mash_talk(token):
    month = datetime.today().month
    talk_list = mash[mash['month'] == month]
    rnd = np.random.randint(0, len(talk_list))
    message = [{
        "type": "text",
        "text": talk_list['text'].values[rnd]
    }, {
        "type": "text",
        "text": talk_list['text_en'].values[rnd]
    }
    ]
    reply_message(token, message)


@route('/callback', method='POST')
def callback():
    events = request.json['events']
    for event in events:
        reply_token = event['replyToken']
        pprint(event)
        if event['type'] == 'postback':
            postback_data = parse_qs(event['postback']['data'])
            if "section" in postback_data:
                pass
            elif "chapter" in postback_data:
                main = postback_data['main'][0]
                chapter = postback_data['chapter'][0]
                part = main_record[main_record['main record'] == float(main)]['name'].item().lower().replace(" ", "_")
                name = eval(part)[eval(part)['chapter'] == chapter]['name'].item()
                if name in table_list:
                    section = eval(name)['title']
                    message = deepcopy(section_list)
                    message['contents']['hero'][
                        'url'] = f"https://raw.githubusercontent.com/yatabis/FGO_English/master/images/{name}.png"
                    for sec in section:
                        sec_btn = deepcopy(SECTION_BUTTON)
                        sec_btn['action']['label'] = sec
                        message['contents']['body']['contents'].append(sec_btn)
                    reply_message(reply_token, [message])
                else:
                    if chapter == "F":
                        reply_text(reply_token, f"ストーリー第{main}部序章の実装をお待ちください。")
                    elif chapter == "FIN":
                        reply_text(reply_token, f"ストーリー第{main}部終章の実装をお待ちください。")
                    else:
                        reply_text(reply_token, f"ストーリー第{main}部第{chapter}章の実装をお待ちください。")
            elif "main" in postback_data:
                main = postback_data['main'][0]
                name = main_record[main_record['main record'] == float(main)]['name'].item().lower()
                if name in table_list:
                    reply_message(reply_token, [carousels[main]])
                else:
                    reply_text(reply_token, f"ストーリー第{main}部の実装をお待ちください。")
            else:
                reply_text(reply_token, "不正なポストバックが送信されました。")
        else:
            mash_talk(reply_token)


if __name__ == '__main__':
    connection_config = {
        'user': os.environ['DB_USER'],
        'password': os.environ['DB_PASS'],
        'host': os.environ['DB_HOST'],
        'database': os.environ['DB_NAME'],
        'cursorclass': pymysql.cursors.DictCursor
    }
    connection = pymysql.connect(**connection_config)
    main_record = pd.read_sql('select * from `main record`', connection)
    observer_on_timeless_temple = pd.read_sql('select * from `Observer on Timeless Temple`', connection)
    fuyuki = pd.read_sql('select * from fuyuki', connection)
    prologue = pd.read_sql('select * from prologue', connection)
    tables = pd.read_sql('show tables', connection).values
    mash = pd.read_sql('select * from mash_talk', connection)
    table_list = tables.reshape(len(tables))
    connection.close()
    run(host="0.0.0.0", port=int(os.environ.get('PORT', 443)))
