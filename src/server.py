import sys, os
from yaml import Loader, load
from flask import Flask, request, Response
from .main import main
from werkzeug.utils import secure_filename
from flask_swagger_ui import get_swaggerui_blueprint

UPLOAD_FOLDER = "/var/www/uploads"
ALLOWED_EXTENSIONS = {"ipynb"}
SWAGGER_URL = '/api/docs'
API_URL = './static/swagger.yml'

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

swagger_yml = load(open(API_URL, 'r'), Loader=Loader)
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config = {
        'app_name': "leakage-analysis API",
        'spec': swagger_yml,
    },
)
app.register_blueprint(swaggerui_blueprint)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.post("/upload")
def upload():
    file = request.files["file"]
    if not file:
        return "No file sent", 400
    if not allowed_file(file.filename):
        return "File not allowed", 400
    filename = secure_filename(file.filename)
    # TODO: save in parent folder ?
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return filename


@app.get("/analyze/<filename>")
def analyze(filename):
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(filepath):
        return "File not found", 404
    sys.argv = ["src.main", filepath]
    try:
        main(filepath)
    except Exception as e:
        return "Error occured during analysis", 500
    htmlfilepath = os.path.join(app.config["UPLOAD_FOLDER"], f"{filename[:-6]}_results.json")
    if (os.path.isfile(htmlfilepath)):
        return Response(open(htmlfilepath, "r"), mimetype='application/json')
    else:
        return "No report file produced", 500
