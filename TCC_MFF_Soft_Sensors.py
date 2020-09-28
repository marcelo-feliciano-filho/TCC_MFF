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
from PyQt5.QtWidgets import (QWidget, QLabel, QApplication, QPushButton, QLineEdit, QTabWidget,QAction,
                             QMessageBox, QDesktopWidget, QVBoxLayout, QMainWindow, QProgressBar,
                             QFileDialog, QTableView, QHBoxLayout, QComboBox, QTableWidget,QListWidget)
from PyQt5.QtGui import QPixmap, QFont, QIcon #Permite imprimir imagens na tela e alterar a fonte
from PyQt5.QtCore import Qt, QAbstractTableModel
from pyqtgraph import exporters, mkPen, plot, PlotCurveItem
from pandas import ExcelFile, DataFrame
from MatLabPy import SimulinkPlant
#Apenas para testes
from datetime import datetime
from random import randint

from TCC_MFF_Treino import treina_modelo
from style import str_style #Importa a stylesheet necessária para modernizar essa interface

versao = "V.1.0.0 - MVP"
email = "marcelo.feliciano.f@outlook.com"
font = ['sensor', 'current', 'cs', 'cs_sensor'] #Fontes de perturbação
type_ofc = ['none','liquid','solid']#Tipos das perturbações
turb = ['None','Light','Moderate','Severe','Undefined'] #Tipos de turbulência
ctrl = ['FPA_control','NZ_step','NZ_chirp','NZ_sine'] #Tipos de controle
ampl = ['0.1','0.5','1','1.5','2','3','4','6','8','10'] #Amplitudes de onda
bias = ['0.01','0.05','0.1','0.2','0.3','0.5','1','1.25']#Offset do sensor
freq = ['π','2π','3π','4π','5π','6π','8π','10π','20π'] #Frequências
treino = ['Decision Tree','Newral Network: MLP'] #,'Support Vector Machine'

