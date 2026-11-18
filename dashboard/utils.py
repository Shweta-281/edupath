import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


def generate_report_card(student_profile, attendance_pct, avg_score, quiz_attempts):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#5B21B6'), alignment=1)
    subtitle_style = ParagraphStyle(name='SubStyle', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#64748B'), alignment=1, spaceAfter=20)
    
    elements.append(Paragraph("EduPath - Student Progress Report", title_style))
    elements.append(Paragraph(f"Generated on: {__import__('datetime').date.today().strftime('%d %B %Y')}", subtitle_style))
    
    student_info = [
        ["Student Name:", student_profile.user.get_full_name() or student_profile.user.username],
        ["Class & Board:", f"Class {student_profile.grade} · {student_profile.board}"],
        ["Email:", student_profile.user.email],
    ]
    
    t = Table(student_info, colWidths=[1.5*inch, 4.5*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#475569')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    risk_color = {'High Risk': '#DC2626', 'Medium Risk': '#D97706', 'Safe': '#16A34A'}.get(student_profile.risk_status['label'], '#0F172A')
    
    metrics_data = [
        ["Metric", "Result"],
        ["Attendance", f"{attendance_pct}%"],
        ["Average Quiz Score", f"{avg_score}%"],
        ["AI Risk Status", student_profile.risk_status['label']],
        ["XP Points Earned", f"{student_profile.xp_points} XP"],
    ]
    
    mt = Table(metrics_data, colWidths=[3*inch, 3*inch])
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#5B21B6')),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (1,-2), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('TEXTCOLOR', (1,3), (1,3), colors.HexColor(risk_color)),
        ('FONTNAME', (1,3), (1,3), 'Helvetica-Bold'),
    ]))
    elements.append(mt)
    elements.append(Spacer(1, 30))
    
    elements.append(Paragraph("Recent Quiz History", ParagraphStyle(name='H2', parent=styles['Heading2'], textColor=colors.HexColor('#0F172A'))))
    elements.append(Spacer(1, 10))
    
    quiz_data = [["Quiz Name", "Score", "Date"]]
    for attempt in quiz_attempts:
        quiz_data.append([
            attempt.quiz.title[:40],
            f"{attempt.score} / {attempt.quiz.total_marks} ({attempt.percentage()}%)",
            attempt.started_at.strftime("%d %b %Y")
        ])
        
    if len(quiz_data) == 1:
        quiz_data.append(["No quizzes attempted yet.", "-", "-"])
        
    qt = Table(quiz_data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
    qt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(qt)
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="EduPath_Report_{student_profile.user.username}.pdf"'
    return response


def generate_combined_report_card(children_data):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="children_report_cards.pdf"'

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="EduPath — Children's Report Cards",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'EduTitle', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor('#5B21B6'),
    )
    h2 = ParagraphStyle(
        'EduH2', parent=styles['Heading2'],
        fontSize=16, textColor=colors.HexColor('#0F172A'),
    )
    normal = styles['Normal']

    story = []

    story.append(Paragraph("EduPath — Children's Report Cards", title_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"Generated on {timezone.now().strftime('%d %b %Y, %I:%M %p')}",
        normal,
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Children included:", h2))
    for d in children_data:
        s = d['student']
        name = s.user.get_full_name() or s.user.username
        story.append(Paragraph(f"• {name} (Class {s.grade})", normal))
    story.append(PageBreak())

    for i, d in enumerate(children_data):
        s = d['student']
        name = s.user.get_full_name() or s.user.username

        story.append(Paragraph(name, h2))
        story.append(Paragraph(f"Class {s.grade} · {s.user.email}", normal))
        story.append(Spacer(1, 0.3 * cm))

        stats = [
            ['Metric', 'Value'],
            ['Attendance', f"{d['att_pct']}%"],
            ['Quiz Average', f"{d['avg_score']}%"],
            ['Quiz Attempts', str(len(d['attempts']))],
        ]
        t = Table(stats, colWidths=[6 * cm, 6 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B21B6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#F8FAFC')]),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.6 * cm))

        story.append(Paragraph("Recent Quizzes", h2))
        if d['attempts']:
            qdata = [['Quiz', 'Date', 'Score']]
            for a in d['attempts']:
                qdata.append([
                    a.quiz.title[:40],
                    a.started_at.strftime('%d %b %Y') if a.started_at else '-',
                    f"{a.percentage()}%",
                ])
            qt = Table(qdata, colWidths=[7 * cm, 4 * cm, 3 * cm])
            qt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDE9FE')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#5B21B6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(qt)
        else:
            story.append(Paragraph("No quiz attempts yet.", normal))

        if i < len(children_data) - 1:
            story.append(PageBreak())

    doc.build(story)
    return response


def _hex_to_rl(hex_str, fallback="#64748B"):
    try:
        h = (hex_str or fallback).lstrip('#')
        if len(h) != 6:
            h = fallback.lstrip('#')
        return colors.HexColor(f'#{h}')
    except Exception:
        return colors.HexColor(fallback)


def generate_class_report(teacher, students_data, summary):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="class_report_{timezone.now():%Y%m%d}.pdf"'
    )

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"EduPath — Class Report ({teacher.get_full_name() or teacher.username})",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'EduTitle', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor('#5B21B6'),
    )
    h2 = ParagraphStyle(
        'EduH2', parent=styles['Heading2'],
        fontSize=16, textColor=colors.HexColor('#0F172A'),
        spaceAfter=6,
    )
    normal = styles['Normal']
    small = ParagraphStyle('Small', parent=normal, fontSize=9)

    story = []

    story.append(Paragraph("EduPath — Class Report", title_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Teacher: <b>{teacher.get_full_name() or teacher.username}</b>",
        normal,
    ))
    story.append(Paragraph(
        f"Generated: {timezone.now().strftime('%d %b %Y, %I:%M %p')}",
        small,
    ))
    story.append(Spacer(1, 0.6 * cm))

    summary_data = [
        ['Students', 'Courses', 'Class Avg', 'High Risk', 'Medium', 'Safe'],
        [
            str(summary['total_students']),
            str(summary['total_courses']),
            f"{summary['class_avg']}%",
            str(summary['risk_high']),
            str(summary['risk_med']),
            str(summary['risk_safe']),
        ],
    ]
    st = Table(summary_data, colWidths=[3 * cm] * 6)
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B21B6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (3, 1), (3, 1), colors.HexColor('#FEE2E2')),
        ('BACKGROUND', (4, 1), (4, 1), colors.HexColor('#FEF3C7')),
        ('BACKGROUND', (5, 1), (5, 1), colors.HexColor('#DCFCE7')),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph("Student Overview", h2))
    overview_header = ['#', 'Student', 'Class', 'Courses', 'Avg Score', 'Attendance', 'Risk']
    overview_rows = [overview_header]
    for i, d in enumerate(students_data, start=1):
        s = d['student']
        name = s.user.get_full_name() or s.user.username
        overview_rows.append([
            str(i),
            name[:28],
            str(s.grade or '-'),
            str(len(d['courses'])),
            f"{d['avg_score']}%",
            f"{d['att_pct']}%",
            d['risk'].get('label', '-'),
        ])
    ot = Table(overview_rows,
               colWidths=[0.8 * cm, 4.5 * cm, 1.3 * cm, 1.5 * cm, 2 * cm, 2.2 * cm, 2.5 * cm],
               repeatRows=1)
    ot.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDE9FE')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#5B21B6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#F8FAFC')]),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(ot)
    story.append(PageBreak())

    for idx, d in enumerate(students_data):
        s = d['student']
        name = s.user.get_full_name() or s.user.username
        risk = d['risk'] or {}

        story.append(Paragraph(name, h2))
        story.append(Paragraph(f"Class {s.grade or '-'} · {s.user.email}", small))
        story.append(Spacer(1, 0.3 * cm))

        if risk.get('label'):
            banner = Table(
                [[f"AI Status: {risk.get('label')}", risk.get('msg', '')]],
                colWidths=[4 * cm, 12 * cm],
            )
            banner.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), _hex_to_rl(risk.get('bg', '#F8FAFC'))),
                ('TEXTCOLOR', (0, 0), (-1, -1), _hex_to_rl(risk.get('color', '#0F172A'))),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(banner)
            story.append(Spacer(1, 0.4 * cm))

        stats = [
            ['Quiz Average', 'Attendance', 'Enrolled Courses'],
            [f"{d['avg_score']}%", f"{d['att_pct']}%", str(len(d['courses']))],
        ]
        stt = Table(stats, colWidths=[5.3 * cm] * 3)
        stt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(stt)
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph("Courses with You", ParagraphStyle('H3', parent=h2, fontSize=12, spaceAfter=4)))
        if d['courses']:
            for c in d['courses']:
                story.append(Paragraph(f"• {c}", normal))
        else:
            story.append(Paragraph("No active enrollments in your courses.", normal))
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph("Recent Quizzes", ParagraphStyle('H3b', parent=h2, fontSize=12, spaceAfter=4)))
        if d['attempts']:
            qdata = [['Quiz', 'Date', 'Score']]
            for a in d['attempts']:
                qdata.append([
                    a.quiz.title[:45],
                    a.started_at.strftime('%d %b %Y') if a.started_at else '-',
                    f"{a.percentage()}%",
                ])
            qt = Table(qdata, colWidths=[8 * cm, 4 * cm, 3 * cm], repeatRows=1)
            qt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDE9FE')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#5B21B6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#F8FAFC')]),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(qt)
        else:
            story.append(Paragraph("No quiz attempts yet.", small))

        if idx < len(students_data) - 1:
            story.append(PageBreak())

    doc.build(story)
    return response


