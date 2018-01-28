from flask import Flask
from flask import request,render_template
import redis

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/')
def hello():
	hola = r.get('foo')
	#return "Hello World! <br> Hello --> {}".format(hola)
	return render_template("index.html", p=hola.decode("utf-8"))

if __name__ == '__main__':
    app.run()