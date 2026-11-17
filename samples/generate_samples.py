"""Generate three SYNTHETIC clinical PDFs (all names, IDs and facilities are invented).

    pip install reportlab
    python samples/generate_samples.py

01 and 02 use "Label: value" + bulleted sections (the mock provider handles these).
03 is a free-text referral letter: the mock gets little from it, a real LLM gets nearly everything.
"""
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).parent
styles = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=15, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=styles["Heading3"], fontSize=11, spaceBefore=8, spaceAfter=2)
BODY = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=13)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, textColor="#666666")

BANNER = "SYNTHETIC TEST DOCUMENT - fictitious patient, not real medical data"


def build(filename: str, blocks: list):
    doc = SimpleDocTemplate(str(OUT / filename), pagesize=letter,
                            leftMargin=0.8 * inch, rightMargin=0.8 * inch, topMargin=0.7 * inch)
    story = []
    for kind, text in blocks:
        if kind == "h1":
            story.append(Paragraph(text, H1))
        elif kind == "h2":
            story.append(Paragraph(text, H2))
        elif kind == "kv":
            story.append(Paragraph(text, BODY))
        elif kind == "li":
            story.append(Paragraph(f"- {text}", BODY))
        elif kind == "p":
            story.append(Paragraph(text, BODY))
            story.append(Spacer(1, 6))
        elif kind == "small":
            story.append(Paragraph(text, SMALL))
            story.append(Spacer(1, 6))
    doc.build(story)
    print("wrote", OUT / filename)


def section(title: str, items: list[str]) -> list:
    return [("h2", f"{title}:")] + [("li", i) for i in items]


discharge = (
    [("h1", "Riverbend General Hospital"), ("small", BANNER), ("h2", "DISCHARGE SUMMARY")]
    + [("kv", line) for line in [
        "Patient Name: Maria Delgado", "Date of Birth: 1961-03-14", "Sex: Female", "MRN: RGH-0048213",
        "Admission Date: 2026-10-02", "Discharge Date: 2026-10-06", "Department: Internal Medicine",
        "Attending Physician: Dr. Samuel Okafor, MD",
    ]]
    + section("Diagnoses", [
        "Community-acquired pneumonia, right lower lobe (J18.9) - primary",
        "Type 2 diabetes mellitus without complications (E11.9) - chronic",
        "Essential hypertension (I10) - chronic",
        "Hypokalemia (E87.6) - resolved",
    ])
    + section("Allergies", ["Penicillin (rash)", "Sulfa drugs (hives)"])
    + section("Social History", [
        "Former smoker, quit 2010 (20 pack-years)",
        "Alcohol: 1-2 glasses of wine per week",
        "Retired teacher, lives with her husband",
    ])
    + section("Vitals at Discharge", [
        "Blood Pressure: 132/84 mmHg", "Heart Rate: 78 bpm", "Temperature: 98.4 F", "SpO2: 96 %",
    ])
    + section("Lab Results", [
        "WBC: 13.8 x10^3/uL (ref 4.0-11.0) H",
        "Hemoglobin A1c: 8.1 % (ref 4.0-5.6) H",
        "Creatinine: 0.9 mg/dL (ref 0.6-1.2)",
        "Potassium: 3.3 mmol/L (ref 3.5-5.1) L",
        "Procalcitonin: 0.62 ng/mL (ref 0.00-0.25) H",
    ])
    + section("Procedures", ["Chest X-ray, PA and lateral", "Blood cultures x2 (no growth at 48 hours)"])
    + [("h2", "Hospital Course:"),
       ("p", "64-year-old woman admitted with three days of productive cough, fever to 101.8 F and right-sided "
             "pleuritic chest pain. Chest X-ray showed right lower lobe consolidation. Treated with IV "
             "levofloxacin given the penicillin allergy, with defervescence by day 2. Potassium was repleted. "
             "Glucose was managed with sliding-scale insulin and metformin was resumed at discharge.")]
    + section("Discharge Medications", [
        "Levofloxacin 750 mg PO once daily for 3 more days (new)",
        "Metformin 1000 mg PO twice daily (continued)",
        "Lisinopril 10 mg PO once daily (continued)",
        "Potassium chloride 20 mEq PO once daily for 3 days (new)",
    ])
    + section("Follow-up", [
        "Primary care with Dr. Lena Park in 7 days",
        "Repeat chest X-ray in 6 weeks to confirm resolution",
        "Return to ED for fever above 101 F or worsening shortness of breath",
    ])
)

