# Nephro Expert 🩺
A web app that Automatically selects the most suitable GFR equation and calculate it based on patient data and provides drug-dose recommendations based on kidney function.

(eGFR) is the estmated Glomerular Filtration Rate it is a key indicator of kidney function, It is essential for diagnosing , staging and safely prescribing medications for CKD patients. eGFR is calculatd using different equations and not all estimation equations are equal — MDRD, CKD-EPI, and Cockcroft, can give very different results and patients like age, body size, and muscle mass influence which formula is most accurate. 

Overestimated GFR; Patients may get too much medication Risk of toxicity.
Underestimated GFR; Patients may get too little Risk of treatment.

So the idea of this project is to help the docotors to easly know which one is the most suitable GFR equation and get drug-dose recommendations based on its eGFR range.

## Features
- Smart eGFR Equation Selector and calculator
- Drug recommendation table based on eGFR ranges
- Clean UI

## Tech Stack
Python, Flask, HTML/CSS, Pandas/OpenPyXL

## Demo
- Live: https://nephro-expert.onrender.com
- Screen Recocrding: https://github.com/user-attachments/assets/9f7a175b-09e6-4db6-8309-6f82f62d2079

## Run Locally
```bash
git clone https://github.com/<your-username>/Nephro_Expert.git
cd Nephro_Expert
python -m venv venv
source venv/bin/activate  # mac/linux
pip install -r requirements.txt
python app.py
