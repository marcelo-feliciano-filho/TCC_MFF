# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 23:48:10 2020

https://medium.com/@soutrikbandyopadhyay/controlling-a-simulink-model-by-a-python-controller-2b67bde744ee

@author: Marcelo Feliciano Filho
"""

import matlab.engine #Chama a engine do matlab ao python
import matplotlib.pyplot as plt #Importa o módulo pyplot da matplotlib

def monitora(system):
    """
    É uma função que abre o matlab simulink e emula processos
    
    Parameters
    ----------
    system : str
        Onde system é o sistema que se deseja monitorar.
        Esse nome é informado pelo usuário na interface
    Returns
    -------
    None.

    """
    plant = SimulinkPlant(modelName=system)
    #Establishes a Connection
    plant.connectToMatlab()
    
    #Instantiates the controller
    controller = PIController()
    plant.connectController(controller)
    
    #Control Loop
    plant.simulate()
    
    #Closes Connection to MATLAB
    plant.disconnect()
    
class SimulinkPlant:
    def __init__(self,modelName = 'plant'):
        
        #The name of the Simulink Model (To be placed in the same directory as the Python Code) 
        self.modelName = modelName
        #Logging the variables
        self.yHist = 0 
        self.tHist = 0 
        
    def setControlAction(self,u):
        #Helper Function to set value of control action
        self.eng.set_param('{}/u'.format(self.modelName),'value',str(u),nargout=0)
    
    def getHistory(self):
        #Helper Function to get Plant Output and Time History
        return self.eng.workspace['output'],self.eng.workspace['tout']
        
    def connectToMatlab(self):
        
        print("Starting matlab")
        self.eng = matlab.engine.start_matlab()
        
        print("Connected to Matlab")
        
        #Load the model
        self.eng.eval("model = '{}'".format(self.modelName),nargout=0)
        self.eng.eval("load_system(model)",nargout=0)
        
        #Initialize Control Action to 0
        self.setControlAction(0)
        print("Initialized Model")
        
        #Start Simulation and then Instantly pause
        self.eng.set_param(self.modelName,'SimulationCommand','start','SimulationCommand','pause',nargout=0)
        self.yHist,self.tHist = self.getHistory()    
    
    def simulate(self):
        # Control Loop
        while(self.eng.get_param(self.modelName,'SimulationStatus') != ('stopped' or 'terminating')):
            
            self.eng.set_param(self.modelName,'SimulationCommand','continue','SimulationCommand','pause',nargout=0)
            
            self.yHist,self.tHist = self.getHistory()
        
    def disconnect(self):
        self.eng.set_param(self.modelName,'SimulationCommand','stop',nargout=0)
        self.eng.quit()

class PIController:
    def __init__(self):
        
        #Maintain a History of Variables
        self.yHist = []
        self.tHist = []
        self.uHist = []
        self.eSum = 0
        
    def initialize(self):
        
        #Initialize the graph
        self.fig, = plt.plot(self.tHist,self.yHist)
        plt.xlim(0,10)
        plt.ylim(0,20)
        plt.ylabel("Plant Output")
        plt.xlabel("Time(s)")
        plt.title("Plant Response")
        
    def updateGraph(self):
        # Update the Graph
        self.fig.set_xdata(self.tHist)
        self.fig.set_ydata(self.yHist)
        plt.pause(0.1)
        plt.show()
    
    def getControlEffort(self,yHist,tHist):
        
        # Returns control action based on past outputs
        
        self.yHist = yHist
        self.tHist = tHist
        
        self.updateGraph()
        
        if(type(self.yHist) == float):
            y = self.yHist
        else:
            y = self.yHist[-1][0]
        
        # Set Point is 10
        e = 10-y
        
        self.eSum += e
        u = 1*e + 0.001*self.eSum
        
        print(y)
        self.uHist.append(u)
        return u
        
        