from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import boto3, MySQLdb.cursors, os
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

s3 = boto3.client('s3',
                    aws_access_key_id= os.getenv('AWS_ACCESS_KEY'),
                    aws_secret_access_key= os.getenv('AWS_SECRET_KEY')
                     )
bucket_name = os.getenv('BUCKET_NAME')

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return render_template('user.html')
        else:
            msg = 'Incorrect username or password'

    return render_template('index.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        img = request.files['file']
        if img:
            filename = secure_filename(img.filename)
            img.save(filename)
            s3.upload_file(
                Bucket = bucket_name,
                Filename = filename,
                Key = filename
            )
            msg = "Upload Done !"
    return render_template("user.html",msg=msg)

@app.route('/dbusers', methods=['POST'])
def userdb():
    cur = mysql.connection.cursor()
    cur.execute('SELECT firstname, lastname FROM users')
    userslist = []
    for (firstname, lastname) in cur:
        row = str(f'{firstname} {lastname}')
        userslist.append(row)
    cur.close()

    return render_template('user.html', data=userslist)

if __name__ == "__main__":

    app.run(debug=True)