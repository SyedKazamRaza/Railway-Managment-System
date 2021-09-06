import smtplib
from operator import itemgetter
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, json, session, redirect, url_for
from DBHandler import DBHandler
from authlib.integrations.flask_client import OAuth
import json
import stripe

HOST = 'localhost'
USER = 'root'
PWD = ''
DBNAME = 'railway'
YOUR_DOMAIN = 'http://pakrailway.tech'

dbObj = DBHandler(HOST, USER, PWD, DBNAME)


app = Flask(__name__)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id="956018769459-v7vhg7aod95g1m18785a2eefnrvdvrbc.apps.googleusercontent.com",
    client_secret="S7n8MSmX93eHnOIqtg8ppik_",
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    # This is only needed if using openId to fetch user info
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)
app.secret_key = "jf3j98j4jfowijf98"
stripe.api_key = 'sk_test_51I1U9bLxCWtLRhQtx7wtMLdfyPb2N1jCYshldNsibfJdoO3xZQ7PKhep2pJGPtmtg5ysDcPfGd8CV6XMxazRc4OB00iBlfF2kJ'


@app.route('/')
def Home():
    session["sid"] = ""
    session["method"] = ""
    session["not"] = ""

    res = dbObj.getStations()
    return render_template("index.html", sched=json.dumps(res))


@app.route('/admin')
def adminPanel():
    if session.get("admin") is not None:
        res = dbObj.getStations()
        emp = dbObj.getEmps()
        pie = dbObj.getDataForPieChart()
        lineChart = dbObj.getDataForLineChart()
        lineGraph = []
        for d in lineChart.keys():
            lineGraph.append({"date": d, "quant": lineChart[d]})
        res.sort(key=itemgetter('TrainName'))
        return render_template("showDetailsToAdmin.html", res=res, emp=emp, lineGraph=lineGraph, pie=pie)
    else:
        return render_template("adminlogin.html")

@app.route('/changePass',methods=["POST"])
def changePass():
    passw = request.get_json(force=True)
    passw["authId"]= session["auth"]["authID"]
    if dbObj.changePass(passw):
        return ""
    return "notMatch"


@app.route('/editSchedTrain', methods=["POST", "GET"])
def editSchedTrain():
    if (request.args.get("schedid") != None or request.method == 'POST'):

        if (request.method == "GET"):
            sid = request.args.get("schedid")
            sched = dbObj.getSingleSched(sid)
            passengers = dbObj.getPassengers(sid)
            employees = dbObj.getEmployees(sid)
            employeeTrain = dbObj.getEmployeesToAdd(sid)
            return render_template("editSchedTrain.html", employeeTrain=employeeTrain, sched=sched,
                                   passengers=passengers, employees=employees)
        else:
            sid = request.form.get("schedId")
            dbObj.editSched(request.form)
            return redirect(url_for("editSchedTrain") + '?schedid=' + str(sid))
    else:
        return redirect('/admin')


@app.route('/deleteEmpFromTrain')
def deleteEmpFromTrain():
    sid = request.args.get("sid")
    eid = request.args.get("eid")

    dbObj.deleteEmpSched(eid, sid)

    return redirect(url_for("editSchedTrain") + '?schedid=' + str(sid))


@app.route('/addEmpToTrain', methods=["POST", "GET"])
def addEmpToTrain():
    if request.method == "POST":
        sid = request.form.get("schedId")
        empTrain = request.form.get("empTrain")
        eid = empTrain[0:empTrain.find(' ')]

        dbObj.addEmployToSched(eid, sid)
        return redirect(url_for("editSchedTrain") + '?schedid=' + str(sid))
    else:
        return redirect('/admin')


@app.route('/addTrain', methods=["POST"])
def addTrain():

    if dbObj.addTrain(request.get_json(force=True)["trainName"]):
        return "added"
    return "already"


@app.route('/addEmployee', methods=["POST"])
def addEmployee():

    res = dbObj.addEmployee(request.get_json(force=True))
    if res == False:
        return "already"
    return json.dumps(res)


@app.route('/addSched', methods=["POST"])
def addSched():

    if dbObj.addSched(request.get_json(force=True)):
        return "added"
    return "already"


