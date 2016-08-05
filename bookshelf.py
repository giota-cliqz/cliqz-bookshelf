#imports
from __future__ import print_function # In python 2.7
import os
import sys
import sqlite3
import datetime as dt
from datetime import datetime
import datetime
from datetime import timedelta
from flask import Flask, request, session, g, redirect, url_for, abort, \
	  render_template, flash, send_from_directory
from werkzeug.utils import secure_filename
from wtforms import Form, BooleanField, StringField, PasswordField, validators

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__, static_url_path='', static_folder='static')
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'bookshelf.db'),
	SECRET_KEY='development key',	
	email='admin',
	PASSWORD='default'
))
app.config.from_envvar('BOOKSHELF_SETTINGS', silent=True)

class LoginForm(Form):
	email = StringField('Email', [validators.input_required()])
	password = PasswordField('Password', [validators.DataRequired()])
class RegistrationForm(Form):
	first_name = StringField('Firstname', [validators.Length(min=4, max=25)])
	last_name = StringField('Lastname', [validators.Length(min=4, max=25)])
	email = StringField('Email Address', [validators.Length(min=6, max=35)])		
	password = PasswordField('Password', [validators.DataRequired()])

def connect_db():
	"""Connects to the database"""
	rv = sqlite3.connect(app.config['DATABASE'])
	rv.row_factory = sqlite3.Row
	return rv

def init_db():
	 with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

# @app.cli.command('initdb')
# def initdb_command():
# 	init_db()
# 	print ('Initialized the database.', file=sys.stderr)

def get_db():
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

@app.route('/')
def show_books():
	flash('show_books')
	dt  = datetime.datetime
	# count = dt.now()
	# dt(year=2011,month=05,day=05) - dt(year=count.year, month=count.month, day=count.day)

	db = get_db()
	cur = db.execute('select * from books order by id desc')
	books = cur.fetchall()
	books = map(dict,books)
	for book in books:
		cur = db.execute('select * from borrowed where book_id = ?', [book['id']])
		curBook = cur.fetchone()
		if curBook != None:
			
			now = dt.now()
			print (curBook['return_date'])
			# remaining_days = dt(curBook['return_date']) - dt(year=now.year, month=now.month, day=now.day)
			# book['return_date'] = remaining_days

	return render_template('show_books.html', books=books)

@app.route('/uploads/<filename>')
def send_file(filename):
  return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/borrow_book', methods=['GET','POST'])
def borrow_book():
	db = get_db()
	dt  = datetime.datetime
	now = dt.now()
	cur = db.execute('insert into borrowed (user_id, book_id,start_date,return_date) values (?, ?, ?, ?)', [request.form['user_id'], request.form['book_id'],now,now + timedelta(days=14)])
	db.commit()
	cur = db.execute('UPDATE books SET isborrowed = 1, user_id = ? where books.id=?',[request.form['user_id'],request.form['book_id']])
	db.commit()
	cur = db.execute('Select *, borrowed.user_id AS user_id, borrowed.book_id AS book_id from borrowed INNER JOIN users ON borrowed.user_id = users.id INNER JOIN books ON borrowed.book_id = books.id WHERE users.email=?', [session['email']])
	borrowed = cur.fetchall()
	return render_template('show_borrowed.html', borrowed=borrowed)

@app.route('/return_book', methods=['GET','POST'])
def return_book():
	db = get_db()
	cur = db.execute('DELETE FROM borrowed WHERE book_id=?', [request.form['book_id']])
	db.commit()
	cur = db.execute('UPDATE books SET isborrowed = 0 where books.id=?',[request.form['book_id']])
	db.commit()
	cur = db.execute('Select *, borrowed.user_id AS user_id, borrowed.book_id AS book_id from borrowed INNER JOIN users ON borrowed.user_id = users.id INNER JOIN books ON borrowed.book_id = books.id WHERE users.email=?', [session['email']])
	borrowed = cur.fetchall()
	if len(borrowed) == 0:
		cur = db.execute('select * from books order by id desc')
		books = cur.fetchall()
		return render_template('show_books.html',books=books)
	else:
		return render_template('show_borrowed.html', borrowed=borrowed)

@app.route('/add', methods=['GET'])
def show_add_book():
	return render_template('add_book.html')


@app.route('/add', methods=['POST'])
def add_book():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	db.execute('insert into books (title, description, author) values (?, ?, ?)', [request.form['title'], request.form['description'], request.form['author']])
	db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_books'))

@app.route('/borrowed')
def borrowed():
	flash('borrowed books')
	db = get_db()
	cur = db.execute('Select *, borrowed.user_id AS user_id, borrowed.book_id AS book_id from borrowed INNER JOIN users ON borrowed.user_id = users.id INNER JOIN books ON borrowed.book_id = books.id WHERE users.email=?', [session['email']])
	borrowed = cur.fetchall()
	return render_template('show_borrowed.html', borrowed=borrowed)


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm(request.form)
	if request.method =='POST':
	    error = None
	    print(form)
	    db = get_db()
	    result = db.execute('select * from users where email=? and password=?', [form.email.data, form.password.data])
	    cursor = result.fetchone()

	    if cursor is None or not form.validate():
	    	error = 'Invalid email or password'
	    	return render_template('login.html', error=error, form=form)

	    print ('OK.', file=sys.stderr)
	    session['logged_in'] = True 
	    session['isAdmin'] = cursor['admin']
	    session['email'] = cursor['email']
	    session['user_id'] = cursor['id']
	    return redirect(url_for('show_books'))
	return render_template('login.html', form=form)    
    # 

@app.route('/logout')
def logout():
		session.pop('logged_in', None)
		session.pop('isAdmin', None)
		session.pop('email', None)
		session.pop('user_id', None)
		flash('You were logged out')
		return redirect(url_for('show_books'))

@app.route('/users')
def show_users():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	cur = db.execute('select first_name, last_name, email from users order by id desc')
	users = cur.fetchall()
	return render_template('show_users.html', users=users)


@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
	form = RegistrationForm(request.form)
	if request.method == 'POST' and form.validate():
		print ('OK1.', file=sys.stderr) 
		if not session.get('logged_in'):
			abort(401)
		db = get_db()
		db.execute('insert into users (first_name, last_name, email, password, admin) values(?, ?, ?, ?, 0)', [form.first_name.data, form.last_name.data, form.email.data, form.password.data])
		db.commit()
		flash('New user added Successfully')
		print ('OK2.', file=sys.stderr)
		return redirect(url_for('show_users'))
	print ('OK3.', file=sys.stderr)	
	return render_template('add_user.html', form=form)


if __name__ == '__main__':
	if len(sys.argv)>1 and sys.argv [1]== 'initdb':
		init_db()
	app.run(host='0.0.0.0', port=8080)