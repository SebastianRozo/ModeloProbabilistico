import numpy as np
from dataset import getDataset
from model import train_model, predict_proba, predict

def pedir_respuesta(numero_pregunta):
    while True:
        try:
            valor = int(input(f"Respuesta de la pregunta {numero_pregunta} (0-3): "))
            if valor in [0, 1, 2, 3]:
                return valor
            print("Ingresa un numero entre 0 y 3.")
        except ValueError:
            print("Entrada invalida. Debes escribir un numero.")
def formulario_consola(w, b):
    print("\nResponde las 9 preguntas con valores entre 0 y 3.")
    respuestas = []
    for i in range(1, 10):
        respuesta = pedir_respuesta(i)
        respuestas.append(respuesta)
    x_nuevo = np.array([respuestas], dtype=float)
    probabilidad = predict_proba(x_nuevo, w, b)[0]
    clase = predict([probabilidad])[0]
    print("\nResultado:")
    print(f"Probabilidad: {probabilidad:.4f}")
    if probabilidad >=0.5:
        print("RIESGO DE DEPRESION")
    else:
        print("RIESGO MINIMO DE DEPRESION")
    print(f"Clasificacion final: {clase}")
def main():
    train_x, test_x, train_y, test_y = getDataset()
    train_y = train_y.ravel()
    test_y = test_y.ravel()
    w = np.zeros(train_x.shape[1])
    b = 0.0
    learning_rate = 0.01
    iteraciones = 1000
    w, b = train_model(train_x, train_y, w, b, learning_rate, iteraciones)
    formulario_consola(w, b)
if __name__ == "__main__":
    main()
