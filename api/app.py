#!/usr/bin/env python3
from flask import Flask
from flask_cors import CORS

from api.api_v1 import api_v1


app = Flask(__name__)
app.register_blueprint(api_v1, url_prefix='/api/v1')
CORS(app)
# app.run(host='0.0.0.0')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
