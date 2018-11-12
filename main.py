from bottle import route, run
import os


@route('/callback', method='POST')
def callback():
    pass


if __name__ == '__main__':
    run(host="0.0.0.0", port=int(os.environ.get('PORT', 443)))
