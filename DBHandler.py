from datetime import datetime

import pymysql
import pymysql.cursors


class DBHandler:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def employeeTrains(self, empID):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            query = 'select ScheduleID from empsched where EmpId = %s'
            mydbCursor.execute(query, empID)

            ScheduleID = mydbCursor.fetchall()

            if ScheduleID:
                myList = []
                toPass = "("
                for x in ScheduleID:
                    toPass = toPass + "%s,"
                    myList.append(x[0])
                toPass = toPass[:-1]
                toPass = toPass + ")"
                values = tuple(myList)
                queryTwo = "select * from schedule, trains where schedule.trainid = trains.trainid and schedule.ScheduleID IN " + toPass
                arg = values
                mydbCursor.execute(queryTwo, arg)
                result = mydbCursor.fetchall()

                resultList = []
                for x in result:
                    mydict = {}
                    mydict["scheduleID"] = x[0]
                    mydict["trainID"] = x[1]
                    mydict["trainName"] = x[-1]
                    mydict["deptTime"] = x[2]
                    mydict["from"] = x[3]
                    mydict["to"] = x[4]
                    mydict["fare"] = x[5]
                    mydict["ecomonySeats"] = x[6]
                    mydict["businessSeats"] = x[7]
                    resultList.append(mydict)

                return resultList
            else:
                return "No Train Alloted"
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def checkTicket(self, busOrEco, NOT, sid):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        cur = db.cursor()
        try:
            if busOrEco == "bus":
                sql = 'SELECT bussinesseatsremaining from schedule where scheduleid = %s'
            else:
                sql = 'SELECT EconomySeatsRemaining from schedule where scheduleid = %s'
            cur.execute(sql, (sid))
            res = cur.fetchall()
            print("res", res[0][0])
            if (int(res[0][0]) >= int(NOT)):
                return True
            return False
        except Exception as e:
            print(str(e))
        finally:
            db.close()

    def deleteEmp(self, empId):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        cur = db.cursor()
        try:
            sql = 'delete from empsched where empid = %s'
            cur.execute(sql, (empId))
            db.commit()
            cur.execute('select authid from employee where empid=%s', (empId))
            results = cur.fetchall()
            authid = results[0][0]
            cur.execute('delete from employee where authid=%s', (authid))
            db.commit()
            cur.execute('delete from auth where authid=%s', (authid))
            db.commit()
            return True

        except Exception as e:

            return False
        finally:
            db.close()

    def getStations(self):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        cur = db.cursor()
        try:
            sql = 'SELECT * from trains'
            cur.execute(sql)
            trains = cur.fetchall()
            trainList = []
            names = []
            for t in trains:
                trainList.append(t[0])
                names.append(t[1])
            sql = 'SELECT * from schedule inner join trains on schedule.TrainID = trains.TrainID order by schedule.FromStation'
            cur.execute(sql)
            results = cur.fetchall()
            finalRes = []
            added = []
            for res in results:
                finalsD = dict()
                finalsD["schedid"] = res[0]
                finalsD["trainid"] = res[1]
                added.append(res[1])
                finalsD["time"] = res[2]
                finalsD["start"] = res[3]
                finalsD["end"] = res[4]
                finalsD["farePer"] = res[5]
                finalsD["TrainName"] = res[-1]
                if (res[6] != 0 or res[7] != 0) and (
                        datetime.strptime(finalsD["time"], "%H:%M %d/%m/%Y")) > datetime.now():
                    finalRes.append(finalsD)
            for i in range(0, len(trainList)):
                if trainList[i] not in added:
                    finalsD = dict()
                    finalsD["schedid"] = 0
                    finalsD["trainid"] = trainList[i]
                    finalsD["time"] = 0
                    finalsD["start"] = '0'
                    finalsD["end"] = '0'
                    finalsD["farePer"] = '0'
                    finalsD["TrainName"] = names[i]

                    finalRes.append(finalsD)
            return finalRes

        except Exception as e:
            print(str(e))
        finally:
            db.close()

    def getTicket(self, TID):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        cur = db.cursor()
        try:
            sql = 'SELECT * from ticketbooking ti,trains t,schedule s,passengers p where s.scheduleid = ti.scheduleid and t.trainid = s.trainid and ti.pid = p.pid and ti.bookid = %s'
            cur.execute(sql, (TID))
            results = cur.fetchall()
            res = results[0]
            ticket = dict()
            print(res)
            ticket["Method"] = res[3]
            ticket["NumOfTick"] = res[4]
            ticket["busOrEco"] = res[6]
            ticket["Train"] = res[8]
            ticket["Time"] = res[11]
            ticket["From"] = res[12]
            ticket["To"] = res[13]
            ticket["ontickCost"] = res[14]
            ticket["fee"] = res[14] * res[4]
            ticket["fname"] = res[17]
            ticket["lname"] = res[18]
            ticket["CNIC"] = res[20]
            ticket["Phone"] = res[22]
            if ticket["busOrEco"] == "B":
                ticket["ontickCost"] = ticket["ontickCost"] * .2 + ticket["ontickCost"]
                ticket["fee"] = ticket["ontickCost"] * res[4]
                ticket["busOrEco"] = "Business"
            else:
                ticket["busOrEco"] = "Economy"
            if ticket["Method"] == "Cash":
                ticket["RemainingP"] = ticket["fee"]
            else:
                ticket["RemainingP"] = 0
                if ticket["Method"] == "Jazz":
                    ticket["Method"] = "Jazzcash"
                elif ticket["Method"] == "Card":
                    ticket["Method"] = "Card Payment"

            return ticket
        except Exception as e:
            print(str(e))
        finally:
            db.close()

    def addTicket(self, sess):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        cur = db.cursor()
        try:
            if sess.get("method") == None or sess.get("method") == "":
                sess["method"] = "Cash"
            sql = ""
            if sess.get("busOrEco") == "bus":
                sql = 'insert into ticketbooking (bookid,pid,ScheduleID,payment,numoftick,busOrEco) values (null,%s,%s,%s,%s,%s)'
                cur.execute(sql, (sess["pid"], sess["sid"], sess["method"], sess["not"], 'B'))
                db.commit()
                sql = 'update schedule set BussinesSeatsRemaining = (select BussinesSeatsRemaining from schedule where scheduleid = %s)-%s where scheduleid = %s'
            else:
                sql = 'insert into ticketbooking (bookid,pid,ScheduleID,payment,numoftick,busOrEco) values (null,%s,%s,%s,%s,%s)'
                cur.execute(sql, (sess["pid"], sess["sid"], sess["method"], sess["not"], 'E'))
                db.commit()
                sql = 'update schedule set EconomySeatsRemaining = (select EconomySeatsRemaining from schedule where scheduleid = %s)-%s where scheduleid = %s'
            cur.execute(sql, (sess.get("sid"), sess.get("not"), sess.get("sid")))
            db.commit()
            cur.execute('select bookid from ticketbooking where pid=%s', (sess["pid"]))
            results = cur.fetchall()
            return results[-1][0]

        except Exception as e:

            return False
        finally:
            db.close()

    def insertRecord(self, username, fname, lname, cnic, phone, password):
        mydb = None
        try:
            successFullyInserted = True
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()

            checkQuery = 'SELECT * FROM auth WHERE username=%s'
            mydbCursor.execute(checkQuery, username)
            result = mydbCursor.fetchall()
            if result:
                return False
            else:
                query = 'INSERT into auth(username,password,role) VALUES(%s,%s,%s)'
                args = (username, password, "P")
                mydbCursor.execute(query, args)
                mydb.commit()

                queryTwo = 'Select authID from auth where username=%s'
                mydbCursor.execute(queryTwo, username)
                authID = mydbCursor.fetchall()

                queryThree = 'INSERT into passengers(fname,lname,cnic,authID,phone) values(%s,%s,%s,%s,%s)'
                arg = (fname, lname, cnic, authID, phone)
                mydbCursor.execute(queryThree, arg)
                mydb.commit()

                mydbCursor.execute("select pid from passengers where authid =%s", (authID))
                pid = mydbCursor.fetchall()
                return pid[0][0]

        except Exception as e:

            successFullyInserted = False
            return successFullyInserted
        finally:
            if mydb != None:
                mydb.close()

    def userLogIn(self, username, password):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()

            Query = 'SELECT role,authid FROM auth WHERE username=%s and password=%s'
            arg = (username, password)
            mydbCursor.execute(Query, arg)
            result = mydbCursor.fetchall()
            if result:
                r = result[0]
                if r[0] == "P":
                    mydbCursor.execute('select pid from passengers where authid = %s', (result[0][1]))
                    pid = mydbCursor.fetchall()
                    resultList = ["True", r[0], pid[0][0]]
                else:
                    mydbCursor.execute('select empid from employee where authid = %s', (result[0][1]))
                    eid = mydbCursor.fetchall()

                    resultList = ["True", r[0], eid[0][0]]
            else:
                resultList = ["False", ""]
            return resultList
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def getEmps(self):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        cur = db.cursor()
        try:
            sql = 'SELECT * from employee e, empsched es where es.EmpId = e.empid'
            cur.execute(sql)
            results = cur.fetchall()
            sql = 'SELECT * from employee e'
            cur.execute(sql)
            remainings = cur.fetchall()
            finalRes = []
            addedEmps = []
            for r in results:
                emp = dict()
                addedEmps.append(r[0])
                emp["empID"] = r[0]
                emp["FName"] = r[1]
                emp["LName"] = r[2]
                emp["CNIC"] = r[3]
                emp["Des"] = r[4]
                emp["Phone"] = r[5]
                emp["SchedId"] = r[-1]
                finalRes.append(emp)
            for r in remainings:
                if (r[0] not in addedEmps):
                    emp = dict()
                    emp["empID"] = r[0]
                    emp["FName"] = r[1]
                    emp["LName"] = r[2]
                    emp["CNIC"] = r[3]
                    emp["Des"] = r[4]
                    emp["Phone"] = r[5]
                    finalRes.append(emp)
            return finalRes
        except Exception as e:
            print(str(e))
        finally:
            db.close()

    def getSingleSched(self, sid):
        db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        cur = db.cursor()
        try:
            sql = 'SELECT * from schedule s, trains t where s.ScheduleID = %s and t.trainid = s.trainid'
            cur.execute(sql, (sid))
            results = cur.fetchall()
            results = results[0]
            schedule = dict()
            schedule["schedId"] = results[0]
            schedule["trainId"] = results[1]
            schedule["date"] = results[2]
            schedule["start"] = results[3]
            schedule["end"] = results[4]
            schedule["fare"] = results[5]
            schedule["trainName"] = results[-1]
            return schedule
        except Exception as e:
            print(str(e))
        finally:
            db.close()

    def editSched(self, form):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()

            sql = 'update schedule set fromstation = %s, tostation = %s, fare = %s, DeptTime = %s where scheduleid = %s'
            mydbCursor.execute(sql, (
                form.get("start"), form.get("end"), form.get("fare"), form.get("date"), form.get("schedId")))
            mydb.commit()
            sql = 'update trains set trainName = %s where trainid = %s'
            mydbCursor.execute(sql, (form.get("trainName"), form.get("trainId")))
            mydb.commit()
            return True
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def getPassengers(self, sid):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()

            sql = 'select p.fname,p.lname,p.cnic,p.phone,t.payment,t.numoftick from passengers p, ticketbooking t where t.scheduleid = %s and p.pid = t.pid'
            mydbCursor.execute(sql, (sid))
            results = mydbCursor.fetchall()
            finalRes = []
            for r in results:
                d = dict()
                d["FName"] = r[0]
                d["LName"] = r[1]
                d["CNIC"] = r[2]
                d["phone"] = r[3]
                d["method"] = r[4]
                d["not"] = r[5]
                finalRes.append(d)

            return finalRes
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def getEmployees(self, sid):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()

            sql = 'select e.fname,e.lname,e.cnic,e.phone,e.designation,e.empid from employee e, empsched em where em.scheduleid = %s and em.empid = e.empid'
            mydbCursor.execute(sql, (sid))
            results = mydbCursor.fetchall()
            finalRes = []
            for r in results:
                d = dict()
                d["FName"] = r[0]
                d["LName"] = r[1]
                d["CNIC"] = r[2]
                d["phone"] = r[3]
                d["desig"] = r[4]
                d["eid"] = r[-1]
                finalRes.append(d)
            return finalRes
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def getEmployeesToAdd(self, sid):
        mydb = None
        alreadyAdded = self.getEmployees(sid)
        alreadyEmps = []
        for a in alreadyAdded:
            alreadyEmps.append(a["eid"])

        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = 'select empid, fname,lname,designation from employee'
            mydbCursor.execute(sql)
            results = mydbCursor.fetchall()

            finalRes = []
            eid = []
            for r in results:
                d = dict()
                if r[0] not in eid and r[0] not in alreadyEmps:
                    eid.append(r[0])
                    d["eid"] = str(r[0])
                    d["FName"] = r[1]
                    d["LName"] = r[2]
                    d["desig"] = r[3]
                    finalRes.append(d)

            return finalRes
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def addEmployToSched(self, eid, sid):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = 'INSERT INTO `empsched` (`EmpSchedId`, `EmpId`, `ScheduleID`) VALUES (NULL, %s, %s);'
            mydbCursor.execute(sql, (eid, sid))
            mydb.commit()
            return True
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def deleteEmpSched(self, eid, sid):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = 'delete from empsched where scheduleid = %s and empid = %s'
            mydbCursor.execute(sql, (sid, eid))
            mydb.commit()
            return True
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def addTrain(self, trainName):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = "select trainid from trains where lower(trainname) = lower(%s)"
            mydbCursor.execute(sql, (trainName))
            res = mydbCursor.fetchall()
            if (len(res) != 0):
                return False
            sql = 'insert into trains (trainid, trainName) values (null, %s)'
            mydbCursor.execute(sql, (trainName))
            mydb.commit()
            return True
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def addEmployee(self, emp):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = "select authid from auth where lower(username) = lower(%s)"
            mydbCursor.execute(sql, (emp["userName"]))
            res = mydbCursor.fetchall()
            if (len(res) != 0):
                return False
            sql = 'insert into auth (authid,username, password,role) values (null,%s,"emp123","E")'
            mydbCursor.execute(sql, (emp["userName"]))
            mydb.commit()
            sql = "select authid from auth where lower(username) = lower(%s)"
            mydbCursor.execute(sql, (emp["userName"]))
            res = mydbCursor.fetchall()
            authid = res[0][0]
            sql = 'insert into employee (empid,fname,lname,cnic,designation,phone,authid) values (null,%s,%s,%s,%s,%s,%s)'
            mydbCursor.execute(sql, (emp["fname"], emp["lname"], emp["cnic"], emp["desig"], emp["contact"], authid))
            mydb.commit()
            mydbCursor.execute(
                'select e.fname,e.lname,e.cnic,e.phone,e.designation,e.empid from employee e where authid = %s',
                (authid))
            r = mydbCursor.fetchall()
            r = r[0]
            d = dict()
            d["FName"] = r[0]
            d["LName"] = r[1]
            d["CNIC"] = r[2]
            d["Phone"] = r[3]
            d["Des"] = r[4]
            d["empID"] = r[-1]

            return d
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def addSched(self, sched):
        mydb = None
        try:
            print(sched)
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = 'insert into schedule (trainid,fromstation,tostation,fare,depttime) values (%s,%s,%s,%s,%s)'
            mydbCursor.execute(sql, (sched["trainid"], sched["start"], sched["end"], sched["fare"], sched["dept"]))
            mydb.commit()
            return True
        except Exception as e:
            print(str(e))
            return False
        finally:
            if mydb != None:
                mydb.close()

    def getTickets(self, pid):
        items = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `ticketbooking` WHERE pid = %s"
                myCur.execute(sql, (pid))
                items = myCur.fetchall()
                return items

        except Exception as e:
            return items
        finally:
            if myDb != None:
                myDb.close()

    def editEmp(self, emp):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = 'update employee set fname = %s, lname = %s, cnic = %s, designation=%s, phone = %s where empid = %s'
            mydbCursor.execute(sql, (emp["fname"], emp["lname"], emp["cnic"], emp["desig"], emp["phone"], emp["empId"]))
            mydb.commit()
            return True
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def PasssengersWithCash(self, SID):
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            query = "select * from ticketbooking t, passengers p where t.ScheduleID=%s AND t.Payment='Cash' AND t.PID = p.PID"

            mydbCursor.execute(query, SID)
            result = mydbCursor.fetchall()
            print(result)
            if result:
                allPassengers = []
                for x in result:
                    singlePassenger = {}
                    singlePassenger["bookingid"] = x[0]
                    singlePassenger["numberOfTickets"] = x[4]
                    singlePassenger["firstname"] = x[7]
                    singlePassenger["lastname"] = x[8]
                    singlePassenger["pid"] = x[9]
                    singlePassenger["cnic"] = x[10]
                    singlePassenger["phone"] = x[12]
                    singlePassenger["class"] = x[6]
                    if (singlePassenger["class"] == "B"):
                        singlePassenger["class"] = "Business"
                    else:
                        singlePassenger["class"] = "Economy"
                    allPassengers.append(singlePassenger)

                return allPassengers
            else:
                return "No"
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()

    def setAuth(self, user):
        sql = 'INSERT into auth(username,password,role) VALUES(%s,%s,%s)'
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `auth` WHERE username = %s"
                myCur.execute(sql, (user['username']))
                item = myCur.fetchone()
                if item:
                    return False
                else:
                    sql = 'INSERT into auth(username,password,role) VALUES(%s,%s,%s)'
                    myCur.execute(
                        sql, (user['username'], user['password'], user['role']))
                    myDb.commit()
                    return True

        except Exception as e:

            return False
        finally:
            if myDb != None:
                myDb.close()

    def setPassenger(self, user):
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "INSERT INTO `passengers` (`fname`, `lname`, `cnic`, `authID`, `phone`) VALUES(%s, %s, %s, %s, %s)"
                myCur.execute(
                    sql, (user['fname'], user['lname'], user['cnic'], user['authID'], user['ph']))
                myDb.commit()
                return True

        except Exception as e:

            return False
        finally:
            if myDb != None:
                myDb.close()

    def getAuthId(self, username):
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT authID FROM `auth` WHERE username = %s"
                myCur.execute(sql, (username))
                item = myCur.fetchone()
                return item

        except Exception as e:

            return False
        finally:
            if myDb != None:
                myDb.close()

    def getTickets(self, pid):
        items = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `ticketbooking` WHERE pid = %s"
                myCur.execute(sql, (pid))
                items = myCur.fetchall()
                return items

        except Exception as e:

            return False
        finally:
            if myDb != None:
                myDb.close()

    def getSingleTicket(self, tkid):
        item = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `ticketbooking` WHERE BookID = %s"
                myCur.execute(sql, (tkid))
                item = myCur.fetchone()
                return item

        except Exception as e:

            return item
        finally:
            if myDb != None:
                myDb.close()

    def getAuth(self, user, pw):
        item = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `auth` WHERE username = %s and password = %s"
                myCur.execute(sql, (user, pw))
                item = myCur.fetchone()
                return item
        except Exception as e:

            return {}
        finally:
            if myDb != None:
                myDb.close()

    def getPassenger(self, authID):
        item = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `passengers` WHERE authID = %s"
                myCur.execute(sql, (authID))
                item = myCur.fetchone()
                return item
        except Exception as e:
            return item
        finally:
            if myDb != None:
                myDb.close()

    def getSchedule(self, schid):
        item = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `schedule` WHERE ScheduleID = %s"
                myCur.execute(sql, (schid))
                item = myCur.fetchone()
                return item

        except Exception as e:

            return item
        finally:
            if myDb != None:
                myDb.close()

    def getTrain(self, tid):
        item = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `trains` WHERE trainID = %s"
                myCur.execute(sql, (tid))
                item = myCur.fetchone()
                return item

        except Exception as e:

            return item
        finally:
            if myDb != None:
                myDb.close()

    def getAllTrain(self):
        items = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `trains`"
                myCur.execute(sql)
                items = myCur.fetchall()
                return items

        except Exception as e:

            return items
        finally:
            if myDb != None:
                myDb.close()

    def getAllSchedules(self):
        items = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `schedule`"
                myCur.execute(sql)
                items = myCur.fetchall()
                return items

        except Exception as e:

            return items
        finally:
            if myDb != None:
                myDb.close()

    def getEmployee(self, authID):
        item = []
        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database,
                cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:
                sql = "SELECT * FROM `employee` WHERE authID = %s"
                myCur.execute(sql, (authID))
                item = myCur.fetchone()
                return item

        except Exception as e:
            return False
        finally:
            if myDb != None:
                myDb.close()

    def changePass(self, passw):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = 'select * from auth where authid = %s and password = %s'
            mydbCursor.execute(sql,(passw["authId"],passw["old"]))
            res = mydbCursor.fetchall()
            if len(res) == 0:
                return False
            sql = 'update auth set password = %s where authId = %s'
            mydbCursor.execute(sql, (passw["new"], passw["authId"]))
            mydb.commit()
            return True
        except Exception as e:
            print(str(e))
            return False
        finally:
            if mydb != None:
                mydb.close()


    def getDataForLineChart(self):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = 'select dateBought, numoftick from ticketbooking where dateBought >= DATE(NOW()) - INTERVAL 7 DAY'
            mydbCursor.execute(sql)
            res = mydbCursor.fetchall()
            finalDict = dict()
            for r in res:
                if (finalDict.get(r[0]) == None):
                    finalDict[r[0]] = int(r[1])
                else:
                    finalDict[r[0]] += int(r[1])
            print(finalDict)
            return finalDict
        except Exception as e:
            return False
        finally:
            if mydb != None:
                mydb.close()

    def getDataForPieChart(self):
        mydb = None
        try:
            mydb = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            mydbCursor = mydb.cursor()
            sql = 'select count(*) from ticketbooking where Payment = "Cash"'
            mydbCursor.execute(sql)
            cash = mydbCursor.fetchall()
            sql = 'select count(*) from ticketbooking where Payment = "Card"'
            mydbCursor.execute(sql)
            card = mydbCursor.fetchall()
            sql = 'select count(*) from ticketbooking where Payment = "Jazz"'
            mydbCursor.execute(sql)
            jazz = mydbCursor.fetchall()
            finalDict = dict()
            finalDict["cash"] = cash
            finalDict["jazz"] = jazz
            finalDict["card"] = card
            print(finalDict)
            return finalDict
        except Exception as e:

            return False
        finally:
            if mydb != None:
                mydb.close()
                
    def updatePassenger(self, user):

        try:
            myDb = self.myDb = pymysql.connect(
                host=self.host, user=self.user, password=self.password, db=self.database, cursorclass=pymysql.cursors.DictCursor)
            with myDb.cursor() as myCur:

                passQuery = "UPDATE `passengers` SET `fname` = %s, `lname` = %s, `cnic` = %s, `phone` = %s WHERE `PID` = %s"
                myCur.execute(
                    passQuery, (user['fname'], user['lname'], user['cnic'], user['phone'], user['PID']))
                myDb.commit()
                return True

        except Exception as e:
            print(e)
            return False

        finally:
            if myDb != None:
                myDb.close()