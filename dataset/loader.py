from pathlib import Path

import polars as pl


def getDataset():
    #carga del dataset
    csv_path = Path(__file__).resolve().parent.parent / "data" / "phq9.csv"
    df_phq = pl.read_csv(csv_path)

    #UNIR DF A UNO SOLO PARA ENTRENAR Y PROBAR EL MODELO

    #Mezcla de datos
    df_mezclado = df_phq.sample(fraction=1.0, shuffle=True, seed=42)
    #Separacion de columnas (X: PUNTOS DEL FORMULARIO , Y :SCORE TOTAL ) si quiero agregar mas columnas solo las agrego a la seleccion de x 
    X=df_mezclado.select(["question1", "question2", "question3", "question4", "question5", "question6", "question7", "question8", "question9"])
    Y=df_mezclado.select(pl.when(pl.col("score")>=5).then(1).otherwise(0))

    #Definicion de tamaño de entrenamiento y prueba 
    train_size=int(0.8*len(X))
    test_size=len(X)-train_size

    #Separacion de datos en entrenamiento y prueba de ambas columnas
    train_x=X.slice(0,train_size)
    test_x=X.slice(train_size,test_size)
    
    y_train=Y.slice(0,train_size)
    y_test=Y.slice(train_size,test_size)
     
    train_x=train_x.to_numpy()
    test_x=test_x.to_numpy()

    y_train=y_train.to_numpy()
    y_test=y_test.to_numpy()
    
    return train_x, test_x, y_train, y_test
