import sys, os
from flask import Flask, request, render_template
from .main import main
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "./uploads"
ALLOWED_EXTENSIONS = {"ipynb"}

app = Flask(__name__, template_folder="../uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.post("/upload")
def upload():
    file = request.files["file"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # TODO: save in parent folder ?
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return filename


@app.get("/analyze/<filename>")
def analyze(filename):
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    sys.argv = ["src.main", filename, "-o"]
    main(filepath)
    htmlfilepath = f"{filename[:-3]}.html"
    return render_template(htmlfilepath)
