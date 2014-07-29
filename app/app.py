from flask import Flask, jsonify, request
from access_control_decorator import crossdomain
from worker import work

app = Flask(__name__)
app.config.from_envvar('OAH_SETTINGS')


@app.route('/rate-checker')
def rate_checker():
    return jsonify(**work(request))


@app.route('/county-limit')
@app.route('/county-limit/list')
@crossdomain(origin='*')
def county_limit():
    return jsonify(**work(request))


if __name__ == '__main__':
    app.run()
