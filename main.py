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
USERNAME_EP = "https://api.line.me/v2/bot/profile/"

with open("LINEObject/main_record_carousel.json") as j:
    main_record_carousel = json.load(j)

with open("LINEObject/main_record_carousel_column.json") as j:
    main_record_carousel_column = json.load(j)

with open("LINEObject/chapter_container.json") as j:
    chapter_container = json.load(j)

with open("LINEObject/chapter_contents.json") as j:
    chapter_contents = json.load(j)

with open("LINEObject/story_text.json") as j:
    story_text = json.load(j)

with open("LINEObject/option_choice.json") as j:
    option_choice = json.load(j)


def reply_message(token, messages):
    body = {'replyToken': token, 'messages': messages}
    req = requests.post(REPLY_EP, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=HEADER)
    if req.status_code != 200:
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


def create_option_text(part, chapter, section, line, option):
    choices = [c for c in option_list.to_dict(orient='split')['data'][option] if isinstance(c, str)]
    choice_message = [deepcopy(option_choice) for _ in choices]
    for c in range(len(choices)):
        action = get_action(part, chapter, section, line, None, c + 1)
        choice_message[c]['contents']['body']['contents'][0]['text'] = choices[c]
        choice_message[c]['contents']['body']['contents'][0]['action']['label'] = f"choice {c}"
        choice_message[c]['contents']['body']['contents'][0]['action']['data'] = action

    return choice_message


def get_speaker(speaker, speaker_en):
    return f"{speaker} ({speaker_en})" if speaker_en else f"{speaker}" if speaker else None


def get_font_color(speaker):
    magenta = ["アナウンス"]
    if speaker in magenta:
        color = "#00dddd"
    else:
        color = None
    return color


def get_next_record_line(part, chapter, section, line, flag):
    loop = True
    while loop:
        line += 1
        next_record = main_record[part]['contents'][chapter]['contents'][section]['contents'][line]
        next_flag = next_record['flag'] if not np.isnan(next_record['flag']) else None
        loop = next_flag not in {flag, 0, -1, None}
    return line


def get_action(part, chapter, section, line, option, flag):
    if flag == -1:
        action = f"part={part}&chapter={chapter}"
    elif option is not None:
        action = f"part={part}&chapter={chapter}&section={section}&line={line}&option={option}"
    else:
        next_line = get_next_record_line(part, chapter, section, line, flag)
        action = f"part={part}&chapter={chapter}&section={section}&line={next_line}"
    return action


def load_text_line(part, chapter, section, line, username):
    record = main_record[part]['contents'][chapter]['contents'][section]['contents'][line]
    speaker = get_speaker(record['speaker'], record['speaker_en'])
    text = record['text']
    text_en = record['text_en']
    size = record['size']
    color = get_font_color(record['speaker'])
    flag = int(record['flag']) if not np.isnan(record['flag']) else None
    option = int(record['option']) if not np.isnan(record['option']) else None
    action = get_action(part, chapter, section, line, option, flag)

    text_message = deepcopy(story_text)
    text_message['altText'] = f"Story {chapter}-{section}: {line}"
    text_message['contents']['body']['contents'][0]['text'] = speaker
    text_message['contents']['body']['contents'][2]['contents'][1]['contents'][0]['text'] = text.format(username=username)
    text_message['contents']['body']['contents'][2]['contents'][1]['contents'][2]['text'] = text_en.format(username=username)
    if size:
        text_message['contents']['body']['contents'][2]['contents'][1]['contents'][0]['size'] = size
        text_message['contents']['body']['contents'][2]['contents'][1]['contents'][2]['size'] = size
    if color is not None:
        text_message['contents']['body']['contents'][2]['contents'][1]['contents'][0]['color'] = color
        text_message['contents']['body']['contents'][2]['contents'][1]['contents'][2]['color'] = color
        text_message['contents']['body']['contents'][0]['color'] = color
    text_message['contents']['body']['action']['data'] = action

    return [text_message]


