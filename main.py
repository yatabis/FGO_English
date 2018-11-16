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

with open("LINEObject/main_record_carousel.json") as j:
    main_record_carousel = json.load(j)

with open("LINEObject/main_record_carousel_column.json") as j:
    main_record_carousel_column = json.load(j)

with open("LINEObject/chapter_container.json") as j:
    chapter_container = json.load(j)

with open("LINEObject/chapter_contents.json") as j:
    chapter_contents = json.load(j)

with open("LINEObject/story_text_unit.json") as j:
    story_text_unit = json.load(j)

with open("LINEObject/story_text_message.json") as j:
    story_text_message = json.load(j)


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


def mash_talk(token):
    month = datetime.today().month
    talk_list = mash[mash['month'] == month]
    rnd = np.random.randint(0, len(talk_list))
    message = [{
        "type": "text",
        "text": "マシュ (Mash)"
    }, {
        "type": "text",
        "text": talk_list['text'].values[rnd]
    }, {
        "type": "text",
        "text": talk_list['text_en'].values[rnd]
    }]
    reply_message(token, message)


def get_name(part=None, chapter=None, section=None):
    if section:
        part = main_record[main_record['main record'] == float(part)]['name'].item().lower().replace(" ", "_")
        chapter = eval(part)[eval(part)['chapter'] == chapter]['name'].item().replace(" ", "_")
        name = eval(chapter)[eval(chapter)['section'] == section]['table_title'].item().lower()
    elif chapter:
        part = main_record[main_record['main record'] == float(part)]['name'].item().lower().replace(" ", "_")
        name = eval(part)[eval(part)['chapter'] == chapter]['name'].item()
    elif part:
        name = main_record[main_record['main record'] == float(part)]['name'].item().lower()
    else:
        name = "Value Error."
    return name


def load_text_line(part, chapter, section, line):
    name = get_name(part, chapter, section)
    print(name)
    print(eval(name))
    record = eval(name)[eval(name)['line'] == line]
    speaker = record['speaker'].item()
    text = record['text'].item()
    text_unit = deepcopy(story_text_unit)
    text_message = deepcopy(story_text_message)
    text_message['body']['contents'][0]['text'] = text
    text_unit[0]['text'] = speaker
    text_unit[1]['altText'] = f"Story {chapter}-{section}: {line}"
    text_unit[1]['contents'] = text_message
    return text_unit


def create_chapter(part, chapter):
    name = get_name(part, chapter)
    section_list = deepcopy(chapter_container)
    section_list['altText'] = f"Chapter {chapter}"
    section_list['contents']['hero'][
        'url'] = f"https://raw.githubusercontent.com/yatabis/FGO_English/master/images/{name}.png"
    section = eval(name).to_dict(orient='record')
    for sec in section:
        section_button = deepcopy(chapter_contents)
        section_button['action']['label'] = sec['title']
        section_button['action']['data'] = f"part={part}&chapter={chapter}&section={sec['section']}"
        section_list['contents']['body']['contents'].append(section_button)
    return section_list


def create_part(part):
    name = get_name(part)
    part_carousel = deepcopy(main_record_carousel)
    part_carousel['altText'] = f"Main Record {part}"
    chapter = eval(name.replace(" ", "_")).to_dict(orient='record')
    for chap in chapter:
        part_column = deepcopy(main_record_carousel_column)
        part_column['imageUrl'] = \
            f"https://raw.githubusercontent.com/yatabis/FGO_English/master/images/{chap['name']}.png'"
        part_column['action']['data'] = f"part={part}&chapter={chap['chapter']}"
        part_carousel['template']['columns'].append(part_column)
    return part_carousel


@route('/callback', method='POST')
def callback():
    events = request.json['events']
    for event in events:
        reply_token = event['replyToken']
        pprint(event)
        if event['type'] == 'postback':
            postback_data = parse_qs(event['postback']['data'])
            if "section" in postback_data:
                part = postback_data['part'][0]
                chapter = postback_data['chapter'][0]
                section = int(postback_data['section'][0])
                line = postback_data['list'][0] if 'list' in postback_data else 0
                name = get_name(part, chapter, section)
                if name in table_list:
                    text_line = load_text_line(part, chapter, section, line)
                    reply_message(reply_token, text_line)
                else:
                    if section == '0':
                        if chapter == 0:
                            reply_text(reply_token, f"ストーリー第{part}部第序章プロローグの実装をお待ちください。")
                        else:
                            reply_text(reply_token, f"ストーリー第{part}部第{chapter}章アバンタイトルの実装をお待ちください。")
                    else:
                        reply_text(reply_token, f"ストーリー第{part}部第{chapter}章第{section}節の実装をお待ちください。")
            elif "chapter" in postback_data:
                part = postback_data['part'][0]
                chapter = postback_data['chapter'][0]
                name = get_name(part, chapter)
                if name in table_list:
                    section_list = create_chapter(part, chapter)
                    reply_message(reply_token, [section_list])
                else:
                    if chapter == "0":
                        reply_text(reply_token, f"ストーリー第{part}部序章の実装をお待ちください。")
                    elif chapter == "FIN":
                        reply_text(reply_token, f"ストーリー第{part}部終章の実装をお待ちください。")
                    else:
                        reply_text(reply_token, f"ストーリー第{part}部第{chapter}章の実装をお待ちください。")
            elif 'part' in postback_data:
                part = postback_data['part'][0]
                name = get_name(part)
                if name in table_list:
                    part_carousel = create_part(part)
                    reply_message(reply_token, [part_carousel])
                else:
                    reply_text(reply_token, f"ストーリー第{part}部の実装をお待ちください。")
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
