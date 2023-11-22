from flask import Flask, render_template, request , session ,abort,redirect
import datetime
import time
import sqlite3
from barcode import EAN13
import pdfkit
import requests
import webbrowser 
config = pdfkit.configuration(wkhtmltopdf="C:\\Users\\hny44\OneDrive\\桌面\\itb\\206\\CW\\env\\wkhtmltox\\bin\\wkhtmltopdf.exe")
app =   Flask(__name__)
app.secret_key = 'any random string'
conn = sqlite3.connect('C:/Users/hny44/OneDrive/桌面/itb/206/CW/206CW',check_same_thread=False)
cur = conn.cursor()
#open database connection
@app.route('/home')
def home():
    if session['username'] == 'admin':
        return render_template("admin.html")
    elif session['username'] == ' ':
        return redirect('/') 
    else:
        return render_template("index.html",guest=session['username'])
@app.route('/enter', methods=["POST","GET"])        
def check():
    if request.method == "POST":
        username = request.form['username']
        pwd = request.form['password']
        custName = " "
        # prepare a cursor object using cursor() method
        sql = ("SELECT username , pwd FROM Userlog WHERE username = '"+username+"' AND pwd = '"+pwd+"'")
        cur.execute(sql)
        try:
            results = cur.fetchall()
            for row in results:
                custName = row[0]
        except Exception as e:
            cur.rollback()
        if custName == ' ':
            abort(400,'Incorrect usename or password')
            return render_template("login.html")
        elif custName == 'admin':
            session['username'] =  custName
            return render_template("admin.html",guest = session['username'])
        else:
            session['username'] = custName
            return render_template("index.html",guest = session['username'])
@app.route('/')
def login():
        session['username'] = ' '
        return render_template('login.html')
@app.route('/search')
def search():
    if session['username'] == 'admin':
        return render_template('search.html')

    else:
        return redirect('/')
@app.route('/getdate',methods=["POST","GET"])
def getdate():
    if request.method == "POST":
        session['key'] = ''
        session['date'] = ''
        keytype = request.form['keyType']
        if keytype == "acc_id":
            key = request.form['Acc']
            sql = "select Acc_No from Acc_inf where Acc_No = '"+ key +"'"
            cur.execute(sql)
            result = cur.fetchall() 
            for d in result:
                session['key'] = d[0]
        elif keytype == "company_name":
            key = request.form['name']
            sql = "select Acc_No from Acc_inf where comany = '"+ key +"'"
            cur.execute(sql)
            result = cur.fetchall() 
            for d in result:
                session['key'] = d[0]
        if session['key'] == '':
            return render_template('search.html',msg ="incorrect input")
        else :
            sql = "select Due from bill"
            cur.execute(sql)
            datelist = cur.fetchall()
            return render_template('result.html',datelist = datelist)
@app.route('/result',methods=["POST","GET"])
def result():
    if request.method == "POST":
        session['date'] = request.form['date']
        webbrowser.open_new_tab('http://localhost:8000/run')
        return redirect('/search')
@app.route('/run')
def run():
    return redirect('/bill')
@app.route('/singin')
def newAcc():
    if session['username'] == 'admin':
        return render_template('singin.html')
    else:
        return redirect('/')
@app.route('/newAcc',methods=["POST","GET"])
def addAcc():
    if request.method == "POST":
        sql = "select Acc_No from Acc_inf  order by Acc_No desc limit 1"
        cur.execute(sql)
        result = cur.fetchall()
        for a in result:
            Acc_No = a[0]
        Acc_No = str(int(Acc_No) +1)
        company = request.form['name']
        Address = request.form['address']
        Meter = request.form['meter']
        sql = "insert into Acc_inf values('"+str(Acc_No)+"','"+company+"','"+Address+"')"
        cur.execute(sql)
        sql = "insert into Meter values('"+Meter+"','"+Acc_No+"')"
        cur.execute(sql)
        sql = "insert into Userlog values('"+Acc_No+"','')"
        return render_template("Accadded.html",Acc_No=Acc_No)
@app.route('/addmeter')
def addmeter():
    if session['username'] == 'admin':
        Acclist =[]
        sql = "select Acc_No from Meter group by Acc_No"
        cur.execute(sql)
        result = cur.fetchall()
        for m in result:        
            Acclist.append(m[0])
        return render_template('addmeter.html',Acclist=Acclist)
    else:
        return redirect('/')
@app.route('/meter',methods=["POST","GET"])
def newmeter():
    if request.method == "POST":
        Acc = request.form['Acc']
        sql = "select Acc_No from Meter group by Acc_No"
        cur.execute(sql)
        result = cur.fetchall()
        for m in result:  
            if Acc == m[0]:
                Acc_No = Acc      
        Meter = request.form['meter']
        sql = "insert into Meter values('"+Meter+"','"+Acc_No+"')"
        cur.execute(sql)
        sql = "select Acc_No from Meter"
        cur.execute(sql)
        result = cur.fetchall()
        num =0
        for i in result:
            num = num +1
        return render_template("Accadded.html",Acc_No=Acc_No,num=num)
