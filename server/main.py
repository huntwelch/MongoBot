from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack

app = Flask(__name__)

print __name__

@app.route("/")
def index():
    return "Hello Phil."

    if __name__ == "__main__":
        app.run()