@app.route('/login',methods=['POST', 'GET'])
def login():

    pw = ""
    if request.method == "POST":
        user = request.form['user']
        pw = request.form['pw']
        auth = dbObj.getAuth(user, pw)

        if auth != None:
            session.permanent = True
            session['auth'] = auth
            if auth['role'] == 'P':
                psnger = dbObj.getPassenger(auth['authID'])
                session['pid'] = psnger['PID']
                if session.get("not") != None and session.get("not") != "":
                    return redirect(url_for('bookTicket'))
                return redirect(url_for('dashboard'))
            elif auth['role'] == 'A' or auth['role'] == 'a':
                session["admin"] = auth['username']
                return redirect(url_for("adminPanel"))
            else:
                return redirect(url_for('employee'))
    else:
        if 'auth' in session:
            auth = session['auth']
            if auth != None:
                if auth['role'] == 'P':
                    psnger = dbObj.getPassenger(auth['authID'])
                    session['pid'] = psnger['PID']
                    if session.get("not") != None and session.get("not") != "":
                        return redirect(url_for('bookTicket'))
                    return redirect(url_for('dashboard'))
                elif auth['role'] == 'A' or auth['role'] == 'a':
                    session["admin"] = auth['username']
                    return redirect(url_for("adminPanel"))
                else:
                    return redirect(url_for('employee'))
    if pw == "":
        return render_template("login.html", msg="")
    else:
        pw = ""
        return render_template("login.html", msg="error")


@app.route('/signUp', methods=['POST', 'GET'])
def signup():
    if 'auth' in session:
        return redirect(url_for("login"))
    p = {}
    passenger = {}
    values = {}

    values['username'] = ""
    values['fname'] = ""
    values['lname'] = ""
    values['cnic'] = ""
    values['ph'] = ""
    values['pw'] = ""
    values['conPass'] = ""

    if request.method == "POST":
        user = request.form['user']
        pw = request.form['pw']
        conPass = request.form['conPass']
        if pw != conPass:
            err = "Password do not match"
            return render_template("signup.html", values=values, err=err)
        else:
            p['username'] = user
            p['password'] = pw
            p['role'] = "P"

            if dbObj.setAuth(p):

                passenger['fname'] = request.form['fname']
                passenger['lname'] = request.form['lname']
                passenger['cnic'] = request.form['cnic']
                passenger['ph'] = request.form['ph']

                authID = dbObj.getAuthId(user)
                passenger['authID'] = authID['authID']

                if dbObj.setPassenger(passenger):
                    auth = dbObj.getAuth(user, pw)
                    if auth != None:
                        session.permanent = True
                        session['auth'] = auth
                        return redirect(url_for('login'))

    elif "oauth" in session:
        person = session['oauth']

        values['username'] = person['user']
        values['fname'] = person['fname']
        values['lname'] = person['lname']
        values['pw'] = person['pw']
        values['conPass'] = person['pw']

        return render_template("signup.html", values=values)

    return render_template("signup.html", values=values)


@app.route("/updatePassProfile", methods=['POST', 'GET'])
def updatePassProfile():
    user = {}
    if request.method == "POST":
        user['fname'] = request.form['fname']
        user['lname'] = request.form['lname']
        user['cnic'] = request.form['cnic']
        user['phone'] = request.form['ph']
        psnger = session['psnger']
        user['authID'] = psnger['authID']
        user['PID'] = psnger['PID']
        dbObj.updatePassenger(user)

    return redirect(url_for('dashboard'))

@app.route('/createAccount', methods=["POST"])
def CreateNewAccount():
    abc = json.loads(request.data)
    username = abc["username"]
    firstName = abc["first"]
    lastName = abc["last"]
    CNICno = abc["CNIC"]
    PhoneNumber = abc["PhoneNumber"]
    password = abc["pass"]

    result = dbObj.insertRecord(
        username, firstName, lastName, CNICno, PhoneNumber, password)
    if result == False:
        return "False"
    else:
        session["pid"] = result
        return "True"


@app.route('/ticketDetail')
def ticketDetail():
    psnger = ''
    if request.args:
        if 'tkid' in request.args:
            tkid = int(request.args.get('tkid'))

            tks = dbObj.getSingleTicket(tkid)

            tmp = dbObj.getSchedule(tks['ScheduleID'])
            psnger = dbObj.getPassenger(session.get('auth').get('authID'))
            for k, v in tmp.items():
                tks[k] = v

            tmp = dbObj.getTrain(tks['TrainID'])
            for k, v in tmp.items():
                tks[k] = v

    tks["eLocLat"] = 24.8607
    tks["eLocLong"] = 67.0011
    tks["sLocLat"] = 31.5305
    tks["sLocLong"] = 74.3613
    if(tks["busOrEco"] == "B"):
        tks["Fare"] = tks["Fare"]*.20 + tks["Fare"]
    tks["Fare"] = tks["Fare"]*tks["numoftick"]
    return render_template("ticketDetail.html", pDetail=psnger, tks=tks)


