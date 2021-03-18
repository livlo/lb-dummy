from flask import Flask, render_template, request, redirect, session, make_response
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import joblib
import json
import csv
import io


application = Flask(__name__)
app = application

ENV = 'dev'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/lb_dummy_dw'
else: #production
    app.debug = False #//username:password@dbname.xxxxxxxxxxxx.eu-central-1.rds.amazonaws.com:3306/dbname'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@postgres-1.c0l2twxdbh9x.ap-southeast-1.rds.amazonaws.com:5432/lb_dummy'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'any random string'

db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    phone = db.Column(db.String(255), unique=True)
    gender = db.Column(db.String(1))
    email = db.Column(db.String(255), unique=True)
    persona = db.Column(db.String(255))
    pref_media = db.Column(db.String(10))

    def __init__(self, user_id, name, phone, gender, email, persona, pref_media):
        self.user_id = user_id
        self.name = name
        self.phone = phone
        self.gender= gender
        self.email = email
        self.persona = persona
        self.pref_media = pref_media

class Transactions(db.Model):
    __tablename__ = 'transactions'
    
    trx_id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.String(255))
    purchase_fashion = db.Column(db.Numeric)
    purchase_fnb = db.Column(db.Numeric)
    purchase_travel = db.Column(db.Numeric)
    purchase_electronic = db.Column(db.Numeric)
    purchase_lifestyle = db.Column(db.Numeric)
    total_amount = db.Column(db.Numeric)

    def __init__(self, trx_id, user_id, purchase_fashion, purchase_fnb, purchase_travel, purchase_electronic, purchase_lifestyle, total_amount):
        self.trx_id = trx_id
        self.user_id = user_id
        self.purchase_fashion = float(purchase_fashion)
        self.purchase_fnb = float(purchase_fnb)
        self.purchase_travel = float(purchase_travel)
        self.purchase_electronic = float(purchase_electronic)
        self.purchase_lifestyle = float(purchase_lifestyle)
        self.total_amount = float(total_amount)

class Interests(db.Model):
    __tablename__ = 'interests'
    
    interest_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), db.ForeignKey('users.user_id'))
    ctor_sms_fashion = db.Column(db.Numeric)
    ctor_sms_fnb = db.Column(db.Numeric)
    ctor_sms_travel = db.Column(db.Numeric)
    ctor_sms_electronic = db.Column(db.Numeric)
    ctor_sms_lifestyle = db.Column(db.Numeric)
    ctor_email_fashion = db.Column(db.Numeric)
    ctor_email_fnb = db.Column(db.Numeric)
    ctor_email_travel = db.Column(db.Numeric)
    ctor_email_electronic = db.Column(db.Numeric)
    ctor_email_lifestyle = db.Column(db.Numeric)
    ctor_push_notif_fashion = db.Column(db.Numeric)
    ctor_push_notif_fnb = db.Column(db.Numeric)
    ctor_push_notif_travel = db.Column(db.Numeric)
    ctor_push_notif_electronic = db.Column(db.Numeric)
    ctor_push_notif_lifestyle = db.Column(db.Numeric)
    acquisition_cost = db.Column(db.Numeric)

    def __init__(self, user_id, ctor_sms_fashion, ctor_sms_fnb, ctor_sms_travel, ctor_sms_electronic, ctor_sms_lifestyle,
                 ctor_email_fashion, ctor_email_fnb, ctor_email_travel, ctor_email_electronic, ctor_email_lifestyle,
                 ctor_push_notif_fashion, ctor_push_notif_fnb, ctor_push_notif_travel, ctor_push_notif_electronic, ctor_push_notif_lifestyle,
                 acquisition_cost):
        self.user_id = user_id
        self.ctor_sms_fashion = float(ctor_sms_fashion)
        self.ctor_sms_fnb = float(ctor_sms_fnb)
        self.ctor_sms_travel = float(ctor_sms_travel)
        self.ctor_sms_electronic = float(ctor_sms_electronic)
        self.ctor_sms_lifestyle = float(ctor_sms_lifestyle)
        self.ctor_email_fashion = float(ctor_email_fashion)
        self.ctor_email_fnb = float(ctor_email_fnb)
        self.ctor_email_travel = float(ctor_email_travel)
        self.ctor_email_electronic = float(ctor_email_electronic)
        self.ctor_email_lifestyle = float(ctor_email_lifestyle)
        self.ctor_push_notif_fashion = float(ctor_push_notif_fashion)
        self.ctor_push_notif_fnb = float(ctor_push_notif_fnb)
        self.ctor_push_notif_travel = float(ctor_push_notif_travel)
        self.ctor_push_notif_electronic = float(ctor_push_notif_electronic)
        self.ctor_push_notif_lifestyle = float(ctor_push_notif_lifestyle)
        self.acquisition_cost = float(acquisition_cost)

