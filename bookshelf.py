#imports
from __future__ import print_function # In python 2.7
import os
import sys
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
	  render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'bookshelf.db'),
	SECRET_KEY='development key',	
	email='admin',
	PASSWORD='default'
))
app.config.from_envvar('BOOKSHELF_SETTINGS', silent=True)

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

@app.cli.command('initdb')
def initdb_command():
	init_db()
	print ('Initialized the database.', file=sys.stderr)

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
	db = get_db()
	cur = db.execute('select title, description, author from books order by id desc')
	books = cur.fetchall()
	return render_template('show_books.html', books=books)


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



@app.route('/login', methods=['GET'])
def show_login():
	return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    error = None
    db = get_db()
    result = db.execute('select * from users where email=? and password=?', [request.form['email'], request.form['password']])
    cursor = result.fetchone()
    if cursor is None:
    	print ('Invalid email or password', file=sys.stderr)
    	error = 'Invalid email or password'
    	return render_template('login.html', error=error)

    print ('OK.', file=sys.stderr)
    session['logged_in'] = True 
    session['isAdmin'] = cursor['admin']
    return redirect(url_for('show_books'))
    # 

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
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

@app.route('/users/add', methods=['GET'])
def show_add_user():
	return render_template('add_user.html')

@app.route('/users/add', methods=['POST'])
def add_user():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	db.execute('insert into users (first_name, last_name, email, password, admin) values(?, ?, ?, ?, 0)', [request.form['first_name'], request.form['last_name'], request.form['email'], request.form['password']])
	db.commit()
	flash('New user added Successfully')
	return redirect(url_for('show_users'))

if __name__ == '__main__':
	if len(sys.argv)>1 and sys.argv [1]== 'initdb':
		init_db()
	app.run('0.0.0.0', 5000)