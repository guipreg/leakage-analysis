import sys, os
from yaml import Loader, load
from flask import Flask, request, Response
from werkzeug.utils import secure_filename
from flask_swagger_ui import get_swaggerui_blueprint
from .main import main

UPLOAD_FOLDER = "/var/www/uploads"
ALLOWED_EXTENSIONS = {"ipynb", "py"}
SWAGGER_URL = "/api/docs"
API_URL = "./static/swagger.yml"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

swagger_yml = load(open(API_URL, "r", encoding="utf-8"), Loader=Loader)
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "leakage-analysis API",
        "spec": swagger_yml,
    },
)
app.register_blueprint(swaggerui_blueprint)


class APIError(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


@app.errorhandler(APIError)
def default_error_handler(e):
    return {"message": e.message}, e.code


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.post("/analyze")
def analyze():
    filename = upload_file(request)
    return analyze_file(filename)


def upload_file(req):
    if "file" not in req.files:
        raise APIError("No file sent", 400)
    file = req.files["file"]
    if not allowed_file(file.filename):
        raise APIError("File not allowed", 400)
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    if not os.path.isfile(filepath):
        raise APIError("File could not be uploaded", 500)
    return filename


def analyze_file(filename):
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    sys.argv = ["src.main", filepath]
    try:
        main(filepath)
    except Exception as e:
        raise APIError("Error occured during analysis", 500) from e

    if filename.endswith("ipynb"):
        jsonpath = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{filename[:-6]}_results.json"
        )
    elif filename.endswith("py"):
        jsonpath = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{filename[:-3]}_results.json"
        )
    if not os.path.isfile(jsonpath):
        raise APIError("No result was produced from analysis", 500)
    return Response(open(jsonpath, "r", encoding="utf-8"), mimetype="application/json")
