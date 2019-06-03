from flask import Flask, request, redirect, Response, url_for, session, flash, jsonify
from flask import render_template
from flaskext.mysql import MySQL
from functools import wraps
import os
# from os.path import join, dirname, realpath
from flask import send_from_directory

# file upload
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './static/img'

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# from flask.ext.session import Session
#from flask_mysqldb import MySQL

app = Flask(__name__, static_url_path='')

mysql = MySQL()

# Config MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
#app.config['MYSQL_DATABASE_PORT'] = '3306'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'city88'
app.config['MYSQL_DATABASE_DB'] = 'car_to_go'
#app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # file upload
# init MYSQL
mysql.init_app(app)


@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.method == 'GET':
        cur = mysql.get_db().cursor()

        result = cur.execute("SELECT drivers.car_pictures FROM drivers INNER JOIN record ON record.driver_id = drivers.id ORDER BY record.created_at DESC LIMIT 3")


        data = cur.fetchall()


        feedback = cur.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT 3")
        feedback = cur.fetchall()

        feedback2 = cur.execute("SELECT * FROM feedback ORDER BY id ASC LIMIT 3")
        feedback2= cur.fetchall()

        print (feedback2)
        return render_template("index.html", data=data, feedback=feedback, feedback2=feedback2)
        # return render_template("index.html", data=data)

    if request.method == 'POST':

        user_id = session['user_id']

        feedback = request.form['feedback']

        cur = mysql.get_db().cursor()
        cur.execute("INSERT INTO feedback (user_id, feedback) VALUES (%s, %s)", [user_id, feedback])
        
        mysql.get_db().commit()
        msg = "Your feedback is highly appreciated "
        return render_template("index.html", msg=msg )


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pass']
        rePassword = request.form['repass']
        gender = request.form['gender']

        cur = mysql.get_db().cursor()
        result = cur.execute("SELECT email FROM users WHERE email = %s", [email])

        if result > 0:
            msg = "This account has been token"
            print ("have this mail")
            return render_template("signup.html", msg=msg)

        if password != rePassword: 
            msg = "Password doesn't match"
            print ("not the sampe passwordd")
            return render_template("signup.html", msg=msg)

        sex = 0 if (gender == "Female") else 1

        cur.execute("INSERT INTO users (email, password, gender) VALUES (%s, %s, %s)", [email, password, int(sex)])
        
        mysql.get_db().commit()

        return render_template("login.html")

    else: 
        return render_template("signup.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_candidate = request.form['pass']

        cur = mysql.get_db().cursor()

        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])

        if result > 0:

            account_candidate = cur.execute("SELECT * FROM users WHERE email = %s AND password = %s ", [email, password_candidate]) 
            
            if account_candidate > 0: 
                session['logged_in'] = True
                session['email'] = email

                user = cur.fetchone()

                session['user_id'] = user[0]
                session['user_role'] = user[4]
                
                return render_template('index.html')
            else: 
                msg = "Invalid password" 
                return render_template('login.html', msg = msg)

        else:
            msg = "Invalid email" 
            return render_template('login.html', msg = msg)

        cur.close()
    else:
        return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            # flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for('login'))



@app.route("/filter")
@is_logged_in
def filter():

    cur = mysql.get_db().cursor()

    result = cur.execute("SELECT * FROM districts")
   
    if result > 0:
        data = cur.fetchall()
        print(data)
        return render_template("filter.html", data = data)
    # else:
    #     data = "No data"
    #     return render_template("filter.html", data = data)


