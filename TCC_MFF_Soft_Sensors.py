# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 18:41:52 2020

links:
    Matlab:
        https://www.learnpyqt.com/courses/graphics-plotting/plotting-pyqtgraph/
        https://medium.com/@soutrikbandyopadhyay/controlling-a-simulink-model-by-a-python-controller-2b67bde744ee
        https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html
    Simulink:
        https://www.mathworks.com/matlabcentral/fileexchange/30953-simulink-block-for-real-time-execution?s_tid=srchtitle
    scikit:
        https://scikit-learn.org/stable/modules/tree.html
        https://scikit-learn.org/stable/modules/svm.html
        https://scikit-learn.org/stable/modules/neural_networks_supervised.html

@author: Marcelo Feliciano Filho
"""

import sys, os, mariadb
from PyQt5.QtWidgets import (QWidget, QLabel, QApplication, QPushButton, QLineEdit, QTabWidget, QAction,
                             QMessageBox, QDesktopWidget, QVBoxLayout, QMainWindow, QProgressBar, QFrame,
                             QFileDialog, QTableView, QHBoxLayout, QComboBox, QListWidget)
from PyQt5.QtGui import QPixmap, QFont, QIcon, QPalette, QColor
#Permite imprimir imagens na tela e alterar a fonte
from PyQt5.QtCore import Qt, QAbstractTableModel, QTimer
from pyqtgraph import exporters, mkPen, PlotWidget
from pandas import ExcelFile, DataFrame
from datetime import datetime
import matlab.engine #Chama a engine do matlab ao python
from random import randint
from numpy import array, int16
from TCC_MFF_Treino import treina_modelo
from style import str_style #Importa a stylesheet necessária para modernizar essa interface

#Variáveis globais necessárias para comunicação entre as classes
versao = "V.1.0.0 - MVP"; ml = "Machine Learning"; mff = "Desenvolvido por Marcelo Feliciano Filho"
email = "marcelo.feliciano.f@outlook.com"
font = ['sensor', 'current', 'cs', 'cs_sensor'] #Fontes de perturbação
type_ofc = ['none','liquid','solid']#Tipos das perturbações
turb = ['None','Light','Moderate','Severe'] #Tipos de turbulência
ctrl = ['FPA_control','NZ_step','NZ_chirp','NZ_sine'] #Tipos de controle
ampl = ['0.01','0.025','0.05','0.1','0.25','0.375','0.5','0.7','0.8','1','1.5','2','3','4','6','8','10'] #Amplitudes
bias = ['0.001','0.01','0.05','0.1','0.2','0.3','0.5','1','1.25']#Offset do sensor
freq = ['0.1π','0.25π','0.4π','0.5π','0.75π','1π','1.25π','1.5π','2π','2.5π','3π','3.5π','4π','5π','20π'] #Frequências
treino = ['Decision Tree','Newral Network: MLP','Support Vector Machine'] #,'Support Vector Machine' é carregado sempre
time = []; time_fail = []; delta_comm = []; delta_meas = []; ofc_falhas = []; simulado = False
df = DataFrame({})
dff = DataFrame({})
Relatorio_TXT_Etapas = []

class QHLine(QFrame): #Permite desenhar linha horizontal
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        palette = QPalette()
        palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
        self.setPalette(palette)

class central(QWidget): #Cria widget para colocar na janela central onde as duas
    
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icons/icone_TCC.png"))
        self.UI()
    
    def UI(self):
        main = QVBoxLayout() #Widget principal, onde serão colocadas todas as abas
        self.unit_y = "Ângulo de deflexão (° graus)"
        self.unit_x = "Segundos (s)"
        self.lines = [] #Lista das linhas do listwidget reinicia
        self.tabela_param = 830
        self.passw = "lembrei"
        
        # Cria os principais layouts que serão inseridos nas 4 abas do software 
        self.main_tab = QHBoxLayout() #Layout para a aba principal
        db_tab = QVBoxLayout() #Layout para a aba dos dados
        rep_tab = QVBoxLayout() #Aba dos relatórios
        info_tab = QVBoxLayout() #Aba das informações
        
        """
        Widgets da primeira aba
        """
        fonte = QFont() #Cria a fonte em negrito
        fonte.setBold(True)
        #Cria o formulário dos parâmetros, controle e barra de progresso
        self.formulario = QVBoxLayout() #Cria o form das principais atividades 
        self.lbl_void = QLabel() #Label vazio para espaçar os dados
        self.lbl_imp = QLabel("Dir. do Sistema",self) #Label da importação do benchmark
        self.lbl_imp.setFont(fonte)
        #self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.btn_bch = QPushButton("Benchmark")
        self.btn_bch.clicked.connect(self.bench)
        self.lbl_param = QLabel("Parametrização",self)
        self.lbl_param.setFont(fonte)
        self.lbl_font = QLabel("Fonte da OFC: ")
        self.cmb_font = QComboBox(self) #Cria o combobox do primeiro parâmetro
        self.cmb_font.addItems(font) #Carrega lista das fontes de perturbação
        self.cmb_font.currentTextChanged.connect(self.pdate_ampl)
        self.hbox_font = QHBoxLayout()
        self.hbox_font.addWidget(self.lbl_font)
        self.hbox_font.addWidget(self.cmb_font)
        self.lbl_type = QLabel("Tipo da OFC: ")
        self.cmb_type = QComboBox(self) #Cria o combobox do primeiro parâmetro
        self.cmb_type.addItems(type_ofc) #Carrega lista das fontes de perturbação
        self.hbox_type = QHBoxLayout()
        self.hbox_type.addWidget(self.lbl_type)
        self.hbox_type.addWidget(self.cmb_type)
        self.lbl_turb = QLabel("Turbulência: ")
        self.cmb_turb = QComboBox(self) #Cria o combobox do segundo parâmetro
        self.cmb_turb.addItems(turb)
        self.hbox_turb = QHBoxLayout()
        self.hbox_turb.addWidget(self.lbl_turb)
        self.hbox_turb.addWidget(self.cmb_turb)
        self.lbl_ctrl1 = QLabel("Tipo Controle: ")
        self.cmb_ctrl1 = QComboBox(self)#Cria o combobox do terceiro parâmetro
        self.cmb_ctrl1.addItems(ctrl)
        self.hbox_ctrl1 = QHBoxLayout()
        self.hbox_ctrl1.addWidget(self.lbl_ctrl1)
        self.hbox_ctrl1.addWidget(self.cmb_ctrl1)
        self.lbl_ampl = QLabel("Ampl(mm)/Bias(mm)/Freq(rad/s):")
        self.cmb_ampl = QComboBox(self) #Cria o combobox das unidades do eixo das abscissas
        self.cmb_ampl.addItems(ampl)
        self.cmb_bias = QComboBox(self) #Cria o combobox das unidades do eixo das abscissas
        self.cmb_bias.addItems(bias)
        self.cmb_freq = QComboBox(self) #Cria o combobox das unidades do eixo das oordenadas
        self.cmb_freq.addItems(freq)
        self.amp_bias_freq = QHBoxLayout()
        self.amp_bias_freq.addWidget(self.cmb_ampl,30)
        self.amp_bias_freq.addWidget(self.cmb_bias,30)
        self.amp_bias_freq.addWidget(self.cmb_freq,40)
        self.lbl_ctrl = QLabel("Painel de Controle",self)
        self.lbl_ctrl.setFont(fonte)
        self.lbl_bench = QLabel("Modelo .lsx Benchmark: ")
        self.cmb_bench = QComboBox(self) #Cria o combobox das unidades do eixo das oordenadas
        self.lbl_treino = QLabel("Modo de Treinamento: ")
        self.cmb_treino = QComboBox(self) #Cria o combobox das unidades do eixo das oordenadas
        self.cmb_treino.addItems(treino)
        self.lbl_time = QLabel("Tempo de Simulação: ")
        self.line_time = QLineEdit()
        self.line_time.setPlaceholderText("Segundos")
        self.hbox_time = QHBoxLayout()
        self.hbox_time.addWidget(self.lbl_time)
        self.hbox_time.addWidget(self.line_time)
        self.list_status = QListWidget()
        self.list_status.doubleClicked.connect(self.exp_rep)
        self.btn_start = QPushButton("Iniciar")
        self.btn_start.clicked.connect(self.start)
        self.btn_start.setDisabled(True)
        self.pbar = QProgressBar()
        self.pbar.setFont(fonte)
        #Insere no formulário os widgets:
        self.formulario.addStretch()
        cp = QDesktopWidget().availableGeometry().center()
        if cp.y()*2 >= 1030: #Se a resolução for alta, coloca o ícone da pontifícia
            self.tabela_param = 1385
            self.lbl_icon = QLabel() #Label que armazena o icone
            #Icone da pontifícia:
            icone_tcc = QPixmap("icons/TCC_Icon.png")#.scaled(50, 61, Qt.KeepAspectRatio, Qt.FastTransformation)
            self.lbl_icon.setPixmap(icone_tcc)
            self.lbl_icon.setAlignment(Qt.AlignCenter)
            self.formulario.addWidget(self.lbl_icon)
            self.passw = ""
            #self.benchmark_path = r"D:/PUCPR/TRABALHO DE CONCLUSAO DO CURSO - TCC/SOFT SENSORS"
            
        self.formulario.addWidget(self.lbl_imp)
        self.formulario.addWidget(self.btn_bch)
        self.formulario.addWidget(QHLine())#)#self.lbl_void) #Espaçamento
        self.formulario.addWidget(self.lbl_param)
        self.formulario.addLayout(self.hbox_font)
        self.formulario.addLayout(self.hbox_type)
        self.formulario.addLayout(self.hbox_turb)
        self.formulario.addLayout(self.hbox_ctrl1)
        self.formulario.addWidget(self.lbl_ampl)
        self.formulario.addLayout(self.amp_bias_freq)
        self.formulario.addWidget(QHLine())#self.lbl_void) #Espaçamento
        self.formulario.addWidget(self.lbl_ctrl)
        self.formulario.addWidget(self.lbl_bench)
        self.formulario.addWidget(self.cmb_bench)
        self.formulario.addWidget(self.lbl_treino)
        self.formulario.addWidget(self.cmb_treino)
        self.formulario.addLayout(self.hbox_time)
        self.formulario.addWidget(self.btn_start)
        self.formulario.addWidget(self.list_status)
        self.formulario.addWidget(self.pbar)
        self.formulario.setAlignment(Qt.AlignCenter)
        self.formulario.addStretch()
        
        #cria o gráfico
        self.grafico = PlotWidget()
        self.grafico.setBackground('#323232') #Coloca a cor de fundo igual a do restante da interface
        # Coloca título no gráfico
        self.grafico.setTitle("Simulação do Benchmark OFC: AirBus", color="#56fceb", size="20pt")
        self.styles = {"color": "#56fceb", "font-size": "16px"} #Cria os estilos de fonte do gráfico
        self.grafico.setLabel("left", self.unit_y, **self.styles) #Insere a unidade do eixo Oordenado
        self.grafico.setLabel("bottom", self.unit_x, **self.styles) #Insere a unidade do eixo das Abscissas
        self.grafico.addLegend() #Coloca legenda no gráfico
        self.grafico.showGrid(x=True, y=True) #Coloca as grids no gráfico
        
        #Cria as três curvas que serão periodicamente atualizadas
        #self.dx_falhas = ScatterPlotItem(name="Falhas: OFC", symbolSize=10,symbol='x',symbolBrush=("#fc031c"), 
        #                                 pen=mkPen(color="#fc031c", width=1))
        #self.grafico.addItem(self.dx_falhas)
        self.dx_comm = self.grafico.plot(name="Comando de Controle", symbolSize=5,symbolBrush=("#15bf48"), 
                                         pen=mkPen(color="#15bf48", width=2))
        self.dx_meas = self.grafico.plot(name="Deflexão Mensurada", symbolSize=5,symbolBrush=("#56fceb"), 
                                         pen=mkPen(color="#56fceb", width=2))
        self.dx_falhas = self.grafico.plot(name="Falhas: OFC", symbolSize=20,symbol='x',symbolBrush=("#fc031c"), 
                                           pen=mkPen(color="#323232", width=0.001))
        
        self.formulario.addStretch()
        #Insere os widgets na widget da aba
        self.main_tab.addLayout(self.formulario,13.5) #Adiciona a aba os parâmetros 
        self.main_tab.addWidget(self.grafico,86.5) #Adiciona o gráfico a aba principal
        
        """
        Cria os widgets da segunda tab
        """
        self.db_table = QTableView() #Cria tabela do banco de dados
        #Itens abaixo da tabela
        self.btn_consulta = QPushButton("Consultar o Número de itens mais Atuais")
        self.btn_consulta.clicked.connect(self.update_tb)
        self.n_itens = QLineEdit()
        self.n_itens.setPlaceholderText("N° Itens")
        self.status_itens = QLineEdit()
        self.status_itens.setPlaceholderText("Status do software:")
        self.status_itens.setDisabled(True)
        self.btn_pdate = QPushButton("Atualiza para os 1000 últimos dados registrados")
        self.btn_pdate.clicked.connect(self.update_tb_1000)
        self.btn_exp = QPushButton("Exportar tabela para Excel")
        self.btn_exp.clicked.connect(self.exp_dados_excel)
        self.pbar_db = QProgressBar()
        self.pbar_db.setFont(fonte)
        self.db_func = QHBoxLayout() #Layout dos botões abaixo da tabela
        self.db_func.addWidget(self.btn_consulta,28)
        self.db_func.addWidget(self.n_itens,4.5)
        self.db_func.addWidget(self.status_itens,8.5)
        self.db_func.addWidget(self.pbar_db,25)
        self.db_func.addWidget(self.btn_pdate,21)
        self.db_func.addWidget(self.btn_exp,12)
        #Insere abaixo da tabela os itens:
        db_tab.addWidget(self.db_table,93)
        db_tab.addLayout(self.db_func,7)
        db_tab.addStretch()
        
        """
        Cria os widgets da terceira aba
        """
        self.rep_table = QTableView() #Cria tabela do relatório
        #Itens abaixo da tabela
        self.btn_pdate_rep = QPushButton("Atualiza para todos os dados registrados")
        self.btn_pdate_rep.clicked.connect(self.update_rep)
        self.btn_rep = QPushButton("Atualiza para todos últimos 'N' dados registrados")
        self.btn_rep.clicked.connect(self.update_rep_n)
        self.btn_exp_rep = QPushButton("Exportar relatório para Excel")
        self.btn_exp_rep.clicked.connect(self.exp_rep_excel)
        self.n_itens_rep = QLineEdit()
        self.n_itens_rep.setPlaceholderText("N° Itens")
        self.status_itens = QLineEdit()
        self.pbar_rep = QProgressBar()
        self.pbar_rep.setFont(fonte)
        self.rep_func = QHBoxLayout() #Layout dos botões abaixo da tabela
        self.rep_func.addWidget(self.btn_pdate_rep,20)
        self.rep_func.addWidget(self.btn_rep,22)
        self.rep_func.addWidget(self.n_itens_rep,4.5)
        self.rep_func.addWidget(self.pbar_rep,38)
        self.rep_func.addWidget(self.btn_exp_rep,15.5)
        #Insere abaixo da tabela os itens:
        rep_tab.addStretch()
        rep_tab.addWidget(self.rep_table,90)
        rep_tab.addLayout(self.rep_func,10)
        rep_tab.addStretch()
        
        """
        Cria os widgets da aba informativa
        """
        #Cria a aba informativa do final
        self.mapa = QLabel() #
        self.mapa.setPixmap(QPixmap("icons/MAPA_MENTAL.png"))
        info_tab.addWidget(self.mapa)
        info_tab.setAlignment(Qt.AlignHCenter)

        ############################Criando abas##############################
        self.tabs = QTabWidget() #Widget das tabs que reune as 4
        self.tab1 = QWidget() #Tab de emulação do benchmark
        self.tab2 = QWidget() #Tab do banco de dados
        self.tab3 = QWidget() #Relatório de Falhas
        self.tab4 = QWidget() #Informações complementares
        self.tabs.addTab(self.tab1,"Simulação do Sistema")
        self.tabs.addTab(self.tab2,"Consulta Geral ao Banco de Dados")
        self.tabs.addTab(self.tab3,"Consultar Tabela do Relatório de Falhas")
        self.tabs.addTab(self.tab4,"Informações sobre o TCC: Mapa Mental")
        
        self.tab1.setLayout(self.main_tab) # Adicionando a aba de simulação
        self.tab2.setLayout(db_tab) # Adicionando adicionando aba do db
        self.tab3.setLayout(rep_tab) # Adicionando adcionando aba
        self.tab4.setLayout(info_tab) # Adicionando para a tab1
        
        #Adiciona ao box principal a estrutura de tabs
        main.addWidget(self.tabs) #Coloca a estrutura de tabs no layout principal
        self.setLayout(main)
    
    def plot(self, x, y, plotname, color):
        pen = mkPen(color=color)
        self.grafico.plot(x, y, name=plotname, pen=pen, symbolSize=5, symbolBrush=(color))
    
    def maria_conn(self):
        try:
            self.conn = mariadb.connect(
                user="root",
                password=self.passw,
                host="127.0.0.1",
                port=3306,
                database="db_ofc_tcc")
            self.cur = self.conn.cursor()
        except mariadb.Error as e:
            QMessageBox.warning(self,"Aviso",f"Sem conexão com o Banco de dados, devido ao erro: {e}")
    
        self.list_status.addItem("Conectado ao db_tcc")
        if "Conectado ao db_tcc" not in self.lines: #Se não estiver coloca
            self.lines.append("Conectado ao db_tcc")
        
    def bench(self):
        ask_dir = "Escolha o diretório onde o Benchmark se encontra"
        self.benchmark = str(QFileDialog.getExistingDirectory(None,ask_dir))
        self.list_status.clear() #Limpa a lista toda vez que o botão de benchmark é pressionado
        if self.benchmark != '': #Se não for vazio, continua
            arqs = os.listdir(self.benchmark)
            bench = [] #Reiniciado quando escolhida outra pasta
            self.lines = [] #Lista das linhas do listwidget reinicia
            
            for arq in arqs:
                if '.slx' in arq: #Se a extenção do arquivo for a mesma do simulink
                    bench.append(arq)
            
            if not(bench): #Se o vetor estiver vazio
                not_bench = f"Não foi encontrado arquivo do simulink no diretório selecionado {self.benchmark}!"
                QMessageBox.warning(self,"Aviso!",not_bench)
            else:
                self.list_status.addItem(f"Diretório: {self.benchmark}")
                self.lines.append("\n-------------------------------------------------------------\n")
                self.lines.append(f"Diretório: {self.benchmark}")
                self.cmb_bench.addItems(bench)
                self.maria_conn() #Inicia conexão com o banco de dados
                self.btn_start.setDisabled(False) #Habilita o botão para iniciar os testes
                self.pbar.setValue(10)#Coloca 10% na barra de progresso
    
    def get_param(self):
        
        print(self.line_time.text())
        #Valida o que o usuário digitou
        try: 
            if float(self.line_time.text()) < 0:
                QMessageBox.warning(None,"Erro!","Insira um valor numérico real não negativo no Tempo de Simulação!")
                return
            else:
                simu_time = float(self.line_time.text())
        except: 
            QMessageBox.warning(None,"Erro!","Insira um valor numérico real não negativo no Tempo de Simulação!")
            return
        
        #Define a função de turbulência da classe aircraft
        turb = self.cmb_turb.currentText()
        if turb == 'None':
            func_turb = "setNoTurbulence()"
        elif turb == 'Light':
            func_turb = "setLightTurbulence()"
        elif turb == 'Moderate':
            func_turb = "setModerateTurbulence()"
        elif turb == 'Severe':
            func_turb = "setSevereTurbulence()"
            
        param = [self.cmb_font.currentText(),self.cmb_type.currentText(),self.cmb_ampl.currentText(),
                 self.cmb_bias.currentText(),self.cmb_freq.currentText().replace("π","*pi"),func_turb,
                 self.cmb_ctrl1.currentIndex()+1,simu_time]
        print(param)
        
        return param
        
    def start(self):
        global Relatorio_TXT_Etapas, time, time_fail, delta_comm, delta_meas, ofc_falhas
        
        #Limpa variáveis globais
        time = []
        time_fail = []
        delta_comm = []
        delta_meas = []
        ofc_falhas = []

        #Treina os parâmetros
        simu = self.cmb_bench.currentText()
        self.system = self.benchmark+"/"+self.cmb_bench.currentText() #Caminho do sistema
        #monitora(system) #chama o simulink para emular o sistema
        quest = f"O sistema para emulação no Simulink é {self.system}?"
        if QMessageBox.question(self,"Tem certeza?",quest,QMessageBox.Yes|QMessageBox.No,
                                QMessageBox.No) == QMessageBox.Yes:
            self.metodo = self.cmb_treino.currentText() #Pega do combo o texto do modelo a treinar
            
            self.benchmark_simu = self.cmb_bench.currentText()
            
            self.parametros = self.get_param() #Recebe os parâmetros informados pelo usuário
            if not self.parametros:
                self.line_time.setFocus()
                return
            
            self.list_status.addItem(f"Treinando o modelo {simu} pelo método {self.metodo}")
            self.lines.append(f"Treinando o modelo {simu} pelo método {self.metodo}")
            self.pbar.setValue(15)
            
            #Chama a classe do treino
            tic_mdl = datetime.now()
            #Dá ao usuário a possibilidade de treinar ou carregar modelo
            quest2 = "Deseja treinar os dados? O não implica em carregar módulo default de treino"
            if QMessageBox.question(self,"Treinar ou não?",quest2,QMessageBox.Yes|QMessageBox.No,
                                QMessageBox.No) == QMessageBox.Yes and self.metodo != 'Support Vector Machine':
                self.modelo = treina_modelo(self.metodo,True)
                method = "Treinado"
            else: #Se for SVM, carrega o modelo pronto ao invez de treinar
                self.modelo = treina_modelo(self.metodo,False)
                method = "Carregado"
            
            self.list_status.addItem(f"Modelo {simu} foi {method} pelo método {self.metodo} em {datetime.now()-tic_mdl}")
            self.lines.append(f"Modelo {simu} foi {method} pelo método {self.metodo} em {datetime.now()-tic_mdl}")
            self.pbar.setValue(25)
            self.list_status.addItem(f"Iniciando {self.system} no Simulink")
            self.lines.append(f"Iniciando {self.system} no Simulink")
            #monitora(system) #Associa o monitoramento 
            
            self.list_status.addItem("Iniciando o MatLab (estimado: 13.6s)")
            self.lines.append("Iniciando o MatLab (estimado: 13.6s)")

            self.pbar.setValue(30)
            tic_matlab = datetime.now()
            
            self.eng = matlab.engine.start_matlab() #Background true para receber os valores
            self.list_status.addItem(f"O MatLab foi iniciado em {datetime.now()-tic_matlab}")
            self.lines.append(f"O MatLab foi iniciado em {datetime.now()-tic_matlab}")
            
            print(self.benchmark)
            self.eng.addpath(self.benchmark,nargout=0)
            
            #Função que carrega todas as variáveis necessárias pra se iniciar o simulink
            self.SimulinkPlant(self.parametros)
            self.list_status.addItem("Carregando modelo no SimuLink (estimado: 6.35s)")
            self.lines.append("Carregando modelo no SimuLink (estimado: 6.35s)")
            self.pbar.setValue(32.5)
            self.eng.eval(f"model = '{self.system}'",nargout=0)
            self.eng.eval(f"simulation.setSimulinkModel('{self.benchmark_simu}');",nargout=0)

            self.pbar.setValue(35)
            self.list_status.addItem("Carregando prâmetros ao modelo Simulink")
            self.lines.append("Carregando prâmetros ao modelo Simulink")
            
            tic_m = datetime.now()
            self.eng.eval("SimOut = sim(simulation.simulink_model, 'SrcWorkspace', 'current');",nargout=0)
            self.processo = self.eng.eval("""[SimOut.dx_comm SimOut.dx_meas SimOut.time];""")
            self.list_status.addItem(f"O Modelo {simu} foi treinado pelo método {self.metodo} em {datetime.now()-tic_m}")
            self.lines.append(f"O Modelo {simu} foi treinado pelo método {self.metodo} em {datetime.now()-tic_m}")

            self.pbar.setValue(40)
            self.list_status.addItem(f"Emulando {self.system} no Simulink")
            self.lines.append(f"Emulando {self.system} no Simulink")
            Relatorio_TXT_Etapas = self.lines
            #Emulação do sistema
            
            self.delta_comm = [] #Zera a lista de declara
            self.delta_meas = []
            self.ofc_fail = [] #Armazena dados das falhas encontradas
            self.time_fail = []
            self.time = []
            self.barra = 40
            self.janela = 40 #Tamanho da janela de dados a ser colatada
            self.i = 0 #Número da iteração
            self.total_itter = self.parametros[-1]*40 + 1 #Numero total de iterações
            #Loop do timar para plotar o gráfico
            self.timer = QTimer()
            self.timer.setInterval(10)
            self.timer.timeout.connect(self.update_graph)
            QMessageBox.information(self,"Aviso",f"O {self.system} será emulado")
            self.timer.start()
            
        else:
            pass
    
    def update_graph(self):
        
        global time, delta_comm, delta_meas, simulado, ofc_falhas, time_fail
        self.barra += (self.i/(self.total_itter) - 0.4*(self.i/self.total_itter))/(self.total_itter/200.4)

        #Recebe apenas os valores desejados, comando, medida e tempo
        self.delta_comm.append(self.processo[self.i][0])
        self.delta_meas.append(self.processo[self.i][1])
        self.time.append(self.processo[self.i][2])
        
        dat = [self.processo[self.i][0],self.processo[self.i][1],self.processo[self.i][2]]
        
        win = []
        for i in range(self.janela):
            if self.i < self.total_itter-self.janela:
                win.append(float(self.processo[i+self.i][0])) #Recebe o valor das janelas respectivas
            else:
                win.append(float(self.processo[randint(0,self.total_itter-1)][0])) #Revebe valor de indice aleatório
        
        w = array(win)
        result = int(self.modelo.predict(w.reshape(1,-1)).astype(int16)[0]) #Recebe 0 se não há falha e 1 se houver
        if result == 1: #Se é uma falha, acrescenta ao vetor o dado da falha
            self.ofc_fail.append(self.processo[self.i][1])
            self.time_fail.append(self.processo[self.i][2])
        
        reg = [dat[0],dat[1],dat[2],result,win] #Cria vetor com os dados e a classificação dos sinais
        self.update_db(reg,self.parametros) #Atualiza o banco de dados com a informação mais recente
        
        self.dx_comm.setData(self.time, self.delta_comm)
        self.dx_meas.setData(self.time, self.delta_meas)
        
        if self.ofc_fail: #Se houver dados nesse objeto
            self.dx_falhas.setData(self.time_fail, self.ofc_fail)
        else:
            self.dx_falhas.setData([0],[0])
        
        self.pbar.setValue(self.barra)#Coloca % na barra de progresso
        self.i += 1
        if self.i >= self.total_itter-1:
            print(self.barra)
            self.timer.stop()
            self.conn.commit()
            self.pbar.setValue(100)
            time = self.time
            delta_comm = self.delta_comm
            delta_meas = self.delta_meas
            ofc_falhas = self.ofc_fail
            time_fail = self.time_fail
            simulado = True #Variável que habilita impressão do gráfico
            QMessageBox.information(self,"Sucesso!",f"O processo {self.system} foi emulado com sucesso!")
            return
    
    def SimulinkPlant(self,param):
        """
        Essa função objetiva declarar as variáveis necessárias para desenvolvimento da simulação 
        
        Parameter
        ----------
        
        param: array
            Array com todos os parâmetros fornecidos pelo usuário    
        
        Returns
        -------
        None. Mas realiza inúmeros comandos para simular a planta e declarar as variáveis
    
        """
        
        #Iniciando o benchmark e carrega as principais variáveis ao console da API
        self.eng.eval("ofc_benchmark_init;",nargout=0)
        self.eng.eval("simulation.setSimulinkModel('ofc_benchmark_acquire');",nargout=0)
        #Carrega as variáveis: aircraft, ofc, servoModel, servoReal e simulation!
        
        self.eng.eval("servoReal.randomiseServoParameters()",nargout=0) #Faz o objeto servo real ficar aleatório
        self.eng.eval(f"ofc.setLocation('{param[0]}')",nargout=0)
        self.eng.eval(f"ofc.setType('{param[1]}')",nargout=0)
        self.eng.eval(f"ofc.setAmplitude({param[2]})",nargout=0)
        self.eng.eval(f"ofc.setBias({param[3]})",nargout=0)
        self.eng.eval(f"ofc.setFrequency({param[4]})",nargout=0)
        self.eng.eval("ofc.setPhase(0)",nargout=0)
        self.eng.eval("ofc.setStartTime(0)",nargout=0)
        self.eng.eval(f"aircraft.{param[5]}",nargout=0)
        
        #Cria sinal aleatório de controle
        self.eng.eval("""controls = {@(x)aircraft.setControlInput('FPA_control'), ...
                        @(x)aircraft.setControlInput('NZ_step', x(1), x(2), x(3)), ...
                        @(x)aircraft.setControlInput('NZ_sine', x(1), x(2), x(3), x(4)), ...
                        @(x)aircraft.setControlInput('NZ_chirp', x(1))};""",nargout=0)
        self.eng.eval("controls{"+str(param[6])+"}([10^randi([-1 1]),randi([10 25]),randi([35, 50]),randi([0, 10])])",
                        nargout=0)
        self.eng.eval(f"simulation.setStopTime({param[7]})",nargout=0) #Seta o tempo final de simulação
    
    def update_tb(self):
        global df
        
        self.pbar_db.setValue(0) #Zera a barra de progresso
        
        limite = self.n_itens.text()
        self.pbar_db.setValue(10)
        try:
            int(limite)
        except:
            QMessageBox.warning(self,"Atenção!","Insira um número inteiro!")
            return
        
        if int(limite) <= 0:
            QMessageBox.warning(self,"Atenção!","Insira um número positivo maior que zero!")
            return
        try:
            self.cur.execute(f"SELECT * FROM tb_ofc_dt ORDER BY id DESC LIMIT {limite};")
        except:
            self.maria_conn()
            self.cur.execute(f"SELECT * FROM tb_ofc_dt ORDER BY id DESC LIMIT {limite};")
        
        self.pbar_db.setValue(20)
        dados = self.cur.fetchall()
        #Convertendo os dados provenientes do banco de dados para um dataframe e  então envia para tabela
        self.df = DataFrame(dados, columns = ["id","data","Deflexão comando","Deflexão medida",
                                              "Tempo (s)","Falha","Parâmetros"])
        df = self.df
        self.pbar_db.setValue(30)
        
        self.db_table.setModel(pandasModel(self.df)) #Coloca os dados consultados na tabela
        self.db_table.setColumnWidth(0,45)
        self.db_table.setColumnWidth(1,120)
        self.db_table.setColumnWidth(2,105)
        self.db_table.setColumnWidth(3,105)
        self.db_table.setColumnWidth(4,65)
        self.db_table.setColumnWidth(5,42)
        self.db_table.setColumnWidth(6,self.tabela_param)
        self.pbar_db.setValue(100)
    
    def update_tb_1000(self):
        global Relatorio_TXT_Etapas, df
        
        try:
            self.cur.execute("SELECT * FROM tb_ofc_dt ORDER BY id DESC LIMIT 1000;")
        except:
            self.maria_conn()
            self.cur.execute("SELECT * FROM tb_ofc_dt ORDER BY id DESC LIMIT 1000;")
            
        falhas = self.cur.fetchall()
        self.list_status.addItem("O relatório de falhas foi gerado!")
        self.lines.append("O relatório de falhas foi gerado!")
        Relatorio_TXT_Etapas = self.lines
        
        self.df = DataFrame(falhas, columns = ["id","data","Deflexão comando","Deflexão medida",
                                              "Tempo (s)","Falha","Parâmetros"])
        df = self.df
        
        self.db_table.setModel(pandasModel(self.df))
        self.db_table.setColumnWidth(0,45)
        self.db_table.setColumnWidth(1,120)
        self.db_table.setColumnWidth(2,105)
        self.db_table.setColumnWidth(3,105)
        self.db_table.setColumnWidth(4,65)
        self.db_table.setColumnWidth(5,42)
        self.db_table.setColumnWidth(6,self.tabela_param)
        self.pbar_db.setValue(100)
    
    def update_db(self,dt,p):
        """
        Essa função cadastra um item no banco de dados

        Parameters
        ----------
        dt : tuple
            Linha proveniente do objeto de dados do matlab com três linhas (tempo, comando, medida e falha).
        p : list
            Lista dos parâmetros selecionados pelo usuário.
        Returns
        -------
        None.

        """
        global freq, ctrl, ampl
        fe = p[4].replace('*pi','π')
        pa = f"Metodo: {self.metodo}; F_OFC: {p[0]}; T_OFC: {p[1]}; Ampli.: {p[2]}; Bias: {p[3]}; Freq: {fe};"
        pa += f"Turb: {p[5].replace('()','')}; T_Ctrl: {ctrl[p[6]]}; t_simu: {p[7]}s; window: {dt[4]}"
        
        nw = datetime.now().strftime("%Y-%m-%d %H:%M:%S")#datetime.strftime(datetime.now(),"%d/%b/%Y - %H:%M")
        self.cur.execute("""INSERT INTO tb_ofc_dt (data,dx_comm,dx_meas,dt,falha,parametros) VALUES 
                         (?,?,?,?,?,?);""",[nw,dt[0],dt[1],dt[2],dt[3],pa])

    def exp_graph(self):
        """
        Essa função exporta o gráfico como está na tela em forma de imagem

        Returns
        -------
        None.

        """
        global time, delta_comm, delta_meas, simulado
        
        if simulado:
            ask_dir = "Escolha o diretório onde o deseja salvar o gráfico" #string que pergunta o diretório
            save = str(QFileDialog.getExistingDirectory(None,ask_dir)) #Pede ao usuário o diretório onde ele quer salvar
            self.grafico.plot(time,delta_comm, symbolSize=5,symbolBrush=("#15bf48"), 
                                                 pen=mkPen(color="#15bf48", width=2))
            self.grafico.plot(time,delta_meas, symbolSize=5,symbolBrush=("#56fceb"), 
                                                 pen=mkPen(color="#56fceb", width=2))
            self.grafico.plot(time_fail,ofc_falhas, symbolSize=15,symbol='x',symbolBrush=("#fc031c"), 
                                                     pen=mkPen(color="#323232", width=0.001))
            
            exporter = exporters.ImageExporter(self.grafico.plotItem) #Exporta o objeto do gráfico
            exporter.export(save+f'/graph_{int(datetime.timestamp(datetime.now()))}.png')  #Salva como png o gráfico
            QMessageBox.information(self,"Concluído!",f"Gráfico salvo com sucesso em: {save}")
        else:
            QMessageBox.warning(self,"Atenção!","O sistema ainda não foi emulado!")
    
    def exp_excel_all(self,aq):
        """
        Essa função exporta os dados adquiridos para uma planilha do excel

        Returns
        -------
        Não retorna parâmetros, apenas executa a ação de exportar para uma planilha

        """
        global df, dff
        
        if not(df.empty) or not(dff.empty): #Se um dos dois não for vazio
            salve = str(QFileDialog.getExistingDirectory(None, "Escolha o diretório onde quer salvar o relatório"))
            save = salve+"/Relatório_OFC_MFF.xlsx"
            
            if aq==0 and not(df.empty): #Se os dados foram coletados, gera dos dados
                df.to_excel(save,sheet_name="Relatório_OFC_MFF",index=False)
                info_save_excel = f"O relatório geral foi salvo em {save}!"
            elif aq==1 and not(dff.empty): #Se as falhas foram coletadas, gera as falhas
                dff.to_excel(save.replace("MFF","FALHAS_MFF"),sheet_name="Relatório_Falhas_OFC_MFF",index=False)
                info_save_excel = f"O relatório final das falhas de caráter oscilatória foi salvo em {save}!"
            elif aq==2 and (not(df.empty) or not(dff.empty)): #Salva ambos
                if not(df.empty):
                    df.to_excel(save,sheet_name="Relatório_OFC_MFF",index=False)
                    info_save_excel = f"O relatório geral foi salvo em {save}!"
                if not(dff.empty):
                    dff.to_excel(save.replace("MFF","FALHAS_MFF"),sheet_name="Relatório_Falhas_OFC_MFF",index=False)
                    info_save_excel = f"O relatório final das falhas de caráter oscilatória foi salvo em {save}!"

                if not(df.empty) and not(dff.empty):
                    info_save_excel = f"Os dois relatórios foram salvos em {save}!"

            QMessageBox.information(self,"Sucesso!",info_save_excel)
        else:
            info_not_save = "Nenhum dos dois relatórios foram gerados ainda!"
            QMessageBox.warning(self,"Atenção!",info_not_save)

    def exp_rep_excel(self):
        """
        Essa função exporta os dados adquiridos para uma planilha do excel

        Returns
        -------
        Não retorna parâmetros, apenas executa a ação de exportar para uma planilha

        """
        self.exp_excel_all(1)

    def exp_dados_excel(self):
        """
        Essa função exporta os dados adquiridos para uma planilha do excel

        Returns
        -------
        Não retorna parâmetros, apenas executa a ação de exportar para uma planilha

        """
        self.exp_excel_all(0)

    def exp_rep(self):
        """
        Exporta um relatório em txt com os dados de falhas é acionado ao clickar duas vezes na caixa com logs
        duplo click em 
        Returns
        -------
        None.

        """
        global Relatorio_TXT_Etapas #Insere na função a variável compartilhada entre classes
        if Relatorio_TXT_Etapas:
            dire = str(QFileDialog.getExistingDirectory(None, "Escolha o diretório para salvar o relatório em TXT!"))
            with open(dire+"/Relatorio_TXT_Etapas.txt",'w') as txt:
                txt.write("Relatório das etapas realizadas pelo software:\n")
                for line in Relatorio_TXT_Etapas: #Para cada linha, escreve no TXT
                    txt.write("\n"+str(line))
                    
            QMessageBox.information(None,"Feito!","O relatório com as etapas realizadas foi salvo com sucesso!")
        else:
            QMessageBox.warning(None,"Atenção!","O relatório com as etapas ainda não foi gerado!")
    
    def update_rep_n(self): #Essa função irá popular a tabela de dados
        global dff
        limit = self.n_itens_rep.text()
        self.pbar_rep.setValue(10) #Reseta o valor da barra de progresso para 10%
        try:
            int(limit)
        except:
            QMessageBox.warning(self,"Atenção!","Insira um número inteiro!")
            return
        
        try:
            self.cur.execute(f"SELECT * FROM tb_ofc_dt WHERE falha = 1 ORDER BY id DESC LIMIT {limit}")
        except:
            self.maria_conn()
            self.cur.execute(f"SELECT * FROM tb_ofc_dt WHERE falha = 1 ORDER BY id DESC LIMIT {limit}")

        falhas = self.cur.fetchall()
        self.dff = DataFrame(falhas, columns = ["id","data","Deflexão comando","Deflexão medida",
                                                "Tempo (s)","Falha","Parâmetros"])
        dff = self.dff
        self.rep_table.setModel(pandasModel(self.dff))
        self.rep_table.setColumnWidth(0,45)
        self.rep_table.setColumnWidth(1,120)
        self.rep_table.setColumnWidth(2,110)
        self.rep_table.setColumnWidth(3,100)
        self.rep_table.setColumnWidth(4,65)
        self.rep_table.setColumnWidth(5,42)
        self.rep_table.setColumnWidth(6,self.tabela_param)
        self.pbar_rep.setValue(100)
        
    def update_rep(self): #Essa função irá popular a tabela de dados
        global dff
        try:
            self.cur.execute("SELECT * FROM tb_ofc_dt WHERE falha = 1 ORDER BY id DESC")
        except:
            self.maria_conn()
            self.cur.execute("SELECT * FROM tb_ofc_dt WHERE falha = 1 ORDER BY id DESC")

        falhas = self.cur.fetchall()
        self.dff = DataFrame(falhas, columns = ["id","data","Deflexão comando","Deflexão medida",
                                                "Tempo (s)","Falha","Parâmetros"])
        dff = self.dff
        self.rep_table.setModel(pandasModel(self.dff))
        self.rep_table.setColumnWidth(0,45)
        self.rep_table.setColumnWidth(1,120)
        self.rep_table.setColumnWidth(2,110)
        self.rep_table.setColumnWidth(3,100)
        self.rep_table.setColumnWidth(4,65)
        self.rep_table.setColumnWidth(5,42)
        self.rep_table.setColumnWidth(6,self.tabela_param)
        self.pbar_rep.setValue(100)
    
    def pdate_ampl(self):
        if self.cmb_font.currentText() in ['sensor','cs_sensor']:
            self.lbl_ampl.setText("Ampl(mm)/Bias(mm)/Freq(rad/s):")
        else:
            self.lbl_ampl.setText("Ampl(mA)/Bias(mA)/Freq(rad/s):")
    
    def filed(self): #Abre o arquivo em forma de dicionário e retorna o caminho completo (posição 0)
        path = QFileDialog.getOpenFileName(self,"Abre um arquivo do excel","","All Files(*);;*xlsx *xls")
        
        if (".xls" in path[0]): #Se for um arquivo do excel
            modelo = ExcelFile(path[0]).parse(0,skiprows=1)# Carrega o template em um Excel e a planilha
            self.relatorio.setModel(pandasModel(modelo))
            self.tab2.setDisabled(False)
            self.tab2.update()
            self.update()
        else: #Se não for...
            QMessageBox.warning(self,"Arquivo incorreto","Escolha um arquivo do Excel (.xlsx ou .xls)!")
     
    def salva(self): #Salva o dataset do relatório em um arquivo excel
        global df, dff, Relatorio_TXT_Etapas, simulado
    
        if not(df.empty) or not(dff.empty) or Relatorio_TXT_Etapas or simulado: #Se tem algo para salvar, procede
            r1 = ""; r2 = ""; r3 = ""
            salve = str(QFileDialog.getExistingDirectory(None, "Escolha o diretório onde quer salvar o relatório"))
            save_total = salve+"/Relatório_OFC_MFF.xlsx"
            save_falhas = salve+"/Relatório_OFC_Falhas_MFF.xlsx"
            save_txt = salve+"/Relatorio_TXT_Etapas.txt"
            
            if not(df.empty): #Se o dataframe com os dados contar com mais de 0 codigos
                df.to_excel(save_total,sheet_name="Relatório_OFC_MFF",index=False)
                r1 = "Relatório_OFC_MFF,"
            if not(dff.empty): #Se as falhas foram coletadas, gera as falhas
                dff.to_excel(save_falhas,sheet_name="Relatório_Falhas_OFC_MFF",index=False)
                r2 = "Relatório_Falhas_OFC_MFF,"
            if len(Relatorio_TXT_Etapas) > 0: #Se o relatório txt não está vazio
                with open(save_txt,'w') as txt:
                    txt.write("Relatório das etapas realizadas pelo software:\n")
                    for line in Relatorio_TXT_Etapas: #Para cada linha, escreve no TXT
                        txt.write("\n"+str(line))
                r3 = "Relatorio_TXT_Etapas"
            
            duplas = (r1 or r2) or (r1 or r3) or (r2 or r3) #Uma dupla
            todos = (r1 and r2 and r3) #Todos
            solo = (r1 or r2 or r3) and not (duplas) #Apenas um
            
            if duplas: #Plural
                QMessageBox.information(self,"Sucesso!",f"Os relatórios: {r1}{r2}{r3} foram salvos!".replace(","," e "))
            elif todos:
                QMessageBox.information(self,"Sucesso!",f"Os relatórios: {r1}{r2}{r3} foram salvos!")
            elif solo: #Singular
                QMessageBox.information(self,"Sucesso!",f"O relatório: {r1}{r2}{r3} foi salvo!")
            if simulado:#Se foi simulado, exporta o gráfico
                if (QMessageBox.warning(self,"Aviso","Você gostaria de salvar o gráfico?",
                                        QMessageBox.Yes|QMessageBox.No,QMessageBox.No) == QMessageBox.Yes):
                    self.exp_graph()
        else:
            QMessageBox.warning(self,"Atenção!","Nenhum relatório foi gerado, portanto não há o que salvar!")
            
class pandasModel(QAbstractTableModel):
    # Cria o modelo que converte do pandas ao PYQT5
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None): #Função que conta as linhas do objeto
        return self._data.shape[0]

    def columnCount(self, parnet=None):#Função que conta as colunas do objeto
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

class Window(QMainWindow): #QWidget
    def __init__(self):
        global centro
        super().__init__()
        cp = QDesktopWidget().availableGeometry().center()
        self.resize(2*cp.x(), 2*cp.y())
        self.center()
        self.setWindowTitle(f"Interface do TCC para identificação de OFC por métodos de {ml} {versao} - {mff}")
        self.setWindowIcon(QIcon("icons/TCC_Icon.png"))
        self.UI()
        self.centro = central() #Chama a classe
        self.showMaximized()
        
    def UI(self):
        #Cria a barra de ferramentas
        tb = self.addToolBar("Ferramentas")
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        manualtb = QAction(QIcon("icons/manual.png"),"Manual",self)
        manualtb.setToolTip("Abre o manual caso você tenha o MsPowerPoint")
        tb.addAction(manualtb)
        opentb = QAction(QIcon("icons/folder.png"),"Abrir",self)
        opentb.setToolTip("Aponte o diretório com o benchmark")
        tb.addAction(opentb)
        exp_graph = QAction(QIcon("icons/exp_graph.png"),"Exp_Graph",self)
        exp_graph.setToolTip("Exporta o gráfico em formato png")
        tb.addAction(exp_graph)
        exp_excel = QAction(QIcon("icons/exp_excel.png"),"Exp_Excel",self)
        exp_excel.setToolTip("Exporta o banco de dados da tabela em formato Excel")
        tb.addAction(exp_excel)
        exp_report = QAction(QIcon("icons/exp_report.png"),"Exp_Report",self)
        exp_report.setToolTip("Exporta o relatório em formato TXT")
        tb.addAction(exp_report)
        savetb = QAction(QIcon("icons/save.png"),"Salvar",self)
        savetb.setToolTip("Exporta o gráfico, banco de dados e o relatório")
        tb.addAction(savetb)
        exittb = QAction(QIcon("icons/exit.png"),"Sair",self)
        exittb.setToolTip("Sair do software")
        tb.addAction(exittb)
        tb.actionTriggered.connect(self.btns) #Cria função com todos os botões
        self.setCentralWidget(central())
        self.show()
        
    def center(self): #Função que centraliza a interface
        qr = self.frameGeometry() #Define um frame com geometria
        cp = QDesktopWidget().availableGeometry().center() #Encontra ponto central
        qr.moveCenter(cp) #Move ao centro
        self.move(qr.topLeft()) #Seta a origem no canto superior esquerdo da tela

    def saindo(self):
        mbox = QMessageBox.information(self,"Aviso","Você realmente deseja sair?",
                                       QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if mbox == QMessageBox.Yes:
            self.centro.close() #Fecha a classe
            self.close() #Fecha o programa
            exit(1) #Sai do programa
    
    def btns(self,btn): #Essa função encontra o botão da toolbox
        
        if btn.text() == "Manual":
            try:
                os.startfile("docs\\manual_TCC.pptx")
            except:
                point = "É provável que você não tenha o MSPowerPoint Instalado!"
                QMessageBox.information(self,"Aviso",point)
                return
        elif btn.text() == "Abrir":
            self.centro.bench()
        elif btn.text() == "Exp_Graph":
            self.centro.exp_graph()
        elif btn.text() == "Exp_Excel":
            self.centro.exp_excel_all(2) #2 de argumento para imprimir todos
        elif btn.text() == "Exp_Report":
            self.centro.exp_rep()
        elif btn.text() == "Salvar":
            self.centro.salva()
        elif btn.text() == "Sair":
            self.saindo()
        self.centro.update()
        self.update()

def main(): # Inicia a aplicação
    App = QApplication(sys.argv)
    App.setStyle('Fusion')
    window = Window()
    window.show()
    modern_style = str_style()
    App.setStyleSheet(modern_style)
    sys.exit(App.exec_())
    
if __name__ == '__main__':
    main()