lab = (
    [("h1", "Lakeside Diagnostics Laboratory"), ("small", BANNER), ("h2", "LABORATORY REPORT")]
    + [("kv", line) for line in [
        "Patient Name: James Whitfield", "Date of Birth: 1978-11-02", "Sex: Male", "MRN: LDL-552190",
        "Collection Date: 2026-11-03", "Ordering Provider: Dr. Priya Raman, MD",
    ]]
    + section("Reason for Testing", [
        "Hyperlipidemia, unspecified (E78.5)", "Prediabetes (R73.03)",
    ])
    + section("Lab Results", [
        "Total Cholesterol: 246 mg/dL (ref 0-199) H",
        "LDL Cholesterol: 168 mg/dL (ref 0-99) H",
        "HDL Cholesterol: 38 mg/dL (ref 40-200) L",
        "Triglycerides: 201 mg/dL (ref 0-149) H",
        "Fasting Glucose: 112 mg/dL (ref 70-99) H",
        "Hemoglobin A1c: 6.1 % (ref 4.0-5.6) H",
        "ALT: 34 U/L (ref 7-56)",
        "TSH: 2.1 mIU/L (ref 0.4-4.0)",
        "eGFR: 94 mL/min/1.73m2 (ref 60-120)",
    ])
    + section("Current Medications", ["Atorvastatin 20 mg PO once daily (continued)"])
    + [("h2", "Comments:"),
       ("p", "Fasting specimen (12 hours). LDL above goal on current statin dose; consider dose adjustment. "
             "A1c in prediabetes range, up from 5.8 % in 2025.")]
)

referral = [
    ("h1", "Northside Family Medicine"), ("small", BANNER), ("h2", "REFERRAL LETTER - CARDIOLOGY"),
    ("p", "November 10, 2026"),
    ("p", "Dear Dr. Haddad,"),
    ("p", "I am referring Mr. Robert Chen (born July 22, 1955; chart number NFM-77104) for outpatient "
          "cardiology evaluation of exertional chest discomfort. Over the past six weeks he has noticed a "
          "pressure-like sensation in his chest after climbing two flights of stairs, relieved within five "
          "minutes by rest. He denies symptoms at rest, syncope or palpitations."),
    ("p", "His history includes hypertension, hyperlipidemia and chronic kidney disease stage 3a. He quit "
          "smoking in 2015 after a 30 pack-year history. His father had a myocardial infarction at age 58."),
    ("p", "In clinic today his blood pressure was 148/92 mmHg, heart rate 84 bpm and BMI 29.4. A resting ECG "
          "showed normal sinus rhythm with nonspecific T-wave flattening in the lateral leads. Recent labs: "
          "LDL 131 mg/dL, creatinine 1.4 mg/dL (eGFR 52), and a high-sensitivity troponin within normal limits."),
    ("p", "Current medications are amlodipine 10 mg daily, losartan 50 mg daily and rosuvastatin 10 mg at "
          "bedtime. I have started aspirin 81 mg daily and given him sublingual nitroglycerin 0.4 mg to use as "
          "needed. He is allergic to codeine, which causes nausea."),
    ("p", "I would appreciate your assessment, including whether stress testing or coronary CT angiography "
          "is appropriate. I have asked him to call 911 for chest pain at rest or lasting more than 15 minutes, "
          "and I will see him back in four weeks."),
    ("p", "Sincerely,<br/>Dr. Ana Torres, MD<br/>Northside Family Medicine"),
]

if __name__ == "__main__":
    build("01_discharge_summary.pdf", discharge)
    build("02_lab_report.pdf", lab)
    build("03_referral_letter.pdf", referral)
