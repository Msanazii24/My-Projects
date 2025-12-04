from numpy import array

t = array(["str"] * 30)

def transfer1():
    global t
    global n
    f = open("SMS.txt", "r")
    n = 0
    eof = False
    while not eof:
        ch = f.readline()
        ch = ch.strip()  
        if ch == "":
            eof = True
        else:
            t[n] = ch
            n += 1
    f.close()

def transfer2(t, n):
    f = open("SMS.txt", "w")
    for i in range(n):
        if "F" in t[i] and "A" in t[i] and "B" in t[i] and "C" in t[i]:
            f.write(t[i] + "\n")  
    f.close()

def gagnant():
    f = open("SMS.txt", "r")    
    f2 = open("gagnant.txt", "w") 
    eof = False
    while not eof:
        ch = f.readline()
        if ch == "":
            eof = True
        elif "FCBA" in ch:
            f2.write(ch)  
    f.close()
    f2.close()


transfer1()
transfer2(t, n)
gagnant()
