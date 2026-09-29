import io
import json
from datetime import datetime
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


class ReportGenerator:
    """
    Generates downloadable incident investigation reports in PDF and JSON formats.
    Complies with PRD Section 4.6 and Section 6.
    """

    def generate_json_report(self, incident: Dict[str, Any]) -> str:
        """Returns structured JSON serialization of the incident."""
        export_payload = {
            "report_generated_at": datetime.utcnow().isoformat(),
            "generator": "TRACE AI Incident Platform v1.0",
            "incident": incident
        }
        return json.dumps(export_payload, default=str, indent=2)

    def generate_pdf_report(self, incident: Dict[str, Any]) -> bytes:
        """
        Generates a polished, professional PDF report using ReportLab.
        Adheres to executive reporting standards with severity-based coloring.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1e293b")
        )
        
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b")
        )

        heading_style = ParagraphStyle(
            "HeadingSection",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white
        )

        table_body_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1e293b")
        )

        story = []

        # 1. Header
        story.append(Paragraph("TRACE AI &bull; INCIDENT INVESTIGATION REPORT", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} &bull; Analysis Platform Version 1.0",
            subtitle_style
        ))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=14))

        # 2. Key Metadata Table
        sev = incident.get("severity", "WARNING").upper()
        sev_color = "#dc2626" if sev == "CRITICAL" else ("#d97706" if sev == "WARNING" else "#16a34a")

        metadata_data = [
            [
                Paragraph("<b>Incident ID:</b>", body_style),
                Paragraph(str(incident.get("id", "N/A")), body_style),
                Paragraph("<b>Severity:</b>", body_style),
                Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", body_style),
            ],
            [
                Paragraph("<b>Category:</b>", body_style),
                Paragraph(str(incident.get("category", "N/A")).replace("_", " ").title(), body_style),
                Paragraph("<b>Status:</b>", body_style),
                Paragraph(f"<b>{incident.get('status', 'INVESTIGATING')}</b>", body_style),
            ],
            [
                Paragraph("<b>Detection Time:</b>", body_style),
                Paragraph(str(incident.get("detected_time", "N/A")), body_style),
                Paragraph("<b>Model Confidence:</b>", body_style),
                Paragraph(f"{round(float(incident.get('confidence', 0.0)) * 100, 1)}%", body_style),
            ],
            [
                Paragraph("<b>Incident Title:</b>", body_style),
                Paragraph(f"<b>{incident.get('title', 'System Anomaly Cluster')}</b>", body_style),
                Paragraph("<b>Correlated Events:</b>", body_style),
                Paragraph(str(len(incident.get("evidence", []))), body_style),
            ]
        ]

        meta_table = Table(metadata_data, colWidths=[90, 200, 90, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # 3. AI Diagnosis & Root Cause Analysis
        story.append(Paragraph("AI Diagnosis & Probable Root Cause (Jev Decision Engine)", heading_style))
        diag = incident.get("diagnosis") or {}
        cause_text = diag.get("possible_cause", "Unclassified Anomaly")
        explanation_text = diag.get("explanation", incident.get("summary", "No details available."))
        uncertainty_text = diag.get("uncertainty", "Manual validation required.")

        diag_content = [
            [
                Paragraph("<b>Identified Diagnosis:</b>", body_style),
                Paragraph(f"<b>{cause_text}</b>", body_style)
            ],
            [
                Paragraph("<b>Diagnosis Explanation:</b>", body_style),
                Paragraph(explanation_text, body_style)
            ],
            [
                Paragraph("<b>Uncertainty Assessment:</b>", body_style),
                Paragraph(f"<i>{uncertainty_text}</i>", body_style)
            ]
        ]
        diag_table = Table(diag_content, colWidths=[130, 410])
        diag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(diag_table)
        story.append(Spacer(1, 14))

        # 4. Recommended Actionable Remediation Steps
        steps = diag.get("recommended_steps", [])
        if steps:
            story.append(Paragraph("Recommended Investigation & Remediation Steps", heading_style))
            step_rows = []
            for i, step in enumerate(steps, 1):
                step_rows.append([
                    Paragraph(f"<b>{i}.</b>", body_style),
                    Paragraph(step, body_style)
                ])
            step_table = Table(step_rows, colWidths=[20, 520])
            step_table.setStyle(TableStyle([
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(step_table)
            story.append(Spacer(1, 14))

        # 5. Chronological Supporting Evidence Table
        evidence_list = incident.get("evidence", [])
        if evidence_list:
            story.append(Paragraph("Supporting Evidence & Event Timeline", heading_style))
            story.append(Paragraph(
                "<i>Note: Events are sequenced chronologically based on timestamps. Temporal sequence indicates correlation, not definitive causality.</i>",
                subtitle_style
            ))
            story.append(Spacer(1, 6))

            ev_headers = [
                Paragraph("Time", table_header_style),
                Paragraph("Service", table_header_style),
                Paragraph("Level", table_header_style),
                Paragraph("Log Message / Anomaly Description", table_header_style)
            ]
            ev_table_data = [ev_headers]

            for ev in evidence_list[:15]:
                log = ev.get("log") or {}
                time_str = str(log.get("timestamp", ""))[-8:] if log.get("timestamp") else "N/A"
                ev_table_data.append([
                    Paragraph(time_str, table_body_style),
                    Paragraph(str(log.get("service", "unknown")), table_body_style),
                    Paragraph(str(log.get("severity", "INFO")), table_body_style),
                    Paragraph(str(log.get("message", ev.get("description", "")))[:120], table_body_style)
                ])

            ev_table = Table(ev_table_data, colWidths=[55, 80, 50, 355])
            ev_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(ev_table)

        # Build document
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


report_generator = ReportGenerator()