# ================================================================
# NEW: Teacher — Payout Statement PDF
# ================================================================
def generate_payout_statement(teacher, period_label, summary, course_rows, monthly_rows):
    """
    teacher      : User
    period_label : str, e.g. "All time" or "Nov 2026"
    summary      : dict { lifetime_gross, lifetime_teacher, lifetime_platform,
                          month_gross, month_teacher, month_platform,
                          year_gross, year_teacher }
    course_rows  : list of dicts { course_title, share_percent, enrollments,
                                    gross, teacher_earn, platform_earn }
    monthly_rows : list of dicts { label, gross, teacher_earn }
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="EduPath_Payout_{teacher.username}_{timezone.now():%Y%m%d}.pdf"'
    )

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"EduPath — Payout Statement ({teacher.get_full_name() or teacher.username})",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('EduTitle', parent=styles['Title'],
                                  fontSize=22, textColor=colors.HexColor('#5B21B6'))
    h2 = ParagraphStyle('EduH2', parent=styles['Heading2'],
                         fontSize=14, textColor=colors.HexColor('#0F172A'),
                         spaceBefore=6, spaceAfter=8)
    normal = styles['Normal']
    small = ParagraphStyle('Small', parent=normal, fontSize=9,
                            textColor=colors.HexColor('#64748B'))

    story = []

    # --- Header ---
    story.append(Paragraph("EduPath — Teacher Payout Statement", title_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Teacher: <b>{teacher.get_full_name() or teacher.username}</b> "
        f"({teacher.email or '—'})",
        normal,
    ))
    story.append(Paragraph(
        f"Period: <b>{period_label}</b> · Generated: {timezone.now().strftime('%d %b %Y, %I:%M %p')}",
        small,
    ))
    story.append(Spacer(1, 0.6 * cm))

    # --- Summary strip ---
    story.append(Paragraph("Summary", h2))
    summary_data = [
        ['Metric', 'This Month', 'This Year', 'Lifetime'],
        ['Gross Sales', f"₹{summary['month_gross']}", f"₹{summary['year_gross']}", f"₹{summary['lifetime_gross']}"],
        ['Your Earnings', f"₹{summary['month_teacher']}", f"₹{summary['year_teacher']}", f"₹{summary['lifetime_teacher']}"],
        ['Platform Fee', f"₹{summary['month_platform']}", f"₹{summary['year_platform']}", f"₹{summary['lifetime_platform']}"],
    ]
    st = Table(summary_data, colWidths=[3.5 * cm, 4 * cm, 4 * cm, 4.5 * cm])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B21B6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#F8FAFC')]),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#EDE9FE')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#5B21B6')),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.6 * cm))

    # --- Per-course breakdown ---
    if course_rows:
        story.append(Paragraph("Per-Course Breakdown", h2))
        c_head = ['Course', 'Share %', '# Paid', 'Gross', 'Your Share', 'Platform']
        c_data = [c_head]
        for r in course_rows:
            c_data.append([
                r['course_title'][:32],
                f"{r['share_percent']}%",
                str(r['enrollments']),
                f"₹{r['gross']}",
                f"₹{r['teacher_earn']}",
                f"₹{r['platform_earn']}",
            ])
        ct = Table(c_data,
                    colWidths=[5.5 * cm, 1.8 * cm, 1.5 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm],
                    repeatRows=1)
        ct.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDE9FE')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#5B21B6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#F8FAFC')]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(ct)
        story.append(Spacer(1, 0.6 * cm))

    # --- Monthly breakdown ---
    if monthly_rows:
        story.append(Paragraph("Last 12 Months", h2))
        m_head = ['Month', 'Gross Sales', 'Your Earnings']
        m_data = [m_head]
        for r in monthly_rows:
            m_data.append([r['label'], f"₹{r['gross']}", f"₹{r['teacher_earn']}"])
        mt = Table(m_data, colWidths=[5 * cm, 5 * cm, 5 * cm], repeatRows=1)
        mt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDE9FE')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#5B21B6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#F8FAFC')]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(mt)

    story.append(Spacer(1, 1 * cm))
    footer = ParagraphStyle('Footer', parent=normal, fontSize=9,
                             textColor=colors.HexColor('#94A3B8'), alignment=1)
    story.append(Paragraph(
        "This is a computer-generated statement. For payout queries, contact hello@edupath.in",
        footer,
    ))
    story.append(Paragraph("© 2026 EduPath. All rights reserved.", footer))

    doc.build(story)
    return response