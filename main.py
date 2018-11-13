from bottle import route, run
import os
from pprint import pprint


@route('/callback', method='POST')
def callback():
    events = request.json['events']
    for event in events:
        pprint(event)


if __name__ == '__main__':
    run(host="0.0.0.0", port=int(os.environ.get('PORT', 443)))
