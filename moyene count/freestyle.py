from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QMessageBox,QTableWidget,QTableWidgetItem
from math import *
from numpy import array
from pickle import load,dump
e=dict(numins=str,moy=float,score=float)
e1=dict(cin=str,np=str,numins=str,passw=str,moy=float,score=float)
def analyse():
    f2=open("admin.dat","rb")
    eof=False
    i=0
    e1=dict()
    while not eof:
        try:
            f.tab.setRowCount(i+1)
            e1=load(f2)
            numins2=f.numins2.text()
            if numins2 == str(e1["numins"]):
                f.tab.setItem(i,0,QTableWidgetItem(str(e1["cin"])))
                f.tab.setItem(i,1,QTableWidgetItem(str(e1["np"])))
                f.tab.setItem(i,2,QTableWidgetItem(str(e1["numins"])))
                f.tab.setItem(i,3,QTableWidgetItem(str(e1["passw"])))
                f.tab.setItem(i,4,QTableWidgetItem(str(e1["moy"])))
                f.tab.setItem(i,5,QTableWidgetItem(str(e1["score"])))
                i=i+1
        except:
            eof=True
def afficher():
    f2=open("admin.dat","rb")
    numins2=f.numins2.text()
    eof=False
    i=0
    while not eof:
        try:
            e1=load(f2)
            numins=e1["numins"]
            f.list.addItem("cin="+str(e1["cin"])+"||"+"np="+str(e1["np"])+"||"+"numins="+str(e1["numins"])+"||"+"password="+str(e1["passw"])+"||"+"moy="+str(e1["moy"])+"||"+"score="+str(e1["score"]))
            
        except:
            eof=True
def calculer():
    if f.math.text() =="":
        math=f.math.setText("0.0")
    if f.phy.text() == "":
        phy=f.phy.setText("0.0")
    if f.prog.text() == "":
        prog=f.prog.setText("0.0")
    if f.sti.text() == "":
        sti=f.sti.setText("0.0")
    if f.franc.text() == "":
        franc=f.franc.setText("0.0")
    if f.arab.text() == "":
        arab=f.arab.setText("0.0")
    if f.eng.text() == "":
        eng=f.eng.setText("0.0")
    if f.philo.text() == "":
        philo=f.philo.setText("0.0")
    if f.option.text() == "":
        opt=f.option.setText("0.0")
    if (f.sport.text() == "" or f.check.isChecked() ):
        sport=f.sport.setText("0.0")
    
    
    math=float(f.math.text())
    phy=float(f.phy.text())
    prog=float(f.prog.text())
    sti=float(f.sti.text())
    franc=float(f.franc.text())
    arab=float(f.arab.text())
    eng=float(f.eng.text())
    philo=float(f.philo.text())
    opt=float(f.option.text())
    if (f.check.isChecked() ):
        sport=float(f.sport.text())
    else:
        sport=0.0
    if (math < 0.0 or math > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (phy < 0.0 or phy > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (prog < 0.0 or prog > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (sti < 0.0 or sti > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (franc < 0.0 or franc > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (arab < 0.0 or arab > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (eng < 0.0 or eng > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (philo < 0.0 or philo > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (sport < 0.0 or sport > 20.0):
        QMessageBox.critical(f,"error","check values")
    if (opt < 0.0 or opt > 20.0):
        QMessageBox.critical(f,"error","check values")
    if opt >= 10:
        moyenne = (
            prog*2 + sti*2 + math*4 + phy*3 +
            arab*2 + franc*2 + eng*2 +
            philo + sport + opt
        ) / 20
        score=moyenne*10+opt
    else:
        moyenne = (
            prog*2 + sti*2 + math*4 + phy*3 +
            arab*2 + franc*2 + eng*2 +
            philo + sport
        ) / 19
        score=moyenne*10+opt
    f.resnote.setText(str(moyenne))
    f.resscore.setText(str(score))
    f1=open("score.dat","ab")
    numins=f.numins.text()
    e=dict()
    if f.numins.text() =="":
        QMessageBox.critical(f,"attention","numero d'inscription est vide!")
    else:
        e["numins"]=numins
        e["moy"]=moyenne
        e["score"]=score
        print(e)
        dump(e,f1)
    

app = QApplication([])
f = loadUi ("note.ui")
f.show()
f.aff.clicked.connect (afficher)
f.cal.clicked.connect (calculer)
f.ana.clicked.connect (analyse)
app.exec_()