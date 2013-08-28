from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/callback")
@app.route("/callback.html")
def callback():
    return render_template('callback.html')

if __name__ == "__main__":
    app.run()