class central(QWidget): #Cria widget para colocar na janela central onde as duas
    
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icons/icone_TCC.png"))
        self.UI()
    
    def UI(self):
        main = QVBoxLayout() #Widget principal, onde serão colocadas todas as abas
        self.unit_y = "Ângulo de deflexão (rad)"
        self.unit_x = "Segundos (s)"
        self.df = DataFrame({})
        
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
        #self.lbl_icon = QLabel() #Label que armazena o icone
        #Icone da pontifícia:
        #icone_tcc = QPixmap("icons/TCC_Icon.png").scaled(50, 61, Qt.KeepAspectRatio, Qt.FastTransformation)
        #self.lbl_icon.setPixmap(icone_tcc)
        #self.lbl_icon.setAlignment(Qt.AlignCenter)
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
        self.lbl_type = QLabel("Tipo da OFC: ")
        self.cmb_type = QComboBox(self) #Cria o combobox do primeiro parâmetro
        self.cmb_type.addItems(type_ofc) #Carrega lista das fontes de perturbação
        self.lbl_turb = QLabel("Turbulência: ")
        self.cmb_turb = QComboBox(self) #Cria o combobox do segundo parâmetro
        self.cmb_turb.addItems(turb)
        self.lbl_ctrl1 = QLabel("Tipo Controle: ")
        self.cmb_ctrl1 = QComboBox(self)#Cria o combobox do terceiro parâmetro
        self.cmb_ctrl1.addItems(ctrl)
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
        self.list_status = QListWidget()
        self.btn_start = QPushButton("Iniciar")
        self.btn_start.clicked.connect(self.start)
        self.btn_start.setDisabled(True)
        self.pbar = QProgressBar()
        self.pbar.setFont(fonte)
        #Insere no formulário os widgets:
        self.formulario.addStretch()
        #self.formulario.addWidget(self.lbl_icon)
        self.formulario.addWidget(self.lbl_imp)
        self.formulario.addWidget(self.btn_bch)
        self.formulario.addWidget(self.lbl_param)
        self.formulario.addWidget(self.lbl_font)
        self.formulario.addWidget(self.cmb_font)
        self.formulario.addWidget(self.lbl_type)
        self.formulario.addWidget(self.cmb_type)
        self.formulario.addWidget(self.lbl_turb)
        self.formulario.addWidget(self.cmb_turb)
        self.formulario.addWidget(self.lbl_ctrl1)
        self.formulario.addWidget(self.cmb_ctrl1)
        self.formulario.addWidget(self.lbl_ampl)
        self.formulario.addLayout(self.amp_bias_freq)
        self.formulario.addWidget(self.lbl_ctrl)
        self.formulario.addWidget(self.lbl_bench)
        self.formulario.addWidget(self.cmb_bench)
        self.formulario.addWidget(self.lbl_treino)
        self.formulario.addWidget(self.cmb_treino)
        self.formulario.addWidget(self.btn_start)
        self.formulario.addWidget(self.list_status)
        self.formulario.addWidget(self.pbar)
        self.formulario.setAlignment(Qt.AlignCenter)
        self.formulario.addStretch()
        
        #cria o gráfico
        self.hour = [1,2,3,4,5,6,7,8,9,10]
        self.temperature_1 = [30,32,34,32,33,31,29,32,35,45]
        self.temperature_2 = [50,35,44,22,38,32,27,38,32,44]
        self.grafico = plot()
        self.grafico.setBackground('#323232') #Coloca a cor de fundo igual a do restante da interface
        # Coloca título no gráfico
        self.grafico.setTitle("Simulação do Benchmark OFC: AirBus", color="#56fceb", size="20pt")
        self.styles = {"color": "#56fceb", "font-size": "16px"} #Cria os estilos de fonte do gráfico
        self.grafico.setLabel("left", self.unit_y, **self.styles) #Insere a unidade do eixo Oordenado
        self.grafico.setLabel("bottom", self.unit_x, **self.styles) #Insere a unidade do eixo das Abscissas
        self.grafico.addLegend() #Coloca legenda no gráfico
        self.grafico.showGrid(x=True, y=True) #Coloca as grids no gráfico
        
        #Cria os objetos para plotar o gráfico
        self.dx_comm = PlotCurveItem(pen="#15bf48")
        self.dx_meas = PlotCurveItem(pen="#15bf48")
        
        #Plota no gráfico as duas séries temporais 
        self.plot(self.hour, self.temperature_1, "Comando de Controle","#15bf48")
        #self.plot(hour, temperature_1, "Comando de Controle", '#15bf48') #Dados do comando
        self.plot(self.hour, self.temperature_2, "Deflexão medida","#56fceb")
        #self.plot(hour, temperature_2, "Deflexão medida", '#56fceb') #Dados medidos

        self.formulario.addStretch()
        #Insere os widgets na widget da aba
        self.main_tab.addLayout(self.formulario,12) #Adiciona a aba os parâmetros 
        self.main_tab.addWidget(self.grafico,88) #Adiciona o gráfico a aba principal
        
        """
        Cria os widgets da segunda tab
        """
        self.db_table = QTableWidget() #Cria tabela do banco de dados
        #Itens abaixo da tabela
        self.btn_consulta = QPushButton("Consultar o Número de itens mais Atuais")
        self.btn_consulta.clicked.connect(self.consultar_db)
        self.n_itens = QLineEdit()
        self.n_itens.setPlaceholderText("N° Itens")
        self.status_itens = QLineEdit()
        self.status_itens.setPlaceholderText("Status do software:")
        self.status_itens.setDisabled(True)
        self.btn_pdate = QPushButton("Atualiza para os 1000 últimos dados registrados")
        self.btn_pdate.clicked.connect(self.update_table)
        self.btn_exp = QPushButton("Exportar tabela para Excel")
        self.btn_exp.clicked.connect(self.exp_excel)
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
        self.btn_pdate_rep = QPushButton("Atualiza para os 1000 últimos dados registrados")
        self.btn_pdate_rep.clicked.connect(self.update_rep)
        self.btn_exp_rep = QPushButton("Exportar relatório para Excel")
        self.btn_exp_rep.clicked.connect(self.exp_rep)
        self.pbar_db = QProgressBar()
        self.pbar_db.setFont(fonte)
        self.rep_func = QHBoxLayout() #Layout dos botões abaixo da tabela
        self.rep_func.addWidget(self.btn_pdate_rep)
        self.rep_func.addWidget(self.pbar_db)
        self.rep_func.addWidget(self.btn_exp_rep)
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
        self.tabs.addTab(self.tab1,"Simulação")
        self.tabs.addTab(self.tab2,"Banco de Dados")
        self.tabs.addTab(self.tab3,"Relatório de Falhas")
        self.tabs.addTab(self.tab4,"Informações sobre o TCC")
        
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
        global cur
        try:
            conn = mariadb.connect(
                user="root",
                password="lembrei",
                host="127.0.0.1",
                port=3306,
                database="db_tcc")
            cur = conn.cursor()
        except mariadb.Error as e:
            QMessageBox.warning(self,"Aviso",f"Sem conexão com o Banco de dados, devido ao erro: {e}")
    
        self.list_status.addItem("Conectado ao db_tcc")
    
    def bench(self):
        ask_dir = "Escolha o diretório onde o Benchmark se encontra"
        self.benchmark = str(QFileDialog.getExistingDirectory(None,ask_dir))
        self.list_status.clear() #Limpa a lista toda vez que o botão de benchmark é pressionado
        if self.benchmark != '': #Se não for vazio, continua
            arqs = os.listdir(self.benchmark)
            bench = []
            
            for arq in arqs:
                if '.slx' in arq: #Se a extenção do arquivo for a mesma do simulink
                    bench.append(arq)
            
            if not(bench): #Se o vetor estiver vazio
                not_bench = f"Não foi encontrado arquivo do simulink no diretório selecionado {self.benchmark}!"
                QMessageBox.warning(self,"Aviso!",not_bench)
            else:
                self.list_status.addItem(f"Diretório: {self.benchmark}")
                self.cmb_bench.addItems(bench)
                self.maria_conn()
                self.btn_start.setDisabled(False) #Habilita o botão para iniciar os testes
                for i in range(0,1000,1):
                    tic = datetime.now()
                    self.pbar.setValue(10)
                    self.temperature_1.append(randint(20,60))
                    self.temperature_2.append(randint(20,60))
                    self.hour.append(self.hour[-1]+1)
                    self.dx_comm(self.hour, self.temperature_1, "Comando de Controle","#15bf48")
                    self.ds_meas(self.hour, self.temperature_2, "Deflexão medida","#56fceb")
                    print(datetime.now()-tic)
    
    def start(self):

        #Treina os parâmetros
        simu = self.cmb_bench.currentText()
        system = self.benchmark+"/"+self.cmb_bench.currentText() #Caminho do sistema
        #monitora(system) #chama o simulink para emular o sistema
        quest = f"O sistema para emulação no Simulink é {system}?"
        if QMessageBox.question(self,"Tem certeza?",quest,QMessageBox.Yes|QMessageBox.No,
                                QMessageBox.No) == QMessageBox.Yes:
            metodo = self.cmb_treino.currentText() #Pega do combo o texto do modelo a treinar
            self.list_status.addItem(f"Treinando o modelo {simu} pelo método {metodo}")
            self.pbar.setValue(15)
            #Chama a classe do treino
            #sleep(.1) #Espera atualizar a tela antes de treinar 
            self.modelo = treina_modelo(metodo)
            self.pbar.setValue(25)
            self.list_status.addItem(f"Iniciando {system} no Simulink")
            #monitora(system) #Associa o monitoramento 
            
            plant = SimulinkPlant(modelName=system) #Carrega a classe na variável plant
            #Establishes a Connection
            plant.connectToMatlab()
            
            #Control Loop
            plant.simulate()
            
            #Closes Connection to MATLAB
            plant.disconnect()
            
            self.pbar.setValue(30)
            self.list_status.addItem(f"Emulando {system} no Simulink")

            QMessageBox.warning(self,"Aviso",f"O {system} será emulado")
        else:
            pass
    
    def consultar_db(self):
        pass
    
    def update_table(self):
        pass
        
    def exp_graph(self):
        """
        Essa função exporta o gráfico como está na tela em forma de imagem

        Returns
        -------
        None.

        """
        ask_dir = "Escolha o diretório onde o deseja salvar o gráfico" #string que pergunta o diretório
        save = str(QFileDialog.getExistingDirectory(None,ask_dir)) #Pede ao usuário o diretório onde ele quer salvar
        exporter = exporters.ImageExporter(self.grafico.plotItem) #Exporta o objeto do gráfico
        exporter.export(save+'/graph.png')  #Salva como png o gráfico da tela
    
    def exp_excel(self):
        """
        Essa função exporta os dados adquiridos para uma planilha do excel

        Returns
        -------
        Não retorna parâmetros, apenas executa a ação de exportar para uma planilha

        """
        salve = str(QFileDialog.getExistingDirectory(None, "Escolha o diretório onde quer salvar o relatório"))
        save = salve+"/Relatório_OFC_MFF.xlsx"
        self.df.to_excel(save,sheet_name="Relatório_OFC_MFF",index=False)
        info_save_excel = f"O relatório final das falhas de caráter oscilatória foi salvo em {save}!"
        QMessageBox.information(self,"Sucesso!",info_save_excel)

    def exp_rep(self):
        """
        Exporta um relatório em txt com os dados de falhas

        Returns
        -------
        None.

        """
        
        pass

    
    def update_rep(self):
        pass
    
    def pdate_ampl(self):
        if self.cmb_font.currentText() in ['sensor','cs_sensor']:
            self.lbl_ampl.setText("Ampl(mm)/Bias(mm)/Freq(rad/s):")
        else:
            self.lbl_ampl.setText("Ampl(mA)/Bias(mA)/Freq(rad/s):")
    
    def filed(self): #Abre o arquivo em forma de dicionário e retorna o caminho completo (posição 0)
        path = QFileDialog.getOpenFileName(self,"Abre um arquivo do excel","","All Files(*);;*xlsx *xls") 
        #file = open(path[0],'r')
        
        if (".xls" in path[0]): #Se for um arquivo do excel
            modelo = ExcelFile(path[0]).parse(0,skiprows=1)# Carrega o template em um Excel e a planilha
            self.relatorio.setModel(pandasModel(modelo))
            self.tab2.setDisabled(False)
            self.tab2.update()
            self.update()
        else: #Se não for...
            QMessageBox.warning(self,"Arquivo incorreto","Escolha um arquivo do Excel (.xlsx ou .xls)!")
     
    def salva(self): #Salva o dataset do relatório em um arquivo excel
        global temp, r_gerado
        if r_gerado:
            salve = str(QFileDialog.getExistingDirectory(None, "Escolha o diretório onde quer salvar o relatório"))
            save = salve+"/Relat_PCH_EQ_MFF.xlsx"
            temp.to_excel(save,sheet_name="Relatório_PCH",index=False)
            QMessageBox.information(self,"Sucesso!",f"O relatório final foi salvo em {save}!")
        else:
            QMessageBox.warning(self,"Erro!","O Pré-Relatório ainda não foi gerado, gere e tente novamente!")
    
    