@app.route('/record')  
def record():
    if session['username'] == 'admin':
        Mlist =[]
        sql = "select Meter_num from Meter"
        cur.execute(sql)
        result = cur.fetchall()
        for m in result:        
            Mlist.append(m[0])
        return render_template('record.html',Mlist=Mlist)
    else:
        return redirect('/')
@app.route('/reading',methods=["POST","GET"])
def read():
    if request.method == "POST":
        Meter = request.form['Meter']
        recd = request.form['recd']
        reading = request.form['reading']
        pay = request.form['pay']    
        sql = "select Reading,recDate from record where Meter_num = '"+ Meter +"' And recdate < '"+recd+"'order by recDate desc limit 1"
        cur.execute(sql)
        d = cur.fetchall()    
        for row in d:
            if float(reading) < float(row[0]):
                er = "uncorrect reading or meter"
                return render_template('pass.html',msg=er) 
            else:
                old = row[1]   
        sql = "Insert into record values('"+Meter+"','"+recd+"',"+reading+")"
        cur.execute(sql)
        sql = "select Acc_No from Meter where Meter_num='"+Meter+"'"
        cur.execute(sql)
        results = cur.fetchall()
        for row in results:
            acc = row[0]    
        
        sql = "select Due from bill where Acc_No ='"+acc+"'order by Due desc limit 1"
        cur.execute(sql)
        for row in results:
            last = row[0] 
        if last == recd:
            pass
        else:
            sql = "Insert into bill values('"+recd+"',' ','"+acc+"','"+pay+"','"+old+"',' ' )"
            cur.execute(sql)
        return render_template('pass.html',msg="finish insert")
@app.route('/datebill')
def datebill():
    if session['username'] == 'admin':
        return render_template('datebill.html')
    else:
        return redirect('/')
@app.route('/getAcc',methods=["POST","GET"])
def getacc():
    if request.method == "POST":
        session['key'] = ''
        session['date'] = ''
        Bdate = request.form['date']
        Acclist = []
        sql = 'select Acc_No from bill where Due = "'+Bdate+'"'
        cur.execute(sql)
        result = cur.fetchall()
        for row in result:
            Acclist.append(row[0])
        if Acclist == []:
            return render_template('pass.html',msg='No bill this date')    
        else:
            session['date'] = Bdate
            return render_template('result2.html',Acclist=Acclist)
@app.route('/result2',methods=["POST","GET"])
def result2():
    if request.method == "POST":
        Acc = request.form['Acc']
        sql = 'select Acc_No from bill where Due = "'+session['date']+'"And Acc_No ="'+Acc+'"'
        cur.execute(sql)
        result = cur.fetchall()
        if result == []:
            return render_template('pass.html',msg = 'can not find the required bill, incorrest Acc_No or date')
        else:
            for row in result:
                session['key'] = row[0]
            webbrowser.open_new_tab('http://localhost:8000/run')
            return redirect('/datebill')

@app.route('/update')
def update():
    if session['username'] == 'admin':
        Acclist = []
        comany = []
        address = []
        Accinf = []
        sql = 'select * from Acc_inf'
        cur.execute(sql)
        result = cur.fetchall()
        i = 0 
        for row in result:
            Acclist.append(row[0])
            comany.append(row[1])
            address.append(row[2])
            Accinf.append((Acclist[i],comany[i],address[i]))
            i = i + 1
        sql = 'select * from Meter'
        cur.execute(sql)
        result = cur.fetchall()
        Meter =[]
        MAc = []
        Meterlist = []
        i = 0 
        for row in result:
            Meter.append(row[0])
            MAc.append(row[1])
            Meterlist.append((Meter[i],MAc[i]))
            i = i+1
        recM =[]
        rec =[]
        reading = []
        readlist = []
        i = 0 
        sql = 'select * from record'
        cur.execute(sql)
        result = cur.fetchall()
        for row in result:
            recM.append(row[0])
            rec.append(row[1])
            reading.append(row[2])
            readlist.append((recM[i],rec[i],reading[i]))
            i = i+1
            
        return render_template('update.html',Acclist=Acclist,Accinf=Accinf,Meterlist=Meterlist,Meter=Meter,readlist=readlist)
    else:
        return redirect('/')
