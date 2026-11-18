# courses/utils.py
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.http import HttpResponse
import io
from datetime import date


def generate_certificate(student_name, course_name, teacher_name, serial=None, issued_on=None):
    """Render a landscape A4 certificate. `serial` and `issued_on` are optional
    so existing callers keep working, but the view now always passes them."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Borders
    p.setStrokeColor(colors.HexColor('#5B21B6'))
    p.setLineWidth(10)
    p.rect(20, 20, width - 40, height - 40)

    p.setStrokeColor(colors.HexColor('#A78BFA'))
    p.setLineWidth(2)
    p.rect(35, 35, width - 70, height - 70)

    # Title
    p.setFont("Helvetica-Bold", 36)
    p.setFillColor(colors.HexColor('#0F172A'))
    p.drawCentredString(width / 2.0, height - 120, "CERTIFICATE OF COMPLETION")

    p.setFont("Helvetica", 16)
    p.setFillColor(colors.HexColor('#64748B'))
    p.drawCentredString(width / 2.0, height - 160, "This certificate is proudly presented to")

    # Student name
    p.setFont("Times-BoldItalic", 48)
    p.setFillColor(colors.HexColor('#5B21B6'))
    p.drawCentredString(width / 2.0, height - 240, student_name)

    p.setStrokeColor(colors.HexColor('#CBD5E1'))
    p.setLineWidth(1)
    p.line(width / 2.0 - 200, height - 255, width / 2.0 + 200, height - 255)

    # Course
    p.setFont("Helvetica", 16)
    p.setFillColor(colors.HexColor('#64748B'))
    p.drawCentredString(width / 2.0, height - 300, "For successfully completing the course")

    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#0F172A'))
    p.drawCentredString(width / 2.0, height - 340, course_name)

    # Date + signature
    p.setFont("Helvetica", 14)
    p.setFillColor(colors.HexColor('#64748B'))
    issue_date = issued_on or date.today()
    p.drawString(100, 100, f"Date: {issue_date.strftime('%d %B %Y')}")

    p.drawString(width - 300, 100, "________________________")
    p.drawString(width - 280, 80, f"{teacher_name}")
    p.drawString(width - 280, 60, "Course Instructor")

    # Serial (bottom-left, subtle)
    if serial:
        p.setFont("Helvetica", 9)
        p.setFillColor(colors.HexColor('#94A3B8'))
        p.drawString(100, 65, f"Certificate ID: {serial}")
        p.drawString(100, 52, "Verify at: /courses/certificate/verify/")

    # Seal
    p.setFillColor(colors.HexColor('#F59E0B'))
    p.circle(width / 2.0, 100, 40, stroke=0, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2.0, 95, "EDUPATH")
    p.drawCentredString(width / 2.0, 80, "CERTIFIED")

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    safe_name = student_name.replace(" ", "_")
    response['Content-Disposition'] = f'attachment; filename="EduPath_Certificate_{safe_name}.pdf"'
    return response