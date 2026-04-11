import numpy as np

from dataset import getDataset
from model import train_model,predict_proba,predict


def main():
    #Obtener el dataset
    train_x,test_x,train_y,test_y=getDataset()

    train_y = train_y.ravel()
    test_y = test_y.ravel()

    #Inicializacion de pesos y bias
    w=np.zeros(train_x.shape[1])
    b=0

    #Inicializacion de parametros de ciclo de entrenamiento
    learning_rate=0.01
    iteraciones=1000

    #Entrenamiento del modelo
    w,b=train_model(train_x,train_y,w,b,learning_rate,iteraciones)

    #prediccion de probabilidades 
    y_prob=predict_proba(x=test_x,w=w,b=b)
    y_predicted=np.array(predict(y_prob))

    #Precision del modelo 
    accuracy=np.mean(y_predicted==test_y)


    #Imprimir resultados
    print("Predicciones:", y_predicted)
    print("Valores Reales:" , y_predicted[:10])
    print("Precision:", accuracy)
    print("Pesos:", w)
    print("Bias:" , b)
    print("Probabilidades:", y_prob)
    print("Primeras 10 reales:", test_y[:10])


if __name__ == "__main__":
    main()