@app.route('/insert',methods=["POST","GET"])
def insert():
    if request.method == "POST":
        keytype = request.form['keyType']
        if keytype == "acc_inf":
            Acc = request.form['Acc']
            sql = 'select Acc_No from Acc_inf where Acc_No ="'+Acc+'"'
            cur.execute(sql)
            result = cur.fetchall()
            for row in result:
                Acc = row[0]
            if Acc == '':
                return render_template("pass.html",msg = 'incorrect input')
            else:
                acckey = request.form['accType']
                if acckey == "company":
                    company = request.form['companyName']
                    if company == '':
                        return render_template("pass.html",msg = 'incorrect input')
                    else:
                        sql = 'update Acc_inf set comany ="'+ company + '" where Acc_No ="'+Acc+'"'
                        cur.execute(sql)
                elif acckey == "address":
                    address =request.form['addressname']
                    if address == '':
                        return render_template("pass.html",msg = 'incorrect input')
                    else:
                        sql = 'update Acc_inf set Address ="'+ address + '" where Acc_No ="'+Acc+'"'
                        cur.execute(sql)
                else:
                    return render_template("pass.html",msg = 'incorrect input')
                Accinf = []
                sql = 'select * from Acc_inf where Acc_No ="'+Acc+'"'
                cur.execute(sql)
                result = cur.fetchall()
                for row in result:
                    Acclist = row[0]
                    comany = row[1]
                    address = row[2]
                    Accinf.append((Acclist,comany,address))
                msg = Accinf
        elif keytype == "reading":
            Meter = request.form['Meter']
            recDate = request.form['date']
            reading = request.form['reading']
            sql = 'update record set reading ="'+ reading + '" where Meter_num ="'+Meter+'"And recDate ="'+recDate+'"'
            cur.execute(sql)
            sql = 'select * from record Where Meter_num ="'+Meter+'"And recDate ="'+recDate+'"'
            cur.execute(sql)
            result = cur.fetchall()
            if result == []:
                return render_template("pass.html",msg = 'incorrect input')
            else:
                for row in result:
                    recM = row[0]
                    rec = row[1]
                    reading = row[2]
                    readlist = recM+","+rec+","+str(reading)
            msg = readlist
        elif keytype == "payment":
            feetype = request.form['feetype']
            fee = request.form['free']
            if feetype =="":
                return render_template("pass.html",msg = 'incorrect input')
            elif fee == "":
                return render_template("pass.html",msg = 'incorrect input')
            else:
                x = datetime.datetime.now()
                y =str(x.strftime("%Y-%m-%d"))
                sql = 'Insert into payment values("'+feetype+'",'+fee+',"'+x.strftime('%Y-%m-%d')+'")'
                cur.execute(sql)
                sql = 'select * from payment order by Date_update'
                cur.execute(sql)
                result = cur.fetchall()
            msg = result
    return render_template('finish.html',msg=msg)
@app.route('/ontime')
def ontime():
    if session['username'] == 'admin':
        sql="select Acc_No from bill Where ontime=''"
        cur.execute(sql)
        onlist=[]
        result = cur.fetchall()
        for row in result:
            onlist.append(row[0])
        return render_template('ontime.html',onlist = onlist)
    else:
        return redirect('/')
@app.route('/on',methods=["POST","GET"])
def on():
    if request.method == "POST":
            Acc = request.form['Acc']
            Due = request.form['date']
            sql = 'select Acc_No from bill where Acc_No ="'+Acc+'"And Due = "'+Due+'"'
            cur.execute(sql)
            result = cur.fetchall()
            for row in result:
                Acc = row[0]
            if Acc == '':
                return render_template("pass.html",msg = 'incorrect input')
            else:
                ont = request.form['ont']
                if ont == '':
                    return render_template("pass.html",msg = 'incorrect input')
                elif ont =='yes':
                    sql = 'update bill set ontime = "yes" where Acc_No ="'+Acc+'"And Due = "'+Due+'"'
                    cur.execute(sql)
                    return render_template("pass.html",msg = 'insert finish')
                else:
                    sql = 'update bill set ontime = "no" where Acc_No ="'+Acc+'"And Due = "'+Due+'"'
                    cur.execute(sql)
                    return render_template("pass.html",msg = 'insert finish')

