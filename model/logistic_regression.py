import numpy as np

def sigmoide(z):
    return 1 / (1+np.exp(-z))


def predict_proba(x, w, b):
    z=np.dot(x,w)+b
    
    #Funcion De Prediccion
    y_predicted=sigmoide(z)
    
    return y_predicted

def train_model(x,y,w,b,learning_rate,iteraciones):
    for i in range(iteraciones):
        #VARIABLE CON VALOR DE PREDICCION
        y_predicted= predict_proba(x,w,b)

        #Error 
        error=y_predicted-y

        #Gradientes
        dw=(1 / len(x)) * np.dot(x.T, error)
        db=np.mean(error)

        w=w-learning_rate*dw
        b=b-learning_rate*db

        #Variable de numero de muestras 
        m=x.shape[0]

        #Variable por si y_predicted es 0 o 1 
        epsilon = 1e-9

        #FOrmula Loss para ver si el modelo si esta aprendiendo 
        loss=-(1/m)*np.sum(y *np.log(y_predicted+epsilon)+(1-y)*np.log(1-y_predicted+epsilon))
    return w,b

#Convierte probabilidades a clases (1 o 0) es decir , si o no 
def predict(y_predicted, threshold=0.5):
    resultados = []
    for p in y_predicted:
        if p >= threshold:
           
            resultados.append(1)
        else:
            
            resultados.append(0)
    return resultados
