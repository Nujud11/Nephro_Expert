from flask import Flask, render_template, request
from datetime import datetime
import math
import pandas as pd

app = Flask(__name__)

# Load drug data from Excel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, 'static', 'drug_data.xlsx')

try:
    drug_df = pd.read_excel(EXCEL_PATH)
except Exception as e:
    drug_df = pd.DataFrame()
    print("Error loading drug data:", e)

def calculate_age(birthday_str):
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d")
    today = datetime.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

def get_recommendations_from_df(egfr_value):
    if drug_df.empty:
        return []

    recommendations = []
    for drug in drug_df["Drug"].unique():
        sub_df = drug_df[drug_df["Drug"] == drug]
        selected = None
        for _, row in sub_df.iterrows():
            range_str = str(row["eGFR Range"]).strip()
            try:
                if ">=" in range_str:
                    threshold = float(range_str.replace(">=", "").strip())
                    if egfr_value >= threshold:
                        selected = row
                        break
                elif "<" in range_str:
                    threshold = float(range_str.replace("<", "").strip())
                    if egfr_value < threshold:
                        selected = row
                        break
                elif "–" in range_str or "-" in range_str:
                    parts = range_str.replace("–", "-").split("-")
                    low, high = float(parts[0]), float(parts[1])
                    if low <= egfr_value <= high:
                        selected = row
                        break
            except:
                continue

        if selected is not None:
            recommendations.append({
                "drug": selected["Drug"],
                "egfr_range": selected["eGFR Range"],
                "adjustment": selected["Dose Adjustment"],
                "comments": selected["Comments"],
                "reference": selected["Reference"]
            })
    return recommendations

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/calculator", methods=["GET", "POST"])
def index():
    result = ""
    reason = ""
    bmi_note = ""
    egfr_value = None
    age = None
    birthday = ""
    gender = ""
    weight = ""
    height_cm = ""
    creatinine = ""
    scr = None
    cystatin = ""
    race = ""
    stability = ""
    equation = ""
    recommendations = []

    if request.method == "POST":
        try:
            birthday = request.form.get("birthday")
            age = calculate_age(birthday)
            gender = request.form.get("gender")
            weight = float(request.form.get("weight"))
            height_cm = float(request.form.get("height"))
            height = height_cm / 100
            scr = float(request.form.get("creatinine"))
            cystatin_raw = request.form.get("cystatin")
            cystatin = float(cystatin_raw) if cystatin_raw else None
            race = request.form.get("race")
            stability = request.form.get("stability")
            preferred_equation = request.form.get("equation")

            if stability == "Unstable":
                result = "This calculator is designed for stable renal function only."
                reason = "eGFR estimation is not valid for patients with acute changes in kidney function."
                return render_template("index.html", result=result, reason=reason, age=age, birthday=birthday)

            if age < 18:
                result = "This calculator does not support pediatric patients (<18 years old)."
                reason = "Use pediatric nephrology tools for patients under 18."
                return render_template("index.html", result=result, reason=reason, age=age, birthday=birthday)

            bmi = weight / (height ** 2)
            if bmi >= 35:
                bmi_note = f"Patient is classified as obese (BMI = {bmi:.1f}), which significantly impacts creatinine-based estimations."
            elif bmi >= 30:
                bmi_note = f"Patient is overweight (BMI = {bmi:.1f}), but below the threshold for switching to MDRD."
            else:
                bmi_note = f"Patient BMI = {bmi:.1f} (Normal or underweight)."

            equation = ""

            if preferred_equation == "ckd_epi_both" and cystatin is not None:
                equation = "CKD-EPI (Creatinine + Cystatin C)"
                eGFR = 135 * min(scr/0.9, 1)**-0.544 * max(scr/0.9, 1)**-0.544 * \
                       min(cystatin/0.8, 1)**-0.323 * max(cystatin/0.8, 1)**-0.778 * \
                       (0.996 ** age) * (0.963 if gender == "Female" else 1)
                reason = "Manually selected: Using both creatinine and cystatin C improves accuracy."

            elif preferred_equation == "ckd_epi_creatinine":
                equation = "CKD-EPI (Creatinine)"
                eGFR = 141 * min(scr/0.9, 1)**-0.411 * max(scr/0.9, 1)**-1.209 * \
                       (0.993 ** age) * (1.018 if gender == "Female" else 1)
                reason = "Manually selected: CKD-EPI (Creatinine) for general stable kidney function."

            elif preferred_equation == "mdrd":
                equation = "MDRD"
                eGFR = 186 * (scr ** -1.154) * (age ** -0.203)
                eGFR *= 0.742 if gender == "Female" else 1
                eGFR *= 1.212 if race == "Black" else 1
                reason = "Manually selected: MDRD is validated for moderate to severe CKD." 
                if race == "Black":
                    reason+= "\nThe eGFR adjusted for Black race as per equation guidelines."

            elif preferred_equation == "cockcroft_gault":
                equation = "Cockcroft-Gault"
                eGFR = ((140 - age) * weight) / (72 * scr)
                if gender == "Female":
                    eGFR *= 0.85
                reason = "Manually selected: Used commonly for drug dosing."

            else:
                if cystatin is not None:
                    equation = "CKD-EPI (Creatinine + Cystatin C)"
                    eGFR = 135 * min(scr/0.9, 1)**-0.544 * max(scr/0.9, 1)**-0.544 * \
                           min(cystatin/0.8, 1)**-0.323 * max(cystatin/0.8, 1)**-0.778 * \
                           (0.996 ** age) * (0.963 if gender == "Female" else 1)
                    reason = "Auto-selected: Most accurate with both biomarkers."
                elif bmi >= 35:
                    equation = "MDRD"
                    eGFR = 186 * (scr ** -1.154) * (age ** -0.203)
                    eGFR *= 0.742 if gender == "Female" else 1
                    eGFR *= 1.212 if race == "Black" else 1
                    reason = "Auto-selected: MDRD preferred for BMI ≥ 35."
                    if race == "Black":
                        reason+= "\nThe eGFR adjusted for Black race as per equation guidelines."
                elif age >= 65:
                    equation = "Cockcroft-Gault"
                    eGFR = ((140 - age) * weight) / (72 * scr)
                    if gender == "Female":
                        eGFR *= 0.85
                    reason = "Auto-selected: Elderly patient, weight available."
                else:
                    equation = "CKD-EPI (Creatinine)"
                    eGFR = 141 * min(scr/0.9, 1)**-0.411 * max(scr/0.9, 1)**-1.209 * \
                           (0.993 ** age) * (1.018 if gender == "Female" else 1)
                    reason = "Auto-selected: Default and validated for most adults."

            egfr_value = round(eGFR, 2)
            result = f"eGFR: {egfr_value:.2f} mL/min/1.73m²\nEquation: {equation}\n{bmi_note}"

            recommendations = get_recommendations_from_df(egfr_value) if egfr_value else []

        except Exception as e:
            result = f"Error: {str(e)}"

    return render_template("index.html",
        result=result,
        reason=reason,
        birthday=birthday,
        age=age,
        gender=gender,
        weight=weight,
        height=height_cm,
        creatinine=scr,
        cystatin=cystatin,
        race=race,
        stability=stability,
        equation=equation,
        egfr=egfr_value,
        recommendations=recommendations
    )

@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True, port=5056)
