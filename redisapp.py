from flask import Flask
from flask import request,render_template, request, url_for, session, g, redirect
import redis

app = Flask(__name__)
DEBUG=True
#r = redis.Redis(host='localhost', port=6379, db=0)

SECRET_KEY = '8cb049a2b6160e1838df7cfe896e3ec32da888d7'
app.secret_key = SECRET_KEY

def init_db():
    db = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=0)
    return db

@app.before_request
def before_request():
    g.db = init_db()

@app.route('/hello')
def hello():
	hola = r.get('foo')
	#return "Hello World! <br> Hello --> {}".format(hola)
	return render_template("index.html", p=hola.decode("utf-8"))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'GET':
        return render_template('signup.html', error=error)
    username = request.form['username']
    password = request.form['password']
    user_id = str(g.db.incrby('next_user_id', 1000))
    g.db.hmset('user:' + user_id, dict(username=username, password=password))
    g.db.hset('users', username, user_id)
    session['username'] = username
    return redirect(url_for('home'))

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'GET':
        return render_template('login.html', error=error)
    username = request.form['username']
    password = request.form['password']
    user_id = str(g.db.hget('users', username), 'utf-8')
    if not user_id:
        error = 'No such user'
        return render_template('login.html', error=error)
    saved_password = str(g.db.hget('user:' + str(user_id), 'password'), 'utf-8')
    if password != saved_password:
        error = 'Incorrect password'
        return render_template('login.html', error=error)
    session['username'] = username
    return redirect(url_for('home'))

@app.route('/home', methods=['GET', 'POST'])
def home():
    if not session:
        return redirect(url_for('login'))
    user_id = g.db.hget('users', session['username'])
    if request.method == 'GET':
        return render_template('home.html', timeline=_get_timeline(user_id))
    text = request.form['tweet']
    post_id = str(g.db.incr('next_post_id'))
    g.db.hmset('post:' + post_id, dict(user_id=user_id,
                                       ts=datetime.utcnow(), text=text))
    g.db.lpush('posts:' + str(user_id), str(post_id))
    g.db.lpush('timeline:' + str(user_id), str(post_id))
    g.db.ltrim('timeline:' + str(user_id), 0, 100)
    return render_template('home.html', timeline=_get_timeline(user_id))

def _get_timeline(user_id):
    posts = g.db.lrange('timeline:' + str(user_id), 0, -1)
    timeline = []
    for post_id in posts:
        post = g.db.hgetall('post:' + str(post_id, 'utf-8'))
        timeline.append(dict(
            username=g.db.hget('user:' + str(post[b'user_id'], 'utf-8'), 'username'),
            ts=post[b'ts'],
            text=post[b'text']))
    return timeline

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run()