def create_chapter(part, chapter):
    name = main_record[part]['contents'][chapter]['name']
    section_list = deepcopy(chapter_container)
    section_list['altText'] = f"Chapter {chapter}"
    section_list['contents']['hero'][
        'url'] = f"https://raw.githubusercontent.com/yatabis/FGO_English/master/images/{name}.png"
    section = main_record[part]['contents'][chapter]['contents']
    for k, v in section.items():
        section_button = deepcopy(chapter_contents)
        section_button['action']['label'] = v['title']
        section_button['action']['data'] = f"part={part}&chapter={chapter}&section={k}"
        section_list['contents']['body']['contents'].append(section_button)
    return [section_list]


def create_part(part):
    part_carousel = deepcopy(main_record_carousel)
    part_carousel['altText'] = f"Main Record {part}"
    chapter = main_record[part]['contents']
    for k, v in chapter.items():
        part_column = deepcopy(main_record_carousel_column)
        part_column['imageUrl'] = \
            f"https://raw.githubusercontent.com/yatabis/FGO_English/master/images/{v['name']}.png"
        part_column['action']['data'] = f"part={part}&chapter={k}"
        part_carousel['template']['columns'].append(part_column)
    return [part_carousel]


def unimplemented(part, chapter=None, section=None):
    text = f"ストーリー第{part}部"
    if chapter == '0':
        text += "序章"
    elif chapter == 'FIN':
        text += "終章"
    elif chapter is not None:
        text += f"第{chapter}章"
    if section == 0:
        if chapter == '0':
            text += "プロローグ"
        elif chapter is not None:
            text += "アバンタイトル"
    elif section is not None:
        text += f"第{section}節"
    text += "の実装をお待ちください。"
    return text


def get_username(user_id):
    req = requests.get(USERNAME_EP + user_id, headers=HEADER)
    name = req.json()['displayName']
    return name


@route('/callback', method='POST')
def callback():
    events = request.json['events']
    for event in events:
        reply_token = event['replyToken']
        user_id = event['source']['userId']
        username = get_username(user_id)
        pprint(event)
        if event['type'] == 'postback':
            postback_data = parse_qs(event['postback']['data'])
            if "option" in postback_data:
                part = postback_data['part'][0]
                chapter = postback_data['chapter'][0]
                section = int(postback_data['section'][0])
                line = int(postback_data['line'][0])
                option = int(postback_data['option'][0])
                option_text = create_option_text(part, chapter, section, line, option)
                reply_message(reply_token, option_text)
            elif "section" in postback_data:
                part = postback_data['part'][0]
                chapter = postback_data['chapter'][0]
                section = int(postback_data['section'][0])
                line = int(postback_data['line'][0]) if 'line' in postback_data else 1
                if main_record[part]['contents'][section]['contents'][section]['name'].lower() in table_list:
                    text_line = load_text_line(part, chapter, section, line, username)
                    reply_message(reply_token, text_line)
                else:
                    unimplemented_text = unimplemented(part, chapter, section)
                    reply_text(reply_token, unimplemented_text)
            elif "chapter" in postback_data:
                part = postback_data['part'][0]
                chapter = postback_data['chapter'][0]
                if main_record[part]['contents'][chapter]['name'].lower() in table_list:
                    section_list = create_chapter(part, chapter)
                    reply_message(reply_token, section_list)
                else:
                    unimplemented_text = unimplemented(part, chapter)
                    reply_text(reply_token, unimplemented_text)
            elif 'part' in postback_data:
                part = postback_data['part'][0]
                if main_record[part]['name'].lower() in table_list:
                    part_carousel = create_part(part)
                    reply_message(reply_token, part_carousel)
                else:
                    unimplemented_text = unimplemented(part)
                    reply_text(reply_token, unimplemented_text)
            else:
                reply_text(reply_token, "不正なポストバックが送信されました。")
        else:
            mash_talk(reply_token)


if __name__ == '__main__':
    from main_record import main_record, option_list, mash_talk, table_list
    run(host="0.0.0.0", port=int(os.environ.get('PORT', 443)))
