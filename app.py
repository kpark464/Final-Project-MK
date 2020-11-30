"""
Simple "Hello, World" application using Flask
"""

from flask import Flask
from flask import render_template
from flask import url_for
from flask import request, redirect, json
from werkzeug.exceptions import HTTPException

import mbta_helper

app = Flask(__name__)


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/nearest', methods=["POST"])
def get_nearest_stop():
    place_name = request.form['placeName']
    if not place_name.strip() == "":
        nearest_stop = mbta_helper.find_stop_near(place_name)
        return render_template('mbta_station.html', nearest_stop=nearest_stop)
    else:
        return redirect(url_for('main_page'))


@app.route('/backToHome', methods=["POST"])
def back_to_home():
    return redirect(url_for('main_page'))


@app.errorhandler(HTTPException)
def error_page(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    # response = e.get_response()
    # replace the body with JSON
    error_data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })

    error_msg = json.loads(error_data)
    return render_template('error.html', error=error_msg)
    # return response
