import bottle
from bottle import template, static_file, run
from pathlib import Path

app = bottle.app()

picdir = Path("Pictures")
files = [str(ii.relative_to(picdir)) for ii in picdir.glob("**/*.jpg")]
current_idx = 0


@app.route("/")
def root():
    global current_idx, picdir, files
    file_name = files[current_idx]
    current_idx += 1
    if current_idx >= len(files):
        current_idx = 0
    return template("server/index.html", filename=file_name)


@app.route("/image/<file_name:path>")
def load_image(file_name):
    global picdir
    return static_file(file_name, root=picdir)


run(app, host="0.0.0.0", port=8080)