@app.route("/driverfilter")
@is_logged_in
def driverfilter():

    cur = mysql.get_db().cursor()

    result = cur.execute("SELECT * FROM districts")

    if result > 0:

        data = cur.fetchall()

        return render_template("driverfilter.html", data=data)


        

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/uploader', methods = ['GET', 'POST'])
@is_logged_in
def upload_file():
    if request.method == 'POST':
        
        print(request.form)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):        
            filename = secure_filename(file.filename)
            plate_num  = request.form['plate_num']
            car_brand = request.form['car_brand']
            car_model = request.form['car_model']
            car_rules = request.form['car_rules']
            car_capacity = request.form['car_capacity']
            district_id = request.form['district_id']

            # dropoff_location=request.form['dropoff_location']
            car = car_brand + car_model
            cur = mysql.get_db().cursor()

            cur.execute("INSERT INTO drivers (plate_num, car_model, car_capacity, rules, car_pictures,district_id) VALUES (%s, %s, %s, %s, %s,%s)", [plate_num, car, car_capacity,car_rules,filename,district_id])

            # cur.execute("INSERT INTO record(driver_id,dropoff_location) VALUES (%s,%s)",[cur.lastrowid,dropoff_location])

        
            mysql.get_db().commit()

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # return redirect(url_for('uploaded_file',
            #                         filename=filename))
            return redirect('/')

    return redirect(request.url)

@app.route("/dashboard", methods = ['GET', 'POST'])
@is_logged_in
def dashboard():
    if request.method == 'GET':
        user_id = session['user_id']

        cur = mysql.get_db().cursor()

        if session['user_role'] == 1:

            result = cur.execute("SELECT * FROM drivers ORDER BY created_at DESC")

            if result > 0:
                data = cur.fetchall()
            else:
                data = []
            print(data)

            return render_template('dashboard.html', data = data)
        else:
        
            result = cur.execute("SELECT record.*, users.email FROM record INNER JOIN users ON users.id = record.passenger_id WHERE passenger_id = %s OR driver_id = %s ORDER BY created_at DESC", [user_id, user_id])

            if result > 0:
                data = cur.fetchall()
            else:
                data = []
            print(data)

            return render_template('dashboard.html', data = data)

@app.route("/process-request", methods = ['GET', 'POST'])
@is_logged_in
def processReq():
    if request.method == 'GET':
        status = request.args['order']
        record_id = request.args['i']
        user_id = session['user_id']

        print(status)
        print(record_id)
        cur = mysql.get_db().cursor()

        cur.execute( "UPDATE record SET status = %s WHERE id = %s ", [status, record_id])

        mysql.get_db().commit()

        return  redirect('/dashboard')


        # result = cur.execute("SELECT * FROM record INNER JOIN users ON users.id = record.passenger_id  WHERE passenger_id = %s OR driver_id = %s ORDER BY created_at DESC", [user_id, user_id])

        # if result > 0:
        #     data = cur.fetchall()
        # else:
        #     data = []
        # print(data)

        # return render_template('dashboard.html', data = data)

@app.route("/rating", methods = ['GET', 'POST'])
@is_logged_in
def rating():
    if request.method == 'GET':

        user_id = session['user_id']
        record_id = request.args['r_id']
        driver_id = request.args['d_id']

        cur = mysql.get_db().cursor()

        result = cur.execute("SELECT record.*, users.email FROM record INNER JOIN users ON users.id = record.driver_id WHERE driver_id = %s AND record.id = %s", [driver_id, record_id])

        if result > 0:
            data = cur.fetchone()
        else:
            data = []
        print(data)

        return render_template('rating.html', data = data)
    if request.method == 'POST':

        rating = request.form['rating']
        record_id = request.form['record_no']

        cur = mysql.get_db().cursor()

        cur.execute( "UPDATE record SET rating = %s WHERE id = %s ", [rating, record_id])

        mysql.get_db().commit()

        return redirect('/dashboard')


@app.route("/reset-password", methods=['GET', 'POST'])
@is_logged_in
def resetPassword():
    if request.method == 'POST':
        oldPassword = request.form['old-password']
        newPassword = request.form['new-password']
        newPassword2 = request.form['new-password2']
        email = session['email']

        cur = mysql.get_db().cursor()

        result = cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", [email, oldPassword])

        if result > 0:

            if newPassword == newPassword2: 

                cur.execute( "UPDATE users SET password = %s WHERE email = %s ", [newPassword, email])

                mysql.get_db().commit()

                msg = "Your password has been changed"

                return render_template('settings.html', msg=msg)
            else:
                msg = "New password doesn't match"

                return render_template('settings.html', msg=msg)
        else:
            msg = "Your original password is invalid, please try again" 
            return render_template('settings.html', msg = msg)