class Details(db.Model):
    __tablename__ = 'details'
    
    detail_id = db.Column(db.Integer, primary_key=True)
    trx_id = db.Column(db.String(255), db.ForeignKey('transactions.trx_id'))
    vendor = db.Column(db.String(255))
    item = db.Column(db.String(255))
    qty = db.Column(db.Integer)
    amount = db.Column(db.Numeric)

    def __init__(self, trx_id, vendor, item, qty, amount):
        self.trx_id = trx_id
        self.vendor = vendor
        self.item = item
        self.qty = qty
        self.amount = float(amount)

#initialize global variable
medias = ['sms', 'email', 'push_notif']
categories = ['fnb', 'fashion', 'travel', 'lifestyle', 'electronic']

# helper function
def purchase_items(inputs, category):
    items = []

    try:
        items = list(inputs['details'][category]['items'].keys())
    except:
        items = []

    return items

def amount_counter(inputs):
    total_amount = 0

    for category in categories:
        try:
            items = purchase_items(inputs, category)
            for i in items:
                sub_total = 0
                d = inputs['details'][category]['items'][i]
                sub_total = d['qty'] * d['amount']
                total_amount += sub_total
        except:
            print('_')

    return total_amount

def submit_detail(inputs):
    trx_id = inputs['trx_id']
    res = []
    for category in categories:
        try:
            items = purchase_items(inputs, category)
            for i in items:
                item_name = i
                vendor_name = inputs['details'][category]['vendor']
                item_qty = inputs['details'][category]['items'][i]['qty']
                item_amount = inputs['details'][category]['items'][i]['amount']
                res.append([trx_id,vendor_name,item_name,item_qty,item_amount])
        except:
            print('_')
    
    return res

def input_interest(input):
    temp = {}
    for media in medias:
        for category in categories:
            temp['ctor_'+media+'_'+category] = input['ctor'][media]['category'][category]
    return temp

def total_acquisition_cost(input):
    total = 0
    for media in medias:
        total += input['ctor'][media]['acquisition_cost']
    
    return total

