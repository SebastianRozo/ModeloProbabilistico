from fastapi import HTTPException
from db.connection.main import Connection
from schemas.phq9 import PHQ9Request
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape
import numpy as np
from dataset.loader import getDataset
from model.logistic_regression import predict_proba, train_model,predict
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
class modelServices:
    def __init__(self):
        self.db = Connection()

    def ensure_phq9_created_at_column(self, cursor):
        cursor.execute(
            """
            ALTER TABLE phq9_responses
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """
        )
        self.db.conn.commit()

    def get_phq9_risk(self, score:int):
        if score <= 4:
            return "minimo"
        if score <= 9:
            return "leve"
        if score <= 14:
            return "moderado"
        if score <= 19:
            return "moderadamente_severo"
        return "severo"

    def format_date(self, value):
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def phq9_column_exists(self, cursor, column_name:str):
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            LIMIT 1
            """,
            ("phq9_responses", column_name),
        )
        return cursor.fetchone() is not None

    def get_phq9_score_expression(self, cursor):
        sum_expr = "(q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8 + q9)"
        if self.phq9_column_exists(cursor, "total_score"):
            return f"COALESCE(total_score, {sum_expr})"
        return sum_expr

    def get_total_pages(self, total:int, limit:int):
        if total == 0:
            return 0
        return (total + limit - 1) // limit

    def get_phq9_risk_group(self, score:int):
        if score <= 9:
            return "riesgo_bajo"
        if score <= 14:
            return "riesgo_medio"
        return "riesgo_alto"

    def normalize_risk_filter(self, risk):
        if risk is None:
            return None
        normalized = risk.strip().lower()
        aliases = {
            "bajo": "riesgo_bajo",
            "medio": "riesgo_medio",
            "alto": "riesgo_alto",
            "riesgo_bajo": "riesgo_bajo",
            "riesgo_medio": "riesgo_medio",
            "riesgo_alto": "riesgo_alto",
        }
        if normalized not in aliases:
            raise HTTPException(status_code=400, detail="Filtro de riesgo invalido")
        return aliases[normalized]

    def build_evaluations_report_query(self, score_expr:str, where_clause:str):
        return f"""
        WITH latest_evaluations AS (
            SELECT DISTINCT ON (student_id)
                student_id,
                {score_expr} AS score,
                created_at AS last_evaluation_date
            FROM phq9_responses
            ORDER BY student_id, created_at DESC NULLS LAST, id DESC
        ), report_rows AS (
            SELECT
                s.id_estudiante AS student_id,
                s.codigo_institucional AS student_code,
                u.name,
                u.last_name,
                u.email,
                s.semestre,
                s.genero,
                f.nombre_facultad AS faculty,
                p.nombre_programa AS program,
                le.score AS latest_phq9_score,
                le.last_evaluation_date,
                CASE
                    WHEN le.score IS NULL THEN NULL
                    WHEN le.score <= 9 THEN 'riesgo_bajo'
                    WHEN le.score <= 14 THEN 'riesgo_medio'
                    ELSE 'riesgo_alto'
                END AS risk_group
            FROM students s
            JOIN users u ON u.id_usuario = s.fk_id_usuario
            LEFT JOIN facultades f ON f.id_facultad = s.facultad
            LEFT JOIN programs p ON p.id_programa = s.programa
            LEFT JOIN latest_evaluations le ON le.student_id = s.id_estudiante
        )
        SELECT *
        FROM report_rows
        {where_clause}
        """

    def format_evaluation_report_row(self, row):
        score = int(row[9]) if row[9] is not None else None
        return {
            "student_id": row[0],
            "student_code": row[1],
            "name": row[2],
            "last_name": row[3],
            "email": row[4],
            "semester": row[5],
            "gender": row[6],
            "faculty": row[7],
            "program": row[8],
            "latest_phq9_score": score,
            "last_evaluation_date": self.format_date(row[10]),
            "current_risk": row[11],
        }

    def get_month_name(self, month:int):
        months = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }
        return months.get(month, str(month))

    def get_dashboard_stats(self, page:int = 1, limit:int = 12):
        try:
            offset = (page - 1) * limit
            with self.db.conn.cursor() as cursor:
                self.ensure_phq9_created_at_column(cursor)
                score_expr = self.get_phq9_score_expression(cursor)

                cursor.execute(
                    f"""
                    SELECT score
                    FROM (
                        SELECT DISTINCT ON (student_id)
                            student_id,
                            {score_expr} AS score
                        FROM phq9_responses
                        ORDER BY student_id, created_at DESC NULLS LAST, id DESC
                    ) latest_responses
                    """
                )
                latest_scores = cursor.fetchall()

                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM (
                        SELECT 1
                        FROM phq9_responses
                        GROUP BY EXTRACT(YEAR FROM created_at), EXTRACT(MONTH FROM created_at)
                    ) monthly_count
                    """
                )
                total_months = cursor.fetchone()[0]

                cursor.execute(
                    f"""
                    SELECT
                        EXTRACT(YEAR FROM created_at)::int AS year,
                        EXTRACT(MONTH FROM created_at)::int AS month,
                        AVG({score_expr}) AS average_score
                    FROM phq9_responses
                    GROUP BY year, month
                    ORDER BY year, month
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                monthly_rows = cursor.fetchall()

            risk_distribution = {
                "riesgo_bajo": 0,
                "riesgo_medio": 0,
                "riesgo_alto": 0,
            }
            for row in latest_scores:
                score = int(row[0])
                risk_distribution[self.get_phq9_risk_group(score)] += 1

            monthly_evolution = []
            for row in monthly_rows:
                year = int(row[0])
                month = int(row[1])
                average_score = float(row[2])
                monthly_evolution.append({
                    "mes": self.get_month_name(month),
                    "anio": year,
                    "riesgo_promedio": round((average_score / 27) * 100, 2),
                    "puntaje_promedio": round(average_score, 2),
                })

            return {
                "risk_distribution": risk_distribution,
                "monthly_evolution": monthly_evolution,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_months,
                    "total_pages": self.get_total_pages(total_months, limit),
                },
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo estadisticas del dashboard: {str(e)}")

    def get_evaluations_report(self, risk=None, page:int = 1, limit:int = 10):
        try:
            risk_filter = self.normalize_risk_filter(risk)
            where_clause = "WHERE risk_group = %s" if risk_filter else ""
            offset = (page - 1) * limit

            with self.db.conn.cursor() as cursor:
                self.ensure_phq9_created_at_column(cursor)
                score_expr = self.get_phq9_score_expression(cursor)
                base_query = self.build_evaluations_report_query(score_expr, where_clause)
                params = [risk_filter] if risk_filter else []

                cursor.execute(
                    f"SELECT COUNT(*) FROM ({base_query}) filtered_report",
                    tuple(params),
                )
                total = cursor.fetchone()[0]

                cursor.execute(
                    f"""
                    {base_query}
                    ORDER BY last_evaluation_date DESC NULLS LAST, student_id ASC
                    LIMIT %s OFFSET %s
                    """,
                    tuple(params + [limit, offset]),
                )
                rows = cursor.fetchall()

            return {
                "items": [self.format_evaluation_report_row(row) for row in rows],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": self.get_total_pages(total, limit),
                },
                "filters": {
                    "risk": risk_filter,
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo reporte de evaluaciones: {str(e)}")

    def get_evaluations_report_pdf(self, risk=None, page:int = 1, limit:int = 100):
        report = self.get_evaluations_report(risk, page, limit)
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=28,
            leftMargin=28,
            topMargin=26,
            bottomMargin=26,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            textColor=colors.HexColor("#12355B"),
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            textColor=colors.HexColor("#4B5563"),
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
        )
        cell_style = ParagraphStyle(
            "ReportCell",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#111827"),
        )
        header_style = ParagraphStyle(
            "ReportHeader",
            parent=cell_style,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontSize=7,
            leading=9,
        )

        def pdf_text(value, style=cell_style):
            if value is None:
                value = ""
            return Paragraph(escape(str(value)), style)

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        filter_text = report["filters"]["risk"] or "todos"
        pagination = report["pagination"]
        elements = [
            Paragraph("Reporte de Evaluaciones PHQ-9", title_style),
            Paragraph(
                f"Generado: {generated_at} | Filtro riesgo: {filter_text} | Pagina {pagination['page']} de {pagination['total_pages']} | Total: {pagination['total']}",
                subtitle_style,
            ),
            Spacer(1, 14),
        ]

        summary_data = [[
            Paragraph("Modulo", header_style),
            Paragraph("Fuente", header_style),
            Paragraph("Exportados", header_style),
            Paragraph("Limite", header_style),
        ], [
            pdf_text("Reportes"),
            pdf_text("Ultimo PHQ-9 por estudiante"),
            pdf_text(len(report["items"])),
            pdf_text(pagination["limit"]),
        ]]
        summary_table = Table(summary_data, colWidths=[120, 260, 100, 80])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12355B")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EEF6FF")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#BFD7EA")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D6E4F0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.extend([summary_table, Spacer(1, 16)])

        table_data = [[
            Paragraph("ID", header_style),
            Paragraph("Codigo", header_style),
            Paragraph("Estudiante", header_style),
            Paragraph("Email", header_style),
            Paragraph("Sem.", header_style),
            Paragraph("Facultad", header_style),
            Paragraph("Programa", header_style),
            Paragraph("PHQ-9", header_style),
            Paragraph("Ultima prueba", header_style),
            Paragraph("Riesgo", header_style),
        ]]

        for item in report["items"]:
            full_name = f"{item['name']} {item['last_name']}"
            evaluation_date = item["last_evaluation_date"]
            if evaluation_date:
                evaluation_date = evaluation_date.replace("T", " ")[:19]
            risk_label = self.get_pdf_risk_label(item["current_risk"])
            score_text = item["latest_phq9_score"] if item["latest_phq9_score"] is not None else "Sin dato"
            table_data.append([
                pdf_text(item["student_id"]),
                pdf_text(item["student_code"]),
                pdf_text(full_name),
                pdf_text(item["email"]),
                pdf_text(item["semester"]),
                pdf_text(item["faculty"]),
                pdf_text(item["program"]),
                pdf_text(score_text),
                pdf_text(evaluation_date or "Sin dato"),
                pdf_text(risk_label),
            ])

        report_table = Table(table_data, colWidths=[32, 68, 95, 126, 34, 80, 105, 45, 103, 62], repeatRows=1)
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12355B")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        for row_index, item in enumerate(report["items"], start=1):
            row_color = colors.HexColor("#FFFFFF") if row_index % 2 else colors.HexColor("#F8FAFC")
            table_style.append(("BACKGROUND", (0, row_index), (-1, row_index), row_color))
            table_style.append(("BACKGROUND", (9, row_index), (9, row_index), self.get_pdf_risk_color(item["current_risk"])))
        report_table.setStyle(TableStyle(table_style))
        elements.append(report_table)

        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content

    def get_pdf_risk_label(self, risk):
        labels = {
            "riesgo_bajo": "Bajo",
            "riesgo_medio": "Medio",
            "riesgo_alto": "Alto",
        }
        return labels.get(risk, "Sin dato")

    def get_pdf_risk_color(self, risk):
        colors_by_risk = {
            "riesgo_bajo": colors.HexColor("#DCFCE7"),
            "riesgo_medio": colors.HexColor("#FEF3C7"),
            "riesgo_alto": colors.HexColor("#FEE2E2"),
        }
        return colors_by_risk.get(risk, colors.HexColor("#E5E7EB"))

    def get_student_evaluations(self, id_estudiante:int, page:int = 1, limit:int = 10):
        try:
            offset = (page - 1) * limit
            with self.db.conn.cursor() as cursor:
                self.ensure_phq9_created_at_column(cursor)

                cursor.execute(
                    "SELECT id_estudiante FROM students WHERE id_estudiante = %s",
                    (id_estudiante,),
                )
                student = cursor.fetchone()
                if not student:
                    raise HTTPException(status_code=404, detail="Estudiante no encontrado")

                score_expr = self.get_phq9_score_expression(cursor)

                date_column = None
                for column_name in ("created_at", "fecha_creacion"):
                    if self.phq9_column_exists(cursor, column_name):
                        date_column = column_name
                        break

                date_expr = date_column if date_column else "NULL"
                order_expr = f"{date_column} DESC NULLS LAST, id DESC" if date_column else "id DESC"
                cursor.execute(
                    f"""
                    SELECT id, {score_expr} AS score, {date_expr} AS evaluation_date
                    FROM phq9_responses
                    WHERE student_id = %s
                    ORDER BY {order_expr}
                    LIMIT 1
                    """,
                    (id_estudiante,),
                )
                latest_row = cursor.fetchone()

                cursor.execute(
                    "SELECT COUNT(*) FROM phq9_responses WHERE student_id = %s",
                    (id_estudiante,),
                )
                total_history = cursor.fetchone()[0]

                cursor.execute(
                    f"""
                    SELECT id, {score_expr} AS score, {date_expr} AS evaluation_date
                    FROM phq9_responses
                    WHERE student_id = %s
                    ORDER BY {order_expr}
                    LIMIT %s OFFSET %s
                    """,
                    (id_estudiante, limit, offset),
                )
                rows = cursor.fetchall()

            latest_phq9 = None
            if latest_row:
                latest_score = int(latest_row[1])
                latest_phq9 = {
                    "date": self.format_date(latest_row[2]),
                    "test_name": "PHQ-9",
                    "score": latest_score,
                    "risk": self.get_phq9_risk(latest_score),
                }

            history = []
            for row in rows:
                score = int(row[1])
                history.append({
                    "date": self.format_date(row[2]),
                    "test_name": "PHQ-9",
                    "score": score,
                    "risk": self.get_phq9_risk(score),
                })

            return {
                "student_id": id_estudiante,
                "latest_phq9": latest_phq9,
                "current_risk": latest_phq9["risk"] if latest_phq9 else None,
                "history": history,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_history,
                    "total_pages": self.get_total_pages(total_history, limit),
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error obteniendo evaluaciones: {str(e)}")

    def predict_depression(self,data:PHQ9Request,current_user):
        try:
            #Entrenamiento del modelo con el DataSet Publico
            train_x, test_x, train_y, test_y = getDataset()
            train_y = train_y.ravel()
            test_y = test_y.ravel()
            w = np.zeros(train_x.shape[1])
            b = 0.0
            learning_rate = 0.01
            iteraciones = 1000
            w, b = train_model(train_x, train_y, w, b, learning_rate, iteraciones)

            #Construir el vector de entrada
            respuestas = [
                data.question1,
                data.question2,
                data.question3,
                data.question4,
                data.question5,
                data.question6,
                data.question7,
                data.question8,
                data.question9,
            ]
            vector_phq9 = np.array([respuestas], dtype=float)
            probabilidad = float(predict_proba(vector_phq9, w, b)[0])
            clase = int(predict([probabilidad])[0])
            total_score = int(sum(respuestas))
            
            with self.db.conn.cursor() as cursor:
                self.ensure_phq9_created_at_column(cursor)

                cursor.execute(
                    "SELECT id_estudiante FROM students WHERE fk_id_usuario = %s",
                    (current_user[0],)
                )
                student = cursor.fetchone()
                if not student:
                    raise HTTPException(
                        status_code=404,
                        detail="El usuario autenticado no es un estudiante"
                    )
                student_id = student[0]
                cursor.execute(
                    """
                    INSERT INTO phq9_responses (
                        student_id, q1, q2, q3, q4, q5, q6, q7, q8, q9, total_score
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        student_id,
                        respuestas[0],
                        respuestas[1],
                        respuestas[2],
                        respuestas[3],
                        respuestas[4],
                        respuestas[5],
                        respuestas[6],
                        respuestas[7],
                        respuestas[8],
                        total_score,
                    ),
                )
                response_id = cursor.fetchone()[0]
                self.db.conn.commit()
            return {
                "response_id": response_id,
                "probabilidad": probabilidad,
                "clase": clase,
                "total_score": total_score,
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error prediciendo depresion: {str(e)}")