@app.route('/bill')
def bill():      
    key = session['key'] 
    date = session['date']
    sql = "select * from Acc_inf where Acc_No = '"+ key +"'"
    cur.execute(sql)
    results = cur.fetchall()
    for row in results:
        comany = row[1]
        Address = row[2]
    sql = "select Meter_num from Meter where Acc_No = '"+ key +"'"
    cur.execute(sql)
    Meter = cur.fetchall()
    i = 0
    persent = []
    last = []
    MeterNum = []
    odate = date

    sql = "select since from bill where Due='"+date+"'"
    cur.execute(sql)
    result = cur.fetchall()
    for d in result:
        odate = d[0]
    sql = "select JULIANDAY(Due) - JULIANDAY(since) AS difference  from bill where Due = '"+date+"'" 
    cur.execute(sql)
    result = cur.fetchall()
    for d in result:
        betw = d[0]

    sql = "select pay from bill where Due = '"+date+"' limit 1" 
    cur.execute(sql)
    result = cur.fetchall()
    for v in result:
        dued = v[0]
    
    for item in Meter:
        MeterNum.append(item[0])
        sql ="select Reading from record where Meter_num = '"+ item[0] +"' order by recDate desc limit 2;"
        cur.execute(sql)
        read = cur.fetchall()
        for item in read:
            if len(persent) == i:
                persent.extend(item)
            else:
                last.extend(item)
        i = i+1
    sql = "select ontime from bill where Due = '"+odate+"'And Acc_NO='"+key+"'"
    cur.execute(sql)  
    result = cur.fetchall()
    surcharge = 0
    for row in result:
        if row[0] == 'no':
            sql = "select a.total * b.Free from bill a, payment b  where a.Due = '"+odate+"' and b.Free_type = 'surcharge' and b.Date_update >= '"+odate+"' order by b.Date_update desc limit 1"
            cur.execute(sql)
            Free = cur.fetchall() 
            for m in Free:
                surcharge = float(m[0])
    sql = "select Free from payment where Free_type = 'Fuel'  and Date_update <= '"+date+"' order by Date_update desc limit 1"
    cur.execute(sql)
    Free = cur.fetchall()
    for m in Free:
        Fuel = m[0]
    records =[]
    j = 0
    total = float(surcharge)
    for z in range(len(persent)):
        use = int(persent[j]) - int(last[j])
        fee = int(use)*float(Fuel)
        total = float(total) + float(fee)
        records.append(("("+str(j+1)+")"+str(MeterNum[j]),str(persent[j]),str(last[j]),use,'',fee))
        j = j+1
    total = round(total,1)
    number = '11'+key+date+str(total)
    sql = "update bill set total = '"+str(total)+"'where Acc_No = '"+key+"' and Due = '"+ date+"'"
    cur.execute(sql)  
    my_code = EAN13(number)
    my_code.save('./static/image/code')        
    session['key'] = ""
    session['date'] = ""
    return render_template('bill.html',total= total,due= dued,Fuel=round(Fuel*100,1),Comany = comany,address =Address,Acc_No = key,Bill_date=date,records =records,lastD=odate, betw=betw , surcharge=surcharge, my_code=my_code)
@app.route('/newuser')
def newuser():
    return render_template('register.html')
@app.route('/register', methods =['GET', 'POST'])
def register():
    if request.method == 'POST':  
        username = request.form['username']
        sql="select username from Userlog where username='"+username+"'"
        cur.execute(sql)
        result = cur.fetchall()
        for row in result:
            if row[0] == '':
                return render_template('register.html')
            else:
                pd = request.form['password']
                sql = "update Userlog set pwd = '"+pd+"'where username = '"+username+"'"
                cur.execute(sql)         
                session['username'] = str(username)
                return render_template("index.html",guest = username)
@app.route('/accbill')
def accbill():
    acc = str(session['username'])
    sql = "select Due from bill where Acc_No = '"+acc+"'order by Due desc limit 1 "
    cur.execute(sql)
    result = cur.fetchall()
    for row in result:
        session['date'] = row[0]
    session['key']= acc
    webbrowser.open_new_tab('http://localhost:8000/run')
    return redirect('/home')

@app.route('/accupdate')
def accupdate():
    return render_template("accup.html")
@app.route('/accchange', methods =['GET', 'POST'])
def accchange():
    if request.method == 'POST': 
        Acc = str(session['username'])
        acckey = request.form['accType']
        if acckey == "company":
            company = request.form['companyName']
            if company == '':
                return render_template("pass.html",msg = 'incorrect input')
            else:
                sql = 'update Acc_inf set comany ="'+ company + '" where Acc_No ="'+Acc+'"'
                cur.execute(sql)
        elif acckey == "address":
            address =request.form['addressname']
            if address == '':
                return render_template("pass.html",msg = 'incorrect input')
            else:
                sql = 'update Acc_inf set Address ="'+ address + '" where Acc_No ="'+Acc+'"'
                cur.execute(sql)
        elif acckey == "pwd":
            opd = request.form['opwd']
            npd = request.form['npwd']
            if npd == '':
                return render_template("pass.html",msg = 'incorrect input')
            sql = "select pwd from Userlog where username ='"+Acc+"'and pwd = '"+opd+"'"
            cur.execute(sql)
            result = cur.fetchall()
            if result == []:
                return render_template("pass.html",msg = 'incorrect input')
            else:
                sql = "update Userlog set pwd = '"+npd+"'where username = '"+Acc+"'"
                cur.execute(sql)
                return render_template("pass.html",msg = 'password changed')        
        else:
            return render_template("pass.html",msg = 'incorrect input')
if __name__=='__main__':
    app.debug   =   True
    app.run(host="0.0.0.0",port=8000)
