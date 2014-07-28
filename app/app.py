from flask import Flask
from access_control_decorator import crossdomain

app = Flask(__name__)
app.config.from_envvar('OAH_SETTINGS')


@app.route('/rate-checker')
def rate_checker():
    return "Rate checker"


@app.route('/county-limit')
@app.route('/county-limit/list')
@crossdomain(origin='*')
def county_limit():
    return "County limit"


if __name__ == '__main__':
    app.run()
