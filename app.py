<<<<<<< HEAD
import os
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='127.0.0.1', port=port)
=======
import os
from flask import Flask

app = Flask(__name__)
@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='127.0.0.1', port=port)
>>>>>>> c52eacd691e7861981f5c2dd529a28487e036fba
