# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 00:41:19 2020

@author: Marcelo Feliciano Filho
"""

from sklearn import tree, svm, neural_network as nn #Importa o módulo de árvores decisóriass
from pandas import read_csv
from pickle import dump, load
from os import getcwd

def save_model(model,name): #Salva o modelo com o nome determinado
    
    with open(f"{getcwd()}/docs/{name.replace(':','')}.pkl", 'wb') as f:
        dump(model, f)

def treina_modelo(classif,treinar): #Realiza treinamento das DecisionTreeClassifier (DTC)
    """
    Essa função realiza o treino das variáveis pré-estabelecidas para o modelo
    Conforme a ordem do usuário, na versão MVP temos apenas 3 opções.
        classf: STR
                opção selecionada pelo usuário para treinamento da técnica de Machine Learning classificatória
    """
    if treinar:
        data_X = read_csv("docs/dataset_ofc_X.csv") #Carrega os dados em 'X' (dados dos sensores)
        data_Y = read_csv("docs/dataset_ofc_Y.csv") #Carrega os dados em 'Y' (é falha ou não, binário)
        
        if classif == 'Decision Tree':
            clf = tree.DecisionTreeClassifier() #Cria objeto classificados do tipo árvore decisória
            MODELO = clf.fit(data_X, data_Y.values.ravel()) #Ajusta os dados de x e y no DTC para criar um objeto
        elif classif == 'Support Vector Machine':
            clf = svm.SVC() #Cria objeto classificados do tipo SVM
            MODELO = clf.fit(data_X, data_Y.values.ravel()) #Ajusta os dados de x e y no DTC para criar um objeto
        elif classif == 'Newral Network: MLP': #Chama o mult-layer perceptron
            clf = nn.MLPClassifier(solver='lbfgs', alpha=1e-5,
                                   hidden_layer_sizes=(40, 2), random_state=1)
            MODELO = clf.fit(data_X, data_Y.values.ravel()) #Ajusta os dados de x e y no DTC para criar um objeto
            #Tem que converter para revel no intuito de rodar o perceptron
        save_model(MODELO,classif) #Salva o modelo de classifcação para consulta posterior
    
    else: #Importa o objeto já treinado
        with open(f"{getcwd()}/docs/{classif.replace(':','')}.pkl", 'rb') as f:
            MODELO = load(f) #Ajusta os dados de x e y no DTC para criar um objeto

    return MODELO #Retorna o objeto classificador 