@app.route('/employee')
def employee():
    data = ""
    check = False

    if 'auth' in session:
        auth = session['auth']

        emp = dbObj.getEmployee(auth['authID'])
        if auth != None and emp != None:
            session['empid'] = emp['empid']

            data = dbObj.employeeTrains(emp['empid'])
            if data == "No Train Alloted":
                check = False
            else:
                check = True
        print(data)
        return render_template("employeeMenu.html", empData=data, check=check)

    return redirect(url_for('login'))


@app.route('/employeeMenu')
def employeeMenu():
    session["empID"] = 11
    if session.get("empID") != None:

        data = dbObj.employeeTrains(session.get("empID"))
        if data == "No Train Alloted":
            check = False
        else:
            check = True
        return render_template("employeeMenu.html", empData=data, check=check)
    else:
        return redirect(url_for('showLogin'))


@app.route('/googleLogin')
def googleLogin():
    redirect_uri = url_for('authorize', _external=True)
    google = oauth.create_client('google')
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    passenger = {}

    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    user = oauth.google.userinfo()
    auth = dbObj.getAuth(user['email'], user['sub'])
    if auth == None:
        passenger['user'] = user['email']
        passenger['pw'] = user['sub']
        passenger['fname'] = user['given_name']
        passenger['lname'] = user['family_name']
        session['oauth'] = passenger
        return redirect(url_for('signup'))
    else:
        session.permanent = True
        session['auth'] = auth
        return redirect(url_for('login'))


@app.route("/sendMailTicket", methods=["POST"])
def sendMailTicket():
    try:
        ticketDetailsJson = request.get_json(force=True)
        receiverEmail = ticketDetailsJson["email"]
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        subject = "Your Ticket from " + \
            ticketDetailsJson["From"] + " to " + ticketDetailsJson["To"]
        body = "Here's you ticket Details: \n Train Name: {} \n From: {} \n To: {} \n Time: {} \n Number of Tickets: {} \n Method: {} \n Total Dues: {} \n Class: {} \n Payable: {}".format(
            ticketDetailsJson["Train"], ticketDetailsJson["From"], ticketDetailsJson["To"], ticketDetailsJson["Time"],
            ticketDetailsJson["NumOfTick"], ticketDetailsJson["Method"], ticketDetailsJson["fee"],
            ticketDetailsJson["busOrEco"],
            ticketDetailsJson["RemainingP"])
        myEmail = "sharjeelabbas014@gmail.com"
        s.login("sharjeelabbas014@gmail.com", "tkpvyteorhiqacod")
        message = """From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (myEmail, ", ".join(receiverEmail), subject, body)
        s.sendmail(myEmail, receiverEmail, message)
        s.quit()
        return "sent"
    except Exception as e:
        print(str(e))
        return ""


@app.route('/dashboard')
def dashboard():

    if 'auth' in session:
        auth = session['auth']

        psnger = dbObj.getPassenger(auth['authID'])

        if auth != None and psnger != None:
            session['pid'] = psnger['PID']
            for k, v in auth.items():
                psnger[k] = v

            tks = dbObj.getTickets(psnger['PID'])
            if len(tks) > 0:
                for t in tks:
                    tmp = dbObj.getSchedule(t['ScheduleID'])
                    for k, v in tmp.items():
                        t[k] = v
                i = 1
                for t in tks:

                    t['no'] = i
                    i += 1
                    tmp = dbObj.getTrain(t['TrainID'])
                    for k, v in tmp.items():
                        t[k] = v
                    t['class'] = ""
                tks[0]['class'] = "active"
            session['psnger'] = psnger
            res = dbObj.getStations()
            return render_template("dashboard.html", psnger=psnger, tks=tks,sched=json.dumps(res))

    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('auth', None)
    session.clear()
    return redirect(url_for('login'))




@app.route('/showAllPassengers', methods=["POST"])
def showPassengers():
    SID = json.loads(request.data)
    session["scheduleID"] = SID
    return render_template("passengersToEmp.html")


@app.route('/showPassengersToEmp')
def showPassengersToEmp():
    SID = session["scheduleID"]

    res = dbObj.PasssengersWithCash(SID)
    if res == "No":
        check = False
    else:
        check = True
    return render_template("passengersToEmp.html", data=res, check=check)


@app.route('/traindetails')
def trainDetails():
    session["sid"] = ""
    session["method"] = ""
    session["not"] = ""

    res = dbObj.getStations()
    return render_template("trainDetails.html", sched=json.dumps(res))


ticketDetails = ""


@app.route('/paymentSelection', methods=["POST", "GET"])
def bookTicket():
    global ticketDetails
    print(session)
    if session.get('auth') != None and (session.get('auth').get("role") == "E" or session.get('auth').get("role") == "A"):
        session.clear()
    if request.method == "POST":
        ticketDetails = request.get_json(force=True)
        session["sid"] = ticketDetails["sid"]
        session["not"] = ticketDetails["numOfTickets"]
        session["busOrEco"] = ticketDetails["busOrEco"]
        det = ticketDetails["others"]
        if (session["busOrEco"] == "bus"):
            num = det[-4:]
            final = ""
            if num[0] == ":":
                final = det[0:-4]
                num = det[-3:]
                num = int(int(int(num) * 0.2) + int(num))
                final = final + " " + str(num)
            else:
                if num[0] == " ":
                    final = det[0:-5]
                    num = int(int(int(num) * 0.2) + int(num))
                    final = final + " " + str(num)
                else:
                    final = det[0:-5]
                    num = int(int(int(num) * 0.2) + int(num))
                    final = final + " " + str(num)
            ticketDetails["others"] = final
        print(ticketDetails["others"])
        if dbObj.checkTicket(session["busOrEco"],session["not"],session["sid"]) == True:
            if session.get("pid") is not None:
                return "GOTIT"
            return "LOGIN"
        else:
            return "Error"
    else:
        if session.get("not") != None and session.get('not') != "":
            return render_template("paymentSelection.html")
        else:
            return redirect(url_for('Home'))



@app.route('/paywithmastercard')
def paywithmastercard():
    session["method"] = "Card"
    return render_template("paywithmastercard.html", ticketDetails=ticketDetails)


@app.route('/paywithjazzcash')
def paywithjazzcash():
    d = datetime.today()
    d = d + timedelta(hours=5)
    session["method"] = "Jazz"
    # ticketDetails["date"] = str(d.second + d.minute + d.hour + d.day + d.month)
    mo = ""
    ho = ""
    do = ""
    mino = ""
    so = ""
    if (d.month <= 9):
        mo = "0"
    if (d.hour <= 9):
        ho = "0"
    if (d.day <= 9):
        do = "0"
    if (d.minute <= 9):
        mino = "0"
    if (d.second <= 9):
        so = "0"
    dateT = str(str(d.year) + mo + str(d.month) + do + str(d.day) + ho + str(d.hour) + mino + str(d.minute) + so + str(
        d.second))
    print(dateT)

    if (d.month >= 10):
        mo = ""
    if (d.hour == 9):
        ho = ""
    if (d.day >= 10):
        do = ""
    if (d.minute >= 10):
        mino = ""
    if (d.second >= 10):
        so = ""
    dateEx = str(
        str(d.year) + mo + str(d.month) + do + str(d.day) + ho + str(d.hour + 1) + mino + str(d.minute) + so + str(
            d.second))
    print(dateEx)

    fare = 0
    if ((ticketDetails["others"][-4:])[0] == ':'):
        fare = int(ticketDetails["others"][-3:])
    else:
        fare = int(ticketDetails["others"][-4:])
    return render_template("paywithjazzcash.html", ticketDetails=ticketDetails, fare=int(fare) * 100 * int(session["not"]),
                           dateT=dateT, dateEx=dateEx)
    
    
@app.route('/deleteEmp', methods=["POST"])
def deleteEmp():
    empid = request.get_json(force=True)["empId"]

    if dbObj.deleteEmp(empid):
        return "success"
    return "error"


@app.route('/editEmp', methods=["POST"])
def editEmp():
    emp = request.get_json(force=True)

    if dbObj.editEmp(emp):
        return "success"
    return "error"


@app.route('/success')
def masterSucc():

    bookid = dbObj.addTicket(session)
    return render_template('success.html', bookid=bookid)


@app.route('/jazzcashsuccess', methods=["POST", "GET"])
def jazzcashsuccess():

    bookid = dbObj.addTicket(session)
    return render_template('success.html', bookid=bookid)


@app.route('/showTicket', methods=["GET"])
def showTicket():
    ticketId = request.args.get("ticket")

    res = dbObj.getTicket(ticketId)
    return render_template("showTicket.html", ticket=res)


@app.route('/create-checkout-session', methods=["POST"])
def create_checkout_session():
    amm = 0
    if ((ticketDetails["others"][-4:])[0] == ':'):
        amm = int(ticketDetails["others"][-3:])
    else:
        amm = int(ticketDetails["others"][-4:])
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'pkr',
                        'unit_amount': amm * 100,
                        'product_data': {
                            'name': ticketDetails["others"],
                        },
                    },
                    'quantity': int(ticketDetails["numOfTickets"]),
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        print(str(e))
        return jsonify(error=str(e)), 403


if __name__ == "__main__":
    app.run(debug=True)
