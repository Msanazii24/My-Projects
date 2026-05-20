from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QApplication,QMessageBox,QTableWidget,QTableWidgetItem
from PyQt5.QtCore import QTimer
from pickle import dump,load
e=dict(cin=str,np=str,numins=str,passw=str,moy=float,score=float)
e1=dict(numins=str,moy=float,score=float)
def tempp():
    if f.s > 0:
        f.temp.setText(str(f.s))
        f.s -= 1
        return "No"
    else:
        f.timer.stop()
        f.temp.setText("Done!")
        return "Done!"


def affnote():
    f1=open("score.dat","rb")
    cin=f.cin.text()
    np=f.np.text()
    numins=f.numins.text()
    passw=f.passw.text()
    if f.cin.text() == "":
        QMessageBox.critical(f,"error","cin invalide")
    if f.np.text() == "":
        QMessageBox.critical(f,"error","np invalide")
    if f.numins.text() == "":
        QMessageBox.critical(f,"error","numins invalide")
    if f.passw.text() == "":
        QMessageBox.critical(f,"error","passw invalide")
    e=dict()
    e1=dict()
    f2=open("admin.dat","ab")
    e["cin"]=cin
    e["np"]=np
    e["numins"]=numins
    e["passw"]=passw
    eof=False
    while not eof:
        try:
            e1=load(f1)
            numins1=e1["numins"]
            if numins1 == numins :
                if tempp() == "Done!":
                    moyenne=e1["moy"]
                    score=e1["score"]
                    e["moy"]=moyenne
                    e["score"]=score
                    f.res.setText(str(moyenne)+" Moyenne et"+" "+str(score)+" score")
                else:
                    f.res.setText("Veiller attender le temp pour ta resultat")
        except:
            eof=True
    dump(e,f2)
        
    
    


app = QApplication([])

f = loadUi("client.ui")


f.timer = QTimer()
f.timer.timeout.connect(tempp)
f.s = 30
f.timer.start(1000)
f.aff.clicked.connect(affnote)

f.show()
app.exec_()