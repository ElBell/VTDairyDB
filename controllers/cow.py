__author__ = 'Eleonor Bart'

from main import app


@app.route('/cow', methods=['GET', 'POST'])
def hello_cow():
    return 'M<i>ooooo</i>'

