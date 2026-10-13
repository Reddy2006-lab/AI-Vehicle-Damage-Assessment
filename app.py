from flask import Flask, render_template, request, send_from_directory
from ultralytics import YOLO
import os
import hashlib
import json
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
SAVED_CLAIMS_FILE = "saved_claims.json"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Your trained model
model = YOLO("runs/detect/vehicle_damage-5/weights/best.pt")


# -------------------------------------------------
# CREATE IMAGE HASH
# -------------------------------------------------

def image_hash(file):

    data = file.read()
    file.seek(0)

    return hashlib.sha256(data).hexdigest()


# -------------------------------------------------
# CHECK IF IMAGE IS ALREADY PROCESSED
# -------------------------------------------------

def check_duplicate(file):

    new_hash = image_hash(file)

    for name in os.listdir(UPLOAD_FOLDER):

        path = os.path.join(UPLOAD_FOLDER, name)

        if os.path.isfile(path):

            with open(path, "rb") as old_file:

                old_hash = hashlib.sha256(
                    old_file.read()
                ).hexdigest()

            if new_hash == old_hash:

                return True

    return False


# -------------------------------------------------
# SAVE CLAIM
# -------------------------------------------------

def save_claim(claim_data):

    if os.path.exists(SAVED_CLAIMS_FILE):

        try:

            with open(
                SAVED_CLAIMS_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                claims = json.load(file)

        except (json.JSONDecodeError, FileNotFoundError):

            claims = []

    else:

        claims = []


    claims.append(claim_data)


    with open(
        SAVED_CLAIMS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            claims,
            file,
            indent=4,
            ensure_ascii=False
        )


# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "index.html",
        message=None
    )


# -------------------------------------------------
# UPLOAD
# -------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():

    if "vehicle_image" not in request.files:

        return render_template(
            "index.html",
            message="⚠️ Please select an image."
        )


    image = request.files["vehicle_image"]


    if image.filename == "":

        return render_template(
            "index.html",
            message="⚠️ Please select an image."
        )


    # =============================================
    # DUPLICATE IMAGE CHECK
    # =============================================

    if check_duplicate(image):

        return render_template(

            "index.html",

            message=(
                "⚠️ This image has already been uploaded "
                "and the insurance claim has already been "
                "processed. Please upload a different image."
            )

        )


    # =============================================
    # SAVE IMAGE
    # =============================================

    image_path = os.path.join(
        UPLOAD_FOLDER,
        image.filename
    )

    image.save(image_path)


    # =============================================
    # YOLO DAMAGE DETECTION
    # =============================================

    results = model(image_path)

    detections = []


    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            confidence = float(box.conf[0])

            class_name = model.names[class_id]


            # -------------------------------------
            # DAMAGE INFORMATION
            # -------------------------------------

            if class_name == "doorouter-dent":

                part = "Door"
                damage = "Dent"
                cost = 12000


            elif class_name == "quaterpanel-dent":

                part = "Quarter Panel"
                damage = "Dent"
                cost = 13000


            elif class_name == "rear-bumper-dent":

                part = "Rear Bumper"
                damage = "Dent"
                cost = 14000


            elif class_name == "front-bumper-dent":

                part = "Front Bumper"
                damage = "Dent"
                cost = 14000


            elif class_name == "bonnet-dent":

                part = "Bonnet"
                damage = "Dent"
                cost = 15000


            elif class_name == "fender-dent":

                part = "Fender"
                damage = "Dent"
                cost = 11000


            elif class_name == "roof-dent":

                part = "Roof"
                damage = "Dent"
                cost = 18000


            elif class_name == "pillar-dent":

                part = "Pillar"
                damage = "Dent"
                cost = 16000


            elif class_name == "Headlight-Damage":

                part = "Headlight"
                damage = "Damage"
                cost = 9000


            elif class_name == "Taillight-Damage":

                part = "Taillight"
                damage = "Damage"
                cost = 7000


            elif class_name == "Sidemirror-Damage":

                part = "Side Mirror"
                damage = "Damage"
                cost = 6000


            else:

                part = class_name
                damage = "Damage"
                cost = 10000


            # -------------------------------------
            # CONFIDENCE
            # -------------------------------------

            confidence_percent = round(
                confidence * 100,
                2
            )


            # -------------------------------------
            # SEVERITY + CLAIM
            # -------------------------------------

            if confidence_percent >= 80:

                severity = "Severe"
                claim = round(cost * 0.80)


            elif confidence_percent >= 60:

                severity = "Moderate"
                claim = round(cost * 0.70)


            else:

                severity = "Minor"
                claim = round(cost * 0.60)


            detections.append({

                "vehicle_part": part,

                "damage_type": damage,

                "severity": severity,

                "confidence": confidence_percent,

                "repair_cost": cost,

                "insurance_claim": claim

            })


    # =============================================
    # REMOVE DUPLICATE VEHICLE PARTS
    # KEEP HIGHEST CONFIDENCE
    # =============================================

    unique = {}


    for detection in detections:

        part = detection["vehicle_part"]


        if part not in unique:

            unique[part] = detection


        elif (
            detection["confidence"]
            > unique[part]["confidence"]
        ):

            unique[part] = detection


    detections = list(unique.values())


    # =============================================
    # CREATE CLAIM ID
    # =============================================

    claim_id = (
        "CLM-"
        + datetime.now().strftime("%Y%m%d%H%M%S")
    )


    # =============================================
    # SAVE CLAIM INFORMATION
    # =============================================

    claim_data = {

        "claim_id": claim_id,

        "image": image.filename,

        "date": datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        ),

        "status": "Processed",

        "saved": True,

        "plate_number": "Not Detected",

        "detections": detections

    }


    save_claim(claim_data)


    # =============================================
    # SHOW RESULT
    # =============================================

    return render_template(

        "result.html",

        filename=image.filename,

        detections=detections,

        claim_id=claim_id,

        saved=True,

        plate_number="Not Detected"

    )


# -------------------------------------------------
# DISPLAY IMAGE
# -------------------------------------------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# -------------------------------------------------
# VIEW SAVED CLAIMS
# -------------------------------------------------

@app.route("/saved")
def saved_claims():

    if os.path.exists(SAVED_CLAIMS_FILE):

        try:

            with open(
                SAVED_CLAIMS_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                claims = json.load(file)

        except (json.JSONDecodeError, FileNotFoundError):

            claims = []

    else:

        claims = []


    return render_template(
        "saved.html",
        claims=claims
    )


# -------------------------------------------------
# START FLASK
# -------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)