@app.route("/settings")
@is_logged_in
def settings():

    return render_template('settings.html')


@app.route("/del-record", methods=['GET', 'POST'])
@is_logged_in
def delRecord():
    if request.method == 'GET':
        record_id = request.args['i']
        print(record_id)

        cur = mysql.get_db().cursor()

        cur.execute( "DELETE FROM drivers WHERE id = %s ", [record_id])

        mysql.get_db().commit()

        return redirect('/dashboard')

# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'],
#                                filename)

# @app.route('/', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         # if user does not select file, browser also
#         # submit an empty part without filename
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):        
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('uploaded_file',
#                                     filename=filename))
#     return '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#     <form method=post enctype=multipart/form-data>
#       <input type=file name=file>
#       <input type=submit value=Upload>
#     </form>
#     '''
@app.route("/poll-data", methods=['GET', 'POST'])
def pollData():

    if request.method == 'GET':

        cur = mysql.get_db().cursor()

        result = cur.execute("SELECT * FROM `drivers` ORDER BY created_at DESC LIMIT 6")

        if result > 0:
            data = cur.fetchall()
            return jsonify({'data': data});
    else:
        return render_template('index.html')

@app.route("/qrcode-apply", methods=['GET', 'POST'])
@is_logged_in
def qrcodeApply():
    if request.method == 'GET':
        car_id = request.args['car_id'] 
        enroll_day = request.args['enroll_day']

        user_id = session['user_id']

        cur = mysql.get_db().cursor()

        cur.execute("INSERT INTO record (driver_id, passenger_id, enroll_day) VALUES (%s, %s, %s)", [car_id, user_id, int(enroll_day)])
        
        mysql.get_db().commit()

        # return jsonify({'data': "success"});
        return redirect('/dashboard')




@app.route("/enroll", methods=['GET', 'POST'])
@is_logged_in
def enroll():
    if request.method == 'GET':
        print('-----=====--=-=')
        # get params
        car_id = request.args['car_id']

        cur = mysql.get_db().cursor()

        result = cur.execute("SELECT * FROM drivers WHERE id = %s LIMIT 1", [car_id])

        # if result > 0:
        data = cur.fetchone()

        rating_count = cur.execute("SELECT AVG(rating) FROM record WHERE driver_id = %s", [car_id])
        
        if rating_count > 0:
            temp = cur.fetchone()
            if temp[0]:
                rating_amount = temp[0]
            else:
                rating_amount =  1




        record = cur.execute("SELECT * FROM record WHERE driver_id = %s  AND passenger_id = %s AND status = 1 LIMIT 1", [car_id, session['user_id']])
        if record > 0:
            check = True
        else:
            check = False
        print(check)
        return render_template('enroll.html', data=data, check = check, rating_amount=rating_amount)

    if request.method == 'POST':
        car_id = request.form['car_id'] 
        enroll_day = request.form['enroll_day']

        user_id = session['user_id']

        cur = mysql.get_db().cursor()

        cur.execute("INSERT INTO record (driver_id, passenger_id, enroll_day) VALUES (%s, %s, %s)", [car_id, user_id, int(enroll_day)])
        
        mysql.get_db().commit()

        return jsonify({'data': "success"});

@app.route("/stepdriver", methods=['GET', 'POST'])
def stepdriver():

    return render_template('stepdriver.html');

@app.route("/steppassengers", methods=['GET', 'POST'])
def steppassengers():

    return render_template('steppassengers.html');

@app.route("/orders", methods=['GET', 'POST'])
def orders():
    if request.method == 'GET':

        cur = mysql.get_db().cursor()

        result = cur.execute("SELECT * FROM `drivers` LEFT JOIN  districts ON districts.id = drivers.district_id  ORDER BY created_at DESC")

        if result > 0:
            data = cur.fetchall()

        else:
            data = []
        print(data)
        return render_template('orders.html', data = data);
   

if __name__ == '__main__':
    app.secret_key='car_to_go'
    app.run("0.0.0.0", debug = True)



