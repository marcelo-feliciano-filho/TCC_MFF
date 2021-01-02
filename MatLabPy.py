# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 23:48:10 2020

https://medium.com/@soutrikbandyopadhyay/controlling-a-simulink-model-by-a-python-controller-2b67bde744ee

@author: Marcelo Feliciano Filho
"""
import matlab.engine #Chama a engine do matlab ao python


def test_matlab():
    """
    O único intuito dessa unção é testar o matlab com os dados padrão pré estabelecidos, simulando input do usuário

    Returns
    -------
    None.

    """
    system = r"C:\Users\marce\Desktop\PUCPR\TRABALHO DE CONCLUSÃO DO CURSO - TCC\SOFT SENSORS\ofc_benchmark_acquire.slx"
    bench = "ofc_benchmark_acquire"
    benchmark_path = r"C:\Users\marce\Desktop\PUCPR\TRABALHO DE CONCLUSÃO DO CURSO - TCC\SOFT SENSORS"
    
    eng = matlab.engine.start_matlab() 
    eng.addpath(benchmark_path,nargout=0)
    
    parametro = ["sensor","solid",0.8,0.05,'2*pi',"setSevereTurbulence()",2,20]
    
    #Iniciando o benchmark e carrega as principais variáveis ao console da API
    eng.eval("ofc_benchmark_init",nargout=0)
    eng.eval(f"simulation.setSimulinkModel('{bench}');",nargout=0)
    #Carrega as variáveis: aircraft, ofc, servoModel, servoReal e simulation!
    
    eng.eval("servoReal.randomiseServoParameters()",nargout=0) #Faz o objeto servo real ficar aleatório
    eng.eval(f"ofc.setLocation('{parametro[0]}')",nargout=0)
    eng.eval(f"ofc.setType('{parametro[1]}')",nargout=0)
    eng.eval(f"ofc.setAmplitude({parametro[2]})",nargout=0)
    eng.eval(f"ofc.setBias({parametro[3]})",nargout=0)
    eng.eval(f"ofc.setFrequency({parametro[4]})",nargout=0)
    eng.eval("ofc.setPhase(0)",nargout=0)
    eng.eval("ofc.setStartTime(0)",nargout=0)
    eng.eval(f"aircraft.{parametro[5]}",nargout=0)
    
    #Cria sinal aleatório de controle
    eng.eval("""controls = {@(x)aircraft.setControlInput('FPA_control'), ...
                    @(x)aircraft.setControlInput('NZ_step', x(1), x(2), x(3)), ...
                    @(x)aircraft.setControlInput('NZ_sine', x(1), x(2), x(3), x(4)), ...
                    @(x)aircraft.setControlInput('NZ_chirp', x(1))};""",nargout=0)
    print("Declarou stringão")
    eng.eval("controls{"+str(parametro[6])+"}([10^randi([-1 1]),randi([10 25]),randi([35, 50]),randi([0, 10])])",
                    nargout=0)
    print("Passou o ruim")
    eng.eval(f"simulation.setStopTime({parametro[7]})",nargout=0) #Seta o tempo final de simulação

    eng.eval(f"model = '{system}'",nargout=0)
    
    eng.eval("SimOut = sim(simulation.simulink_model, 'SrcWorkspace', 'current');",nargout=0)

    process = eng.eval("[SimOut.dx_comm SimOut.dx_meas SimOut.time]") #Recebe apenas os valores desejados    

    return(process)

def SimulinkPlant(matlab_obj,parametro):
    """
    Essa função objetiva declarar as variáveis necessárias para desenvolvimento da simulação 
    
    parametroeters
    ----------
    matlab_obj : obj
        Um objeto da API do matlab que permite execução de comandos.
    
    parametro: array
        Array com todos os parâmetros fornecidos pelo usuário    
    
    Returns
    -------
    None. Mas realiza inúmeros comandos para simular a planta e declarar as variáveis

    """
    
    #Iniciando o benchmark e carrega as principais variáveis ao console da API
    matlab_obj.eval("ofc_benchmark_init",nargout=0)
    matlab_obj.eval("simulation.setSimulinkModel('ofc_benchmark_acquire');",nargout=0)
    #Carrega as variáveis: aircraft, ofc, servoModel, servoReal e simulation!
    
    matlab_obj.eval("servoReal.randomiseServoParameters()",nargout=0) #Faz o objeto servo real ficar aleatório
    matlab_obj.eval(f"ofc.setLocation('{parametro[0]}')",nargout=0)
    matlab_obj.eval(f"ofc.setType('{parametro[1]}')",nargout=0)
    matlab_obj.eval(f"ofc.setAmplitude({parametro[2]})",nargout=0)
    matlab_obj.eval(f"ofc.setBias({parametro[3]})",nargout=0)
    matlab_obj.eval(f"ofc.setFrequency('{parametro[4]}')",nargout=0)
    matlab_obj.eval("ofc.setPhase(0)",nargout=0)
    matlab_obj.eval("ofc.setStartTime(0)",nargout=0)
    matlab_obj.eval(f"aircraft.{parametro[5]}",nargout=0)
    
    #Cria sinal aleatório de controle
    matlab_obj.eval("""controls = {@(x)aircraft.setControlInput('FPA_control'), ...
                    @(x)aircraft.setControlInput('NZ_step', x(1), x(2), x(3)), ...
                    @(x)aircraft.setControlInput('NZ_sine', x(1), x(2), x(3), x(4)), ...
                    @(x)aircraft.setControlInput('NZ_chirp', x(1))};""",nargout=0)
    print("Declarou stringão")
    matlab_obj.eval("controls{"+str(parametro[6])+"}([10^randi([-1 1]),randi([10 25]),randi([35, 50]),randi([0, 10])])",
                    nargout=0)
    print("Passou o ruim")
    matlab_obj.eval(f"simulation.setStopTime({parametro[7]})",nargout=0) #Seta o tempo final de simulação
    
    