def media_preference(avg_sms, avg_email, avg_push_notif):
    sort = ''
    d = {}
    d[1] = avg_sms
    d[2] = avg_email
    d[3] = avg_push_notif

    for i in range(3):
        sort += str(sorted(d.items(), key=lambda x: x[1], reverse=True)[i][0])
    return sort

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'GET':
        session['persona'] = 'all'
        session['media'] = 'all'

        #get all users
        users = Users.query.all()
        results = [
            {
                "user_id": user.user_id,
                "gender": user.gender,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "persona": user.persona,
                "pref_media": user.pref_media
            } for user in users]

        #get all interests (average CTOR)
        ctors = Interests.query.all()
        results_ctor = [
            [
                ctor.ctor_sms_fnb,
                ctor.ctor_sms_fashion,
                ctor.ctor_sms_travel,
                ctor.ctor_sms_lifestyle,
                ctor.ctor_sms_electronic,
                ctor.ctor_email_fnb,
                ctor.ctor_email_fashion,
                ctor.ctor_email_travel,
                ctor.ctor_email_lifestyle,
                ctor.ctor_email_electronic,
                ctor.ctor_push_notif_fnb,
                ctor.ctor_push_notif_fashion,
                ctor.ctor_push_notif_travel,
                ctor.ctor_push_notif_lifestyle,
                ctor.ctor_push_notif_electronic,
            ] for ctor in ctors]

        total_ctor = 0
        row = len(results_ctor)
        col = 15

        for i in range(row):
            total_ctor += sum(results_ctor[i])
        
        if row == 0:
            row = 1

        avg_ctor = round(total_ctor/(col*row)*100,2)

        return render_template('index.html', users=results, len=len(results), avg_ctor=avg_ctor)
    
    if request.method == 'POST':
        
        # get all data
        users = Users.query.all()
        results = [
            {
                "user_id": user.user_id,
                "gender": user.gender,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "persona": user.persona,
                "pref_media": user.pref_media
            } for user in users]
        
        #get all interests (average CTOR)
        ctors = Interests.query.all()
        results_ctor = [
            [
                ctor.ctor_sms_fnb,
                ctor.ctor_sms_fashion,
                ctor.ctor_sms_travel,
                ctor.ctor_sms_lifestyle,
                ctor.ctor_sms_electronic,
                ctor.ctor_email_fnb,
                ctor.ctor_email_fashion,
                ctor.ctor_email_travel,
                ctor.ctor_email_lifestyle,
                ctor.ctor_email_electronic,
                ctor.ctor_push_notif_fnb,
                ctor.ctor_push_notif_fashion,
                ctor.ctor_push_notif_travel,
                ctor.ctor_push_notif_lifestyle,
                ctor.ctor_push_notif_electronic,
            ] for ctor in ctors]

        total_ctor = 0
        row = len(results_ctor)
        col = 15

        for i in range(row):
            total_ctor += sum(results_ctor[i])
        
        if row == 0:
            row = 1
        avg_ctor = round(total_ctor/col*100,2)


        # ambil data dari input & mapping data" yang penting
        #users
        user_id = request.form['user_id']
        name = request.form['name']
        gender = request.form['gender']
        email = request.form['email']
        phone = request.form['phone']
        
        #transactions
        # get persona dulu. if persona LB0001 = electronic, get electronic details only.
        transactions = json.loads(request.form['purchase'])

        trx_id = transactions['trx_id']
        purchase_fashion = len(purchase_items(transactions,'fashion'))
        purchase_fnb = len(purchase_items(transactions,'fnb'))
        purchase_travel = len(purchase_items(transactions,'travel'))
        purchase_lifestyle = len(purchase_items(transactions,'lifestyle'))
        purchase_electronic = len(purchase_items(transactions,'electronic'))
        total_amount = amount_counter(transactions)

        #interests
        interests = json.loads(request.form['interest'])

        ctor_sms_fashion = input_interest(interests)['ctor_sms_fashion']
        ctor_sms_fnb = input_interest(interests)['ctor_sms_fnb']
        ctor_sms_travel = input_interest(interests)['ctor_sms_fnb']
        ctor_sms_lifestyle = input_interest(interests)['ctor_sms_lifestyle']
        ctor_sms_electronic = input_interest(interests)['ctor_sms_electronic']

        avg_ctor_sms = (ctor_sms_fashion + ctor_sms_fnb + ctor_sms_travel + ctor_sms_lifestyle + ctor_sms_electronic)/5

        ctor_email_fashion = input_interest(interests)['ctor_email_fashion']
        ctor_email_fnb = input_interest(interests)['ctor_email_fnb']
        ctor_email_travel = input_interest(interests)['ctor_email_travel']
        ctor_email_lifestyle = input_interest(interests)['ctor_email_lifestyle']
        ctor_email_electronic = input_interest(interests)['ctor_email_electronic']

        avg_ctor_email = (ctor_email_fashion + ctor_email_fnb + ctor_email_travel + ctor_email_lifestyle + ctor_email_electronic)/5

        ctor_push_notif_fashion = input_interest(interests)['ctor_push_notif_fashion']
        ctor_push_notif_fnb = input_interest(interests)['ctor_push_notif_fnb']
        ctor_push_notif_travel = input_interest(interests)['ctor_push_notif_travel']
        ctor_push_notif_lifestyle = input_interest(interests)['ctor_push_notif_lifestyle']
        ctor_push_notif_electronic = input_interest(interests)['ctor_push_notif_electronic']
        
        avg_ctor_push_notif = (ctor_push_notif_fashion + ctor_push_notif_fnb + ctor_push_notif_travel + ctor_push_notif_lifestyle + ctor_push_notif_electronic)/5

        acquisition_cost = total_acquisition_cost(interests)

        medpref = media_preference(avg_ctor_sms, avg_ctor_email, avg_ctor_push_notif)

        #PREPROCESS DULS
        ctor_fnb = (ctor_sms_fnb + ctor_email_fnb + ctor_push_notif_fnb) / 3
        ctor_fashion = (ctor_sms_fashion + ctor_email_fashion + ctor_push_notif_fashion) / 3
        ctor_travel = (ctor_sms_travel + ctor_email_travel + ctor_push_notif_travel) / 3
        ctor_lifestyle = (ctor_sms_lifestyle + ctor_email_lifestyle + ctor_push_notif_lifestyle) / 3
        ctor_electronic = (ctor_sms_electronic + ctor_email_electronic + ctor_push_notif_electronic) / 3

        # kumpulin jadi 1 dataframe
        new_data = pd.DataFrame([[ctor_fnb, ctor_fashion, ctor_travel, ctor_lifestyle, ctor_electronic, purchase_fnb, purchase_fashion, purchase_travel, purchase_lifestyle, purchase_electronic, 1 if gender == 'F' else 0, 1 if gender == 'M' else 0]])

        #MACHINE LEARNING DULS
        model_clone = joblib.load('model.pkl')
        persona = model_clone.predict(new_data)[0]
        
        try:
            data_users = Users(user_id, name, phone, gender, email, persona, medpref)
            db.session.add(data_users)
            db.session.commit()

            #Interests
            data_interests = Interests(user_id, ctor_sms_fashion, ctor_sms_fnb, ctor_sms_travel, ctor_sms_electronic, ctor_sms_lifestyle,
                    ctor_email_fashion, ctor_email_fnb, ctor_email_travel, ctor_email_electronic, ctor_email_lifestyle,
                    ctor_push_notif_fashion, ctor_push_notif_fnb, ctor_push_notif_travel, ctor_push_notif_electronic, ctor_push_notif_lifestyle,
                    acquisition_cost)
            db.session.add(data_interests)
            db.session.commit()

            #Transactions
            data_transactions = Transactions(trx_id, user_id, purchase_fashion, purchase_fnb, purchase_travel, purchase_electronic, purchase_lifestyle, total_amount)
            db.session.add(data_transactions)
            db.session.commit()

            #Details
            detail_data = submit_detail(transactions)
            for i in range(len(detail_data)):
                trx_id = detail_data[i][0]
                vendor = detail_data[i][1]
                item = detail_data[i][2]
                qty = detail_data[i][3]
                amount = detail_data[i][4]

                data_details = Details(trx_id, vendor, item, qty, amount)
                db.session.add(data_details)
                db.session.commit()

            #success
            return redirect("/")

        except Exception as e:
            print('error while inserting users', e)
            return render_template('index.html',users=results, len = len(results), message=e, avg_ctor=avg_ctor)

