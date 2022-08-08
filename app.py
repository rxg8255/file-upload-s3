from datetime import datetime
import os
import mysql.connector
import re
import sqlite3
import boto3
from flask import Flask, flash, request, redirect, url_for, session, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'C:/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ACCESS_KEY = 'AKIA6HXBWCEHYQZNFC7I'
SECRET_KEY = '9R2D0h4R7JfR9EJLXZWk+1FxTSoMilqbN3Hy1hYv'
DB = "6632808"

app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = '{}' AND password ='{}'".format(email, password))
        account = cur.fetchone()
        print(account)
        if account:
            session['loggedin'] = True
            session['username'] = account[2]
            session['email'] = account[0]
            msg = 'Logged in successfully !'
            return redirect(url_for('upload_file'))
        else:
            msg = 'Incorrect email / password !'
            return render_template('login.html', msg=msg)
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('type', None)
    return redirect(url_for('login'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    msg = ''
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email ='{}'".format(email))
        account = cur.fetchone()
        if account:
            msg = 'Account already exists'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address'
        elif not firstname or not lastname or not password or not email:
            msg = 'Please fill all details'
        else:
            cur.execute("INSERT INTO users(firstname, lastname, email, password) "
                        "VALUES ('{}', '{}', '{}', '{}')"
                        .format(firstname, lastname, email, password))
            conn.commit()
            msg = 'You have successfully registered !'
            return render_template('login.html', msg=msg)
    elif request.method == 'POST':
        msg = 'Please fill all details'
    return render_template('register.html', msg=msg)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    try:
        if not session['loggedin']:
            msg = 'Please login!'
            return render_template('login.html', msg=msg)
        else:
            if request.method == 'POST':
                if 'file' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                file = request.files['file']
                email = request.form['email']
                if len(email.split(',')) > 5:
                    msg = 'Email ids exceeded more than 5'
                    return render_template('file_upload.html', msg=msg)
                elif not email:
                    msg = "Please enter recepient email id"
                    return render_template('file_upload.html', msg=msg)
                elif file.filename == '':
                    flash('No selected file')
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    s3 = boto3.client("s3",
                                      aws_access_key_id=ACCESS_KEY,
                                      aws_secret_access_key=SECRET_KEY)
                    bucket_name = "6632808"
                    fullpath = os.path.join(UPLOAD_FOLDER, filename)
                    res = db_opeartions(filename, bucket_name, email)
                    response = s3.upload_file(fullpath, bucket_name, filename)
                    print(response)
                    return render_template('file_upload.html', msg=res)
            return render_template('file_upload.html')
    except Exception as e:
        print(e)
        msg = 'Please login!'
        return render_template('login.html', msg=msg)

def db_opeartions(filename, bucket_name, email):
    ENDPOINT = "s3-file-upload.cevyuammehpq.us-east-2.rds.amazonaws.com"
    PORT = "3306"
    USER = "admin"
    REGION = "us-east-2"
    DBNAME = "s3_files_info"
    os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'
    token = "Chinnu123"

    file_url = "https://{}.s3.amazonaws.com/{}".format(bucket_name, filename)
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = mysql.connector.connect(host=ENDPOINT, user=USER,
                                       passwd=token, port=PORT, database=DBNAME,
                                       ssl_ca='SSLCERTIFICATE')
        cur = conn.cursor()
        cur.execute("INSERT INTO `s3_files_info`.`file_info` (`filename`,`fileurl`, `time_stamp`) "
                    "VALUES ('{}', '{}', '{}')".format(filename, file_url, date_time))
        conn.commit()
        cur.execute("SELECT id FROM `s3_files_info`.`file_info` where filename='{}' "
                    "and fileurl='{}' and time_stamp='{}'".format(filename,file_url, date_time))
        fileinfo = cur.fetchone()
        print(fileinfo)
        if fileinfo:
            email_arr = email.split(',')
            for em in email_arr:
                cur.execute("INSERT INTO `s3_files_info`.`file_email_map` (`fileid`,`email`) "
                        "VALUES ('{}', '{}')".format(fileinfo[0], em))
            conn.commit()
        return "File uploaded successfully"
    except Exception as e:
        print(e)
        return "Database connection failed"

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)