class pandasModel(QAbstractTableModel):
    # Cria o modelo que converte do pandas ao PYQT5
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
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
        self.setWindowTitle(f"Interface do módulo de cálculo PCH {versao}")
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
        exp_report.setToolTip("Exporta o relatório em formato Excel")
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
            self.centro.close()
            self.close()
            exit
    
    #Aula 10 - Tool Bar
    def btns(self,btn): #Essa função encontra o botão da toolbox
        global centro
        if btn.text() == "Manual":
            try:
                os.startfile("docs\\manual_PCH.pptx")
            except:
                point = "É provável que você não tenha o MSPowerPoint Instalado!"
                QMessageBox.information(self,"Aviso",point)
                return
        elif btn.text() == "Abrir":
            mvp = "A versão MVP não contempla essa funcionalidade!"
            QMessageBox.information(self,"Aviso!",mvp)
        elif btn.text() == "Exp_Graph":
            self.centro.export_graph()
        elif btn.text() == "Exp_Excel":
            self.export_excel()
        elif btn.text() == "Exp_Report":
            self.export_report()
        elif btn.text() == "Salvar":
            self.centro.salva()
        elif btn.text() == "Sair":
            self.saindo()
        self.centro.update()
        self.update()
        

# Inicia a aplicação
def main():
    App = QApplication(sys.argv)
    App.setStyle('Fusion')
    window = Window()
    window.show()
    modern_style = str_style()
    App.setStyleSheet(modern_style)
    sys.exit(App.exec_())
    #sys.exit(appctxt.app.exec_())
    
if __name__ == '__main__':
    main()