@app.route('/details/<user_id>', methods=['GET'])
def show(user_id):
    if request.method == 'GET':
        detail_trxs = db.session.execute("""
        SELECT t.user_id, d.trx_id, d.vendor, d.item, d.qty, d.amount
        FROM transactions t JOIN details d
        ON t.trx_id = d.trx_id
        WHERE t.user_id = '%s' """ %(user_id))

        results_detail = [
            [
                detail.user_id,
                detail.trx_id,
                detail.vendor,
                detail.item,
                detail.qty,
                detail.amount
            ] for detail in detail_trxs]

        return render_template('details.html', details = results_detail, len = len(results_detail))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        persona = request.args.get('persona')
        selectedMedia = request.args.get('media')

        if selectedMedia == 'sms':
            media = '1'
        elif selectedMedia == 'email':
            media = '2'
        elif selectedMedia == 'push_notif':
            media = '3'
        else:
            media = 'all'
        
        
        session['persona'] = persona
        session['media'] = media

        #initialize persona=all, pref_media=all
        filtered_users = db.session.execute("""
        SELECT * 
        FROM users u JOIN interests i
        ON u.user_id = i.user_id
        """)

        #get all filtered users
        if persona != 'all' and media == 'all':
            filtered_users = db.session.execute("""
            SELECT * 
            FROM users u JOIN interests i
            ON u.user_id = i.user_id
            WHERE u.persona='%s'
            """%(persona))
            
        if persona == 'all' and media != 'all':
            filtered_users = db.session.execute("""
            SELECT * 
            FROM users u JOIN interests i
            ON u.user_id = i.user_id
            WHERE LEFT(u.pref_media,1)='%s'
            """%(media))
        
        if persona != 'all' and media != 'all':
            filtered_users = db.session.execute("""
            SELECT *
            FROM users u JOIN interests i
            ON u.user_id = i.user_id
            WHERE u.persona='%s' AND LEFT(u.pref_media,1)='%s'
            """%(persona,media))
        

        results_filtered_users = [
            {
                "user_id": user.user_id,
                "gender": user.gender,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "persona": user.persona,
                "pref_media": user.pref_media,
                "ctor_sms_fnb":user.ctor_sms_fnb,
                "ctor_sms_fashion":user.ctor_sms_fashion,
                "ctor_sms_travel":user.ctor_sms_travel,
                "ctor_sms_lifestyle":user.ctor_sms_lifestyle,
                "ctor_sms_electronic":user.ctor_sms_electronic,
                "ctor_email_fnb":user.ctor_email_fnb,
                "ctor_email_fashion":user.ctor_email_fashion,
                "ctor_email_travel":user.ctor_email_travel,
                "ctor_email_lifestyle":user.ctor_email_lifestyle,
                "ctor_email_electronic":user.ctor_email_electronic,
                "ctor_push_notif_fnb":user.ctor_push_notif_fnb,
                "ctor_push_notif_fashion":user.ctor_push_notif_fashion,
                "ctor_push_notif_travel":user.ctor_push_notif_travel,
                "ctor_push_notif_lifestyle":user.ctor_push_notif_lifestyle,
                "ctor_push_notif_electronic":user.ctor_push_notif_electronic
            } for user in filtered_users]

        # persona all, selectedMedia all
        results_filtered_ctor = [
                [v for k, v in results_filtered_users[i].items() if k.startswith('ctor')
                ] for i in range(len(results_filtered_users))]
        
        col = 15
        total_filtered_ctor = 0
        row = len(results_filtered_ctor)

        # persona != all
        if persona != 'all':
            results_filtered_ctor = [
                [v for k, v in results_filtered_users[i].items() if k.startswith('ctor') and (persona in k)
                ] for i in range(len(results_filtered_users))]
            col = 3

        elif media != 'all':
            results_filtered_ctor = [
                [v for k, v in results_filtered_users[i].items() if k.startswith('ctor') and (selectedMedia in k)
                ] for i in range(len(results_filtered_users))]
            col = 3

        if persona != 'all' and media != 'all':
            results_filtered_ctor = [
                [v for k, v in results_filtered_users[i].items() if k.startswith('ctor') and (selectedMedia in k) and (persona in k)
                ] for i in range(len(results_filtered_users))]
            col = 1

        for i in range(row):
            total_filtered_ctor += sum(results_filtered_ctor[i])
        
        if row == 0:
            row = 1
        
        avg_filtered_ctor = round(total_filtered_ctor/(col*row) * 100,2)

        return render_template('index.html', users=results_filtered_users, len=len(results_filtered_users), avg_ctor=avg_filtered_ctor)

