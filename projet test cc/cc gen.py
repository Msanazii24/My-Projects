from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QMessageBox,QTableWidget,QTableWidgetItem
from pickle import *
import random
from random import *

e=dict(num=int,expm=int,expy=int,cvv=int)
ee=dict(num=int,expm=int,expy=int,cvv=int,nom=str,zipa=int,con=str)
def finale():
    i=0
    ft=open("client.dat","rb")
    eof=False
    while not eof :
        try:
            ee=load(ft)
            f.tb.setRowCount(i+1)
            f.tb.setItem(i,0,QTableWidgetItem(ee["num"]))
            f.tb.setItem(i,1,QTableWidgetItem(ee["expm"]))
            f.tb.setItem(i,2,QTableWidgetItem(ee["expy"]))
            f.tb.setItem(i,3,QTableWidgetItem(ee["cvv"]))
            f.tb.setItem(i,4,QTableWidgetItem(ee["zipa"]))
            f.tb.setItem(i,5,QTableWidgetItem(ee["name"]))
            f.tb.setItem(i,6,QTableWidgetItem(ee["con"]))
            i=i+1
        except:
            eof=True
    ft.close()
    
    
def generer():
    f1=open("cc.txt","ab")
    num= generate_test_number()
    expm=""
    x=randint(1,12)
    if x>=10:
        expm=expm+str(x)
    else:
        expm=expm+"0"+str(x)
    expy=str(randint(26,33))
    print("exp=",expm,"/",expy)
    cvv=""
    for i in range(3):
        cvv=cvv+str(randint(0,9))
    print("cvv=",cvv)
    cc=str(num)+"/"+expm+"/"+expy+"/"+cvv
    print("cc=",cc)
    e=dict()
    e["num"]=str(num)
    e["expm"]=expm
    e["expy"]=expy
    e["cvv"]=cvv
    print(e)
    dump(e,f1)
    f.lista.addItem(cc)
    f1.close()
    
    
    
    
    
def ajouter():
    tr=f.lista.currentItem()
    if tr is not None:
        value = tr.text()
        print("tr=",value)
        num=value[:value.find("/")]
        value=value[value.find("/")+1:]
        expm=value[:value.find("/")]
        value=value[value.find("/")+1:]
        expy=value[:value.find("/")]
        value=value[value.find("/")+1:]
        cvv=value
        name="guest"
        zipa="10080"
        con="USA"
    else:
        num=f.num.text()
        if not ( num =="" and num.isdecimal() and len(num) == 16 and num[0] == "4" or num[0] == "5"):
            QMessageBox.critical(f,"error","Num invalide")
            return False
        expm=f.expm.text()
        if not ( expm.isdecimal() and len(expm) == 2 and 1<=int(expm)<=12):
            QMessageBox.critical(f,"error","expm invalide")
            return False
        expy=f.expy.text()
        if not ( expy.isdecimal() and len(expy) == 2 and 26<=int(expy)<=33):
            QMessageBox.critical(f,"error","expy invalide")
            return False
        cvv=f.cvv.text()
        if not ( cvv.isdecimal() and len(cvv) == 3):
            QMessageBox.critical(f,"error","cvv invalide")
            return False
        name=f.name.text()
        if name=="":
            QMessageBox.critical(f,"error","add a name")
            return False
        zipa=f.zip.text()
        con=f.con.currentText()
        if con =="Choose ur country":
            QMessageBox.critical(f,"error","select a country")
            return False
    ft=open("client.dat","ab")
    ee=dict()
    ee["num"]=num
    ee["expm"]=expm
    ee["expy"]=expy
    ee["cvv"]=cvv
    ee["name"]=name
    ee["zipa"]=zipa
    ee["con"]=con
    dump(ee,ft)
    print(ee)
    QMessageBox.information(f,"OK","Client added!")
    f.res.setText("Client added!")
    ft.close()
    

import random

def generate_test_number(length=16):
    # first digit must be 4 or 5
    number = [random.choice([4, 5])]

    # fill remaining digits except last (check digit)
    while len(number) < (length - 1):
        number.append(random.randint(0, 9))

    # Luhn checksum calculation
    def luhn_checksum(digits):
        total = 0
        reverse = digits[::-1]
        for i, d in enumerate(reverse):
            if i % 2 == 0:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        return total

    checksum = luhn_checksum(number)
    check_digit = (10 - (checksum % 10)) % 10
    number.append(check_digit)

    return "".join(map(str, number))




app = QApplication([])
f = loadUi ("cc gen.ui")
f.show()
f.btfin.clicked.connect (finale)
f.btgen.clicked.connect (generer)
f.btadd.clicked.connect (ajouter)
app.exec_()