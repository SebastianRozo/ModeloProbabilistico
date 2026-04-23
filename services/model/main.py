from fastapi import HTTPException
from db.connection.main import Connection
from schemas.phq9 import PHQ9Request
import numpy as np
from dataset.loader import getDataset
from model.logistic_regression import predict_proba, train_model,predict
class modelServices:
    def __init__(self):
        self.db = Connection()

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