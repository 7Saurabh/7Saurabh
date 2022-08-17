import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
import random
import json
from datetime import datetime
# from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = 'TheTopSecret'
basedir = os.path.abspath(os.path.dirname(__file__))
#whereevner adding copied URI add sql at the end "postgres" || "postgresql"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://twlepcxonmbsek:5c4820c0e8dd2b3d7a08655924c7124eae84744e7afef4d9269472fa64d3b5ad@ec2-52-205-61-230.compute-1.amazonaws.com:5432/d8eub7a2fanhuo'
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)
    attendance = db.Column(db.Boolean, default=False, nullable=True)

    def __repr__(self):
        return '<User %r>' % self.username

class Attendance(db.Model):
    date = db.Column(db.String, primary_key=True)
    # subjects = db.Column(db.String(255))
    awp_ids = db.Column(db.String(255))
    spm_ids = db.Column(db.String(255))

    def __repr__(self):
        return '<Attendance %r>' % self.date

@app.route('/', methods=('GET','POST')) # /register have to add.
def register():
    # STARTS ORIGINAL REGISTER ROUTE
    if request.method == "POST":
        uname = request.form['uname']
        psw = request.form['psw']

        try:
            print(uname, psw)
            admin = User(username=uname, password=psw)
            db.session.add(admin)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            flash("This username is taken, try with new one !")

    return render_template('register.html')

@app.route('/login', methods=('GET','POST'))
def login():
    if request.method == 'POST':
        uname = request.form['uname']
        psw = request.form['psw']

        session['uname'] = uname # For scanner
                        
        stmt = select(User.password).where(User.username == uname) 
        result = db.session.execute(stmt)                                   
        og_psw = result.fetchone() 
        new_psw = ""
        try:
            for i in og_psw:
                new_psw += i
            if psw == new_psw:
                return redirect(url_for('qrscan'))
            else:
                flash("username or password didn't match !")
        except:
            flash("username and password didn't match !")
    return render_template('login.html')

@app.route('/fetchall')
def fetchall():
    rows = User.query.all()
    return render_template('fetchall.html',
                            title='Overview',
                            rows=rows)
@app.route('/fetchall2')
def fetchall2():
    rows = Attendance.query.all()
    return render_template('fetchall2.html',
                            title='Overview',
                            rows=rows)

@app.route('/markAttendance', methods=['GET','POST'])
def markAttendance():
    if request.method == 'POST':
        uname = request.form['uname']
        subject = request.form['subject']
        stmt = select(User.username).where(User.username == uname) 
        result = db.session.execute(stmt)                                   
        og_uname = result.fetchone() 
        new_uname = ""
        for i in og_uname:
            new_uname += i
        print(new_uname)
        if uname == new_uname:
            User.query.filter_by(username=uname).update(dict(attendance=True))
            db.session.commit()
            #for second table
            all_ids = ""
            for id_s in db.session.query(User.username).where(User.attendance == True):
                id_s = str(id_s)
                k = id_s.replace(")","")
                p = k.replace("(","")
                fnl = p.replace("'","")
                all_ids += str(fnl)
                # For reseting value after adding to the another "Attedance Table"
                # Reseting values for every day purpose
                # User.query.filter_by(username=uname).update(dict(attendance=False))
                # db.session.commit()
            # Attendance.query.filter_by(date=datetime.today().strftime('%d-%m-%Y')).update(dict(ids=all_ids))
            ccdate = datetime.today().strftime('%d-%m-%Y')
            strdate = str(ccdate)
            # Attendance.query.filter_by(date=strdate).update(dict(ids=all_ids)) OG
            print(subject)
            if str(subject) == "AWP":
                Attendance.query.filter_by(date=strdate).update(dict(awp_ids=all_ids))
            else:
                Attendance.query.filter_by(date=strdate).update(dict(spm_ids=all_ids))
            db.session.commit()
        else:
            flash('something is wrong')

    return render_template('mark_attendance.html')


@app.route("/qrgenerate", methods=['GET', 'POST'])
def qrgenerate():
    qrnum = random.randint(100,900)
    session['secrete_num'] = qrnum
    print(qrnum)
    if request.method == ['POST']:
        redirect(url_for('qrgenerate'))
    return render_template("generator.html", qrnum=qrnum)

@app.route('/ProcessUserinfo/<string:decodedText>',methods=['POST'])
def ProcessUserinfo(decodedText):
    # this method takes input from javascript scanner file and passes to "qrscan" route. :)
    decodedText=json.loads(decodedText)
    session['decoded'] = decodedText
    return redirect(url_for('qrscan'))

@app.route('/qrscan', methods=['GET', 'POST'])
def qrscan():
    decodedT = session.get('decoded', None)
    qrnum = session.get('secrete_num', None)
    uname = session.get('uname', None)
    oldqrnum = []
    if uname == None:
        return redirect(url_for('login'))
    if decodedT != None and qrnum != None: # To Avoid a TypeError :)
        if int(decodedT) == int(qrnum) :
            print('same')
            User.query.filter_by(username=uname).update(dict(attendance=True))
            db.session.commit()
            oldqrnum.append(qrnum)
            session.clear()
        else:
            print('no same')
    print(decodedT, qrnum)

    return render_template('scanner.html')

@app.route('/logout')
def logout():
    session.clear()
    # have to do logout buttom and template
    return redirect(url_for('login'))

@app.route('/resetUserDB')
def resetUserDB():
    # fetching in attendance if prev Date is not current Date
    for date in db.session.query(Attendance.date):
        pass
    date = str(date)
    k = date.replace("'","")
    n = k.replace(",","")
    g = n.replace(")","")
    sorted_date = g.replace("(","")
    print(sorted_date)
    if sorted_date !=  datetime.today().strftime('%d-%m-%Y'):
        # This function is to reset the User DB every day !
        # This will make every True value in the database False.
        for id_s in db.session.query(User.username).where(User.attendance == True):
            id_s = str(id_s)
            k = id_s.replace(")","")
            p = k.replace("(","")
            s = p.replace("'","")
            fnl = s.replace(",","")
            print(fnl)
            print()
            User.query.filter_by(username=fnl).update(dict(attendance=False))
            db.session.commit()

        # Creating new row for new Date
        # admin = Attendance(date=datetime.today().strftime('%d-%m-%Y'))
        ccdate = datetime.today().strftime('%d-%m-%Y')
        strdate = str(ccdate)
        admin = Attendance(date=strdate)
        db.session.add(admin)
        db.session.commit()
    return "<h1> Reset <h1>"
    # return redirect(url_for('register'))


# migrate = Migrate(app, db)

if __name__ == '__main__':
    # app.run(port=3000,host="0.0.0.0")
    app.run(debug=True)



#ERRORS TO GET 
# on scanning qr if there is no user (login info)
# while scanning you can't flash or do anything redirect as such
# User.query.filter(User.id == 123).delete()
# db.session.commit()

# TO UPDATE DATE QUERY = { Attendance.query.filter_by(date="17-08-2022").update(dict(date="16-08-2022")) }

# If we create different routes for every subject we  can add attendance easily to "Attendance" DB 