@app.route('/export', methods=['GET', 'POST'])
def export():
    persona = session['persona']
    media = session['media']

    filtered_users = db.session.execute("""
        SELECT * 
        FROM users u JOIN interests i
        ON u.user_id = i.user_id
        """)
    
    #get all filtered users
    if persona != 'all' and media == 'all':
        filtered_users = db.session.execute("""
        SELECT * 
        FROM users u JOIN interests i
        ON u.user_id = i.user_id
        WHERE u.persona='%s'
        """%(persona))
        
    if persona == 'all' and media != 'all':
        filtered_users = db.session.execute("""
        SELECT * 
        FROM users u JOIN interests i
        ON u.user_id = i.user_id
        WHERE LEFT(u.pref_media,1)='%s'
        """%(media))
    
    if persona != 'all' and media != 'all':
        filtered_users = db.session.execute("""
        SELECT *
        FROM users u JOIN interests i
        ON u.user_id = i.user_id
        WHERE u.persona='%s' AND LEFT(u.pref_media,1)='%s'
        """%(persona,media))
        
    #create export structure
    header = [['user_id','name','gender','email','phone','persona','pref_media']]
    csvList = [
        [
            user.user_id,
            user.name,
            user.gender,
            user.email,
            user.phone,
            user.persona,
            user.pref_media
        ]for user in filtered_users]
    csvList[:0] = header

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(csvList)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

if __name__ == '__main__':
    app.run()