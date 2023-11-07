"""

 OMRChecker

 Author: Udayraj Deshmukh
 Github: https://github.com/Udayraj123

"""

import argparse
import json
import os
import sys
from pathlib import Path

import cv2
from flask import Flask
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

from src.entry import entry_point
from src.logger import logger


def parse_args():
    # construct the argument parse and parse the arguments
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        "-i",
        "--inputDir",
        default=["inputs"],
        # https://docs.python.org/3/library/argparse.html#nargs
        nargs="*",
        required=False,
        type=str,
        dest="input_paths",
        help="Specify an input directory.",
    )

    argparser.add_argument(
        "-d",
        "--debug",
        required=False,
        dest="debug",
        action="store_false",
        help="Enables debugging mode for showing detailed errors",
    )

    argparser.add_argument(
        "-o",
        "--outputDir",
        default="outputs",
        required=False,
        dest="output_dir",
        help="Specify an output directory.",
    )

    argparser.add_argument(
        "-a",
        "--autoAlign",
        required=False,
        dest="autoAlign",
        action="store_true",
        help="(experimental) Enables automatic template alignment - \
        use if the scans show slight misalignments.",
    )

    argparser.add_argument(
        "-l",
        "--setLayout",
        required=False,
        dest="setLayout",
        action="store_true",
        help="Set up OMR template layout - modify your json file and \
        run again until the template is set.",
    )

    (
        args,
        unknown,
    ) = argparser.parse_known_args()

    args = vars(args)

    if len(unknown) > 0:
        logger.warning(f"\nError: Unknown arguments: {unknown}", unknown)
        argparser.print_help()
        exit(11)
    return args


def entry_point_for_args(args):
    if args["debug"] is True:
        # Disable tracebacks
        sys.tracebacklimit = 0
    for root in args["input_paths"]:
        return entry_point(
            Path(root),
            args,
        )



ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = ROOT_DIR + '/inputs'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def remove_old_files(filename):
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    os.remove(os.path.join(ROOT_DIR + "/outputs/CheckedOMRs", filename))
    pass


@app.route('/upload_test', methods=["POST"])
def upload_file():
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No file part')
            return json.dumps({"message": "bad request", "error": "no file found"})
        files = request.files.getlist('files')

        for file in files:
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        args = parse_args()
        result = entry_point_for_args(args)

        results = []
        x = 0
        for res in result:
            filename = files[x].filename
            qrData = read_qr(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            data = json.loads(qrData[0])
            results.append({"result": res, "data": data})
            x += 1

        for file in files:
            remove_old_files(file.filename)
        return json.dumps({"message": "ok", "results": results})
    return json.dumps({"message": "bad request"})


def read_qr(filepath):
    try:
        img = cv2.imread(filepath)
        detect = cv2.QRCodeDetector()
        retval, decoded_info, points, straight_qrcode = detect.detectAndDecodeMulti(img)
        if retval:
            return decoded_info
    except:
        print("ERROR")
        return


if __name__ == "__main__":
    app.secret_key = 'super secrey'
    app.run(debug=True, port=5069)
