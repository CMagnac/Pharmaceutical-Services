from datetime import date
import io
import json

from flask import Flask, render_template, send_file, request
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

app = Flask(__name__)

with open("forms.json", encoding="utf-8") as f:
    FORMS = json.load(f)

@app.route("/")
def index():
    return render_template("index.html", forms=FORMS)

@app.route("/questionnaire/<form_id>")
def questionnaire(form_id):
    form = FORMS.get(form_id)
    if not form:
        return "Form not found", 404
    return render_template("questionnaire.html", form=form)

@app.context_processor
def inject_today_date():
    return {
        "current_date": date.today().isoformat()
    }

def wrap_text(text, font, font_size, max_width):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test_line = line + word + " "
        if stringWidth(test_line, font, font_size) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word + " "
    lines.append(line)
    return lines

def clean_text(t):
    if not t:
        return ""
    return (t.replace("\u00A0", " ")   # non-breaking space
             .replace("“", "\"")
             .replace("”", "\"")
             .replace("’", "'"))

@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():

    # Collect patient info 1

    date_jour = clean_text(request.form.get("date_jour", ""))
    nom_prenom = clean_text(request.form.get("nom_prenom", ""))
    num_secu = clean_text(request.form.get("num_secu", ""))
    medecin_traitant = clean_text(request.form.get("medecin_traitant", ""))
    age = clean_text(request.form.get("age", ""))

    # Collect patient info 2 (eligibility information)

    maladies_intervention_chir = clean_text(request.form.get("maladies_intervention_chir", ""))
    allergies_intolerances = clean_text(request.form.get("allergies_intolérances", ""))
    traitements_medic = clean_text(request.form.get("traitements_medic", ""))
    evenement_marquant = clean_text(request.form.get("événement_marquant", ""))
    autre_point = clean_text(request.form.get("autre_point", ""))
    
    # Collect selected criteria
    criteres = [clean_text(c) for c in request.form.getlist("criteria")]

    # Create PDF in memory
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    # Font
    pdf.setFont("Helvetica", 12)
    y = 800
    left_margin = 50
    max_width = 500  # max line width before wrapping
    y = 800  # vertical position

    # Title
    pdf.setFont("Helvetica", 16)
    pdf.drawString(left_margin, y, "Questionnaire Cystite")
    y -= 40

    pdf.setFont("Helvetica", 12)

    # Patient info 1
    infos1 = [
        f"Date du jour : {date_jour}",
        f"Nom / Prénom : {nom_prenom}",
        f"N° Sécurité Sociale : {num_secu}",
        f"Médecin traitant : {medecin_traitant}",
        f"Âge : {age}"
    ]

    pdf.drawString(left_margin, y, "Informations Patient :")
    y -= 25

    for info in infos1:
        pdf.drawString(left_margin + 20, y, info)
        y -= 20

    y -= 20
    pdf.setFont("Helvetica", 14)
    pdf.drawString(left_margin, y, "Critères sélectionnés :")
    y -= 30

    pdf.setFont("Helvetica", 12)

    # Criteria with line-wrapping
    for critere in criteres:
        wrapped_lines = wrap_text(critere, "Helvetica", 12, max_width)
        for line in wrapped_lines:
            pdf.drawString(left_margin + 20, y, "- " + line.strip())
            y -= 18
            if y < 60:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = 800

    # Patient info 2
    infos2 = [
        f"maladies_intervention_chir : {maladies_intervention_chir}",
        f"allergies_intolerances : {allergies_intolerances}",
        f"traitements_medic : {traitements_medic}",
        f"evenement_marquant : {evenement_marquant}",
        f"autre_point : {autre_point}"
    ]

    pdf.drawString(left_margin, y, "Informations Patient :")
    y -= 25

    for info in infos2:
        pdf.drawString(left_margin + 20, y, info)
        y -= 20

    pdf.save()
    buffer.seek(0)

    return send_file(buffer,
                     as_attachment=True,
                     download_name="questionnaire_cystite.pdf",
                     mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
