from flask import Flask, render_template, request, redirect, session, flash
from connection import MySQLConnector
from flask_bcrypt import Bcrypt
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+.[a-zA-Z]*$')
import datetime

app = Flask(__name__)
mydb = MySQLConnector(app, "wall")
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    session['user'] = "Mike"
    return render_template('index.html')

@app.route('/login', methods = ['post'])
def login():
    print request.form
    query = "SELECT * FROM users where email = :email"
    data = {
        'email':request.form['email']
    }
    user = mydb.query_db(query,data) # [], [{}]
    if user and bcrypt.check_password_hash(user[0]['password'], request.form['email']):
        session['user_id'] = user[0]['id']
        session['user_name'] = user[0]['first_name']
        return redirect('/wall')
    pass

@app.route('/register', methods= ['post'])
def register():
    print request.form
    errors = {}
    if len(request.form['first_name']) < 2:
        errors['first_name'] = 'First name must be at least 2 letters'
    if len(request.form['last_name']) < 2:
        errors['last_name'] = 'Last name must be at least 2 letters'
    if request.form['password'] != request.form['confirm_password']:
        errors['matching'] = 'Passwords must match'
    if request.form['password'] < 6:
        errors['password_length'] = 'Password must be at least 6 letters'
    if not EMAIL_REGEX.match(request.form['email']):
        errors['email'] = 'Email must be valid'
    # preventing people from doing multiple registrations!
    query = "SELECT * FROM users where email = :email"
    data = {
        'email':request.form['email']
    }
    user = mydb.query_db(query,data)
    # print user
    # [] <-- nobody with that email, [{}] <-- someone already has that email
    if user: # since [] is falsey
        errors['email'] = 'Email must be valid'

    if not errors:
        password = bcrypt.generate_password_hash(request.form['password'])
        query = "INSERT into users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password,NOW(), NOW())"
        data = {
        'first_name' : request.form['first_name'],
        'last_name' : request.form['last_name'],
        'email' : request.form['email'],
        'password' : password
        }
        user = mydb.query_db(query, data)
        query2 = "SELECT id, first_name FROM users where id = :id"
        data  = {
            "id":user
            }
        user = mydb.query_db(query2, data)
        session['user_id'] = user[0]['id']
        session['user_name'] = user[0]['first_name']

    else:
        flash(errors)
        return redirect('/')
    return redirect('/wall')

@app.route('/logout')
def logout():
    session.clear()
    redirect('/')

@app.route('/wall')
def load_wall():
    query = "SELECT messages.message, messages.id as m_id, concat(users.first_name, ' ', users.last_name) as name, messages.created_at as m_at FROM messages LEFT JOIN users ON users.id = messages.user_id"
    messages = mydb.query_db(query)
    query2 = "SELECT comments.comment, comments.id, comments.created_at, comments.message_id, concat(users.first_name, ' ', users.last_name) as name FROM comments LEFT JOIN users on users.id = comments.user_id"
    comments = mydb.query_db(query2)
    return render_template('wall.html', messages = messages, comments = comments)

@app.route('/messages', methods = ['POST'])
def create_message():
    query = "INSERT INTO messages (message, user_id, created_at, updated_at) VALUES (:message, :user_id, NOW(),NOW())"
    data = {
        "message": request.form['message'],
        "user_id": session['user_id']
    }
    mydb.query_db(query,data)
    return redirect('/wall')

@app.route('/comments', methods = ['POST'])
def create_comment():
    query = "INSERT INTO comments (comment, user_id, message_id, created_at, updated_at) VALUES (:comment, :user_id, :message_id, NOW(),NOW())"
    data = {
        "comment": request.form['comment'],
        "user_id": session['user_id'],
        "message_id": request.form['m_id']
    }
    mydb.query_db(query,data)
    return redirect('/wall')


app.secret_key = 'my_secret_key'
if __name__ == '__main__':
  app.run(debug = True)
