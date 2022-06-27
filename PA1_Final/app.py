######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
from datetime import date

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'neeraja502'
app.config['MYSQL_DATABASE_DB'] = 'myphotoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

'''
 @login_manager.request_loader
 def request_loader(request):
 	users = getUserList()
 	email = request.form.get('email')
 	if not(email) or email not in str(users):
 		return
 	user = User()
 	user.id = email
 	cursor = mysql.connect().cursor()
 	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
 	data = cursor.fetchall()
 	pwd = str(data[0][0] )
 	user.is_authenticated = request.form['password'] == pwd
 	return user
	'''

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	cursor = conn.cursor()
	email = request.form.get('email')
	test = UniqueEmail(email)
	password = request.form.get('password')
	if email == '' or password == '':
		print("couldn't find all tokens")
		return render_template('register.html', all_vals='False')

	first_name = request.form.get('first_name')
	last_name = request.form.get('last_name')
	if first_name == '' or last_name == '':
		print("couldn't find all tokens")
		return render_template('register.html', all_vals='False')


	dob = request.form.get('dob')
	gender=request.form.get('gender')
	hometown=request.form.get('hometown')
	
	if dob == '' or gender == '' or hometown == '':
		print("couldn't find all tokens")
		return render_template('register.html', all_vals='False')
	
	if test:
		insertSQLString = "INSERT INTO Users (email, password, first_name,last_name, birth_date ,gender, hometown) VALUES "
		insertSQLPositions = "('{0}', '{1}', '{2}', '{3}', '{4}','{5}','{6}')"
		print(cursor.execute((insertSQLString+insertSQLPositions).format(email,password,first_name,last_name,dob,gender,hometown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=first_name+" "+last_name, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return render_template('register.html', supress='False')

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def UniqueEmail(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code


#################### PROFILE ##########################


@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	photos = getUsersPhotos(uid)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos = photos, base64 = base64)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def getAlbumID(uid, album_name):
	cursor = conn.cursor()
	SQLStatement = "Select albums_id From Albums Where user_id = '{0}' and name = '{1}'"
	cursor.execute(SQLStatement.format(uid,album_name))
	return cursor.fetchone()[0]

def DoesAlbumExists(uid, album_name):
	cursor = conn.cursor()
	SQLStatement = "Select * From Albums Where user_id = '{0}' and name = '{1}'"
	if cursor.execute(SQLStatement.format(uid,album_name)) == True:
		return True
	else:
		return False

def UniqueTag(tag):
	cursor = conn.cursor()
	SQLStatement = "Select * From Tags Where name = '{0}'"
	if cursor.execute(SQLStatement.format(tag)):
		return False
	else:
		return True

def addTagToDB(tag):
	cursor = conn.cursor()
	SQLStatement = "INSERT INTO Tags (name) VALUES ('{0}')"
	cursor.execute(SQLStatement.format(tag))
	conn.commit()

def getTagIDwithName(tag):
	cursor = conn.cursor()
	SQLStatement = "SELECT tag_id FROM Tags WHERE name = '{0}'"
	cursor.execute(SQLStatement.format(tag))
	#conn.commit()
	return cursor.fetchone()[0]

def getTagNamewithID(tag_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT name FROM Tags WHERE tag_id = '{0}' "
	cursor.execute(SQLStatement.format(tag_id))
	#conn.commit()
	return cursor.fetchone()[0]

def PhotoTagged(tag_id,photo_id):
	cursor = conn.cursor()
	SQLStatement = "INSERT INTO Tagged (tag_id,photo_id) VALUES ('{0}', '{1}')"
	cursor.execute(SQLStatement.format(tag_id,photo_id))
	conn.commit()


#################### UPLOAD ##########################
		
@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album_name = request.form.get('album')
		if not DoesAlbumExists(uid, album_name):
			return render_template('upload.html', DoesAlbumExists = 'False')	
		albums_id = getAlbumID(uid,album_name) 
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (data, user_id, caption,albums_id) VALUES (%s, %s, %s,%s )''' ,(photo_data,uid, caption,albums_id))
		cursor.execute("SELECT photo_id From photos Where caption = (%s) ", (caption))
		
		#assumption -> no same caption for multiple photos
	
		photo_id = cursor.fetchone()[0]
		#conn.commit()
		tags = request.form.get('tag')
		tags = tags.lower()
		tags = tags.split()
		
		for i in range(len(tags)):
			if UniqueTag(tags[i]):
				addTagToDB(tags[i])

		for i in range(len(tags)):
			tag_id = getTagIDwithName(tags[i])
			PhotoTagged(tag_id,photo_id)
		conn.commit()

		return render_template('hello.html', name=flask_login.current_user.id, message='Your photo has been uploaded!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code

def addFriendship(uid1,uid2):
	cursor = conn.cursor()
	SQLStatement = "INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}','{1}')"
	cursor.execute(SQLStatement.format(uid1,uid2))
	conn.commit()

def alreadyFriends(uid1,uid2):
	cursor = conn.cursor()
	SQLStatement = "Select * From Friends Where (user_id1 = '{0}' and user_id2 = '{1}') OR (user_id1 = '{1}' and user_id2 = '{0}')"
	if cursor.execute(SQLStatement.format(uid1,uid2)) == True:
		return True
	else:
		return False

def getUsersFriends(uid):
	cursor = conn.cursor()
	SQLStatement = "SELECT DISTINCT F.email FROM Friends, Users F, Users U WHERE U.user_id = '{0}' AND F.user_id != U.user_id and (U.user_id = Friends.user_id1 OR U.user_id = Friends.user_id2) and (F.user_id = Friends.user_id1 OR F.user_id = Friends.user_id2)"
	cursor.execute(SQLStatement.format(uid))
	return cursor.fetchall() 



#################### FRIENDS ##########################


@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
def friends():
	current_user_id = getUserIdFromEmail(flask_login.current_user.id)
	friends = getUsersFriends(current_user_id)
	if flask.request.method == 'GET':
		return render_template('friends.html', friends = friends)
	else:
	
		friend_email = request.form.get('email')

		if friend_email == flask_login.current_user.id:
			return render_template('friends.html', friends = friends, friend_self = 'True')
		
		
		if UniqueEmail(friend_email) == True:
			return render_template('friends.html', friends = friends, email_exists = 'False')
		
		friend_user_id = getUserIdFromEmail(friend_email)
		
		if alreadyFriends(current_user_id,friend_user_id) == True:
			return render_template('friends.html', friends = friends, already_friends = 'True')

		addFriendship(current_user_id, friend_user_id)
		
		return flask.redirect(flask.url_for('friends'))

def add_album(uid,album_name):
	today = date.today()
	cursor = conn.cursor()
	SQLStatement = "INSERT INTO Albums (user_id, date, name) VALUES ('{0}','{1}','{2}')"
	cursor.execute(SQLStatement.format(uid,today,album_name))
	conn.commit()

def getUsersAlbums(uid):
	cursor = conn.cursor()
	SQLStatement = "Select name, albums_id  From Albums Where user_id = '{0}'"
	cursor.execute(SQLStatement.format(uid))
	#conn.commit()
	return cursor.fetchall()

def getAlbumsPhotos(album_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT data, photo_id, caption, albums_id, user_id FROM Photos WHERE albums_id = '{0}'"
	cursor.execute(SQLStatement.format(album_id))
	#conn.commit()
	return cursor.fetchall() 

def getAlbumsPhotoIDS(album_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT photo_id FROM Photos WHERE albums_id = '{0}'"
	cursor.execute(SQLStatement.format(album_id))
	return cursor.fetchall() 

def getAlbumsName(album_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT name FROM Albums WHERE albums_id = '{0}'"
	cursor.execute(SQLStatement.format(album_id))
	return cursor.fetchall()


#################### ALBUMS ##########################

@app.route('/albums', methods=['GET', 'POST'])
@flask_login.login_required


def albums():
	current_user_id = getUserIdFromEmail(flask_login.current_user.id)
	albums = getUsersAlbums(current_user_id)
	if flask.request.method == 'GET':
		return render_template('albums.html', albums = albums)
	
	album_name = request.form.get('album')
	add_album(current_user_id,album_name)

	return flask.redirect(flask.url_for('albums'))

def deleteAlbum(album_id):
	photo_ids = getAlbumsPhotoIDS(album_id)
	cursor = conn.cursor()
	if(len(photo_ids) == 0):
		cursor.execute("DELETE FROM Albums WHERE albums_id = '{0}'".format(album_id))
	photo_ids = tupleToList(photo_ids)
	photo_ids = [x for inner in photo_ids for x in inner]
	photo_ids = tuple(photo_ids)
	if(len(photo_ids) == 1 ):
		cursor.execute("DELETE FROM Tagged WHERE photo_id = '{0}'".format(photo_ids[0]))
		cursor.execute("DELETE FROM Comments WHERE photo_id = '{0}'".format(photo_ids[0]))
		cursor.execute("DELETE FROM Likes WHERE photo_id = '{0}'".format(photo_ids[0]))
		cursor.execute("DELETE FROM Photos WHERE albums_id = '{0}'".format(album_id))
		cursor.execute("DELETE FROM Albums WHERE albums_id = '{0}'".format(album_id))
	if(len(photo_ids) > 1):
		cursor.execute("DELETE FROM Tagged WHERE photo_id IN {0}".format(photo_ids))
		cursor.execute("DELETE FROM Comments WHERE photo_id IN {0}".format(photo_ids))
		cursor.execute("DELETE FROM Likes WHERE photo_id IN {0}".format(photo_ids))
		cursor.execute("DELETE FROM Photos WHERE albums_id = '{0}'".format(album_id))
		cursor.execute("DELETE FROM Albums WHERE albums_id = '{0}'".format(album_id))
	conn.commit()


@app.route('/album/<album_id>', methods=['GET', 'POST'])
@flask_login.login_required
def album(album_id):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if flask.request.method == 'GET':
		album_name = getAlbumsName(album_id)
		photos = getAlbumsPhotos(album_id)
		photos = processPhotos(photos)
		photos = fixTags(photos)
		return render_template('album.html', photos = photos, album_name = album_name, base64 = base64)
	else:
		if 'delete' in request.form:
			deleteAlbum(album_id)
			albums = get_users_albums(uid)
			return render_template('albums.html', albums = albums)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (data, user_id, caption,albums_id) VALUES (%s, %s, %s,%s )''' ,(photo_data,uid, caption,album_id))
		cursor.execute("SELECT LAST_INSERT_ID()")
		photo_id = cursor.fetchone()[0]
		conn.commit()
		tags = request.form.get('tag')
		tags = tags.lower()
		tags = tags.split()
		
		for i in range(len(tags)):
			if UniqueTag(tags[i]):
				addTagToDB(tags[i])

		for i in range(len(tags)):
			tag_id = getTagIDwithName(tags[i])
			PhotoTagged(tag_id,photo_id)
		return flask.redirect(flask.url_for('album', album_id = album_id))



def album_name_from_id(albums_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT name FROM Albums WHERE albums_id = '{0}'"
	cursor.execute(SQLStatement.format(albums_id))
	return cursor.fetchone()[0]

def getEmailFromUserID(uid):
	cursor = conn.cursor()
	SQLStatement = "SELECT email  FROM Users WHERE user_id = '{0}'"
	cursor.execute(SQLStatement.format(uid))
	return cursor.fetchone()[0]

def processPhotos(photos):
	photos = list(photos) 
	for i in range(len(photos)):
		photos[i] = list(photos[i])
		tags = getPhotosTags(photos[i][1])
		photos[i].append(tags)
		photos[i][3] = album_name_from_id(photos[i][3])
		photos[i][4] = getEmailFromUserID(photos[i][4])
	return photos

def fixTags(photos):
	for i in range(len(photos)):
		if(len(photos[i][5]) > 0):
			for j in range(len(photos[i][5])):
				photos[i][5][j] = photos[i][5][j][1:]
			photos[i][5] = [x for inner in photos[i][5] for x in inner]
	return photos
		

#################### BROWSE ##########################


@app.route('/browse', methods=['GET', 'POST'])
def browse():
	cursor = conn.cursor()
	SQLStatement = "SELECT data, photo_id, caption, albums_id, user_id FROM Photos"
	cursor.execute(SQLStatement)
	photos = cursor.fetchall()
	if request.method == 'GET':
		photos = processPhotos(photos)
		photos = fixTags(photos)
		return render_template('browse.html', photos = photos, base64=base64)
	else:
		photos = processPhotos(photos)
		photos = fixTags(photos)
		return render_template('browse.html', photos = photos, base64=base64)

def likePhoto(user_id, photo_id):
	cursor = conn.cursor()
	SQLStatement = "INSERT INTO Likes (user_id, photo_id) VALUES ('{0}','{1}')"
	cursor.execute(SQLStatement.format(user_id, photo_id))
	conn.commit()


def getLikes(photo_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT user_id FROM Likes WHERE photo_id = '{0}'"
	cursor.execute(SQLStatement.format(photo_id))
	likes = list(cursor.fetchall())
	print(likes)
	for i in range(len(likes)):
		likes[i] = list(likes[i])
		likes[i][0] = getEmailFromUserID(likes[i][0])
		if(likes[i][0] == None):
			likes[i][0] = "Anonymous User"
	return likes

def alreadyLiked(user_id, photo_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT * FROM Likes WHERE user_id = '{0}' and photo_id = '{1}'"
	if cursor.execute(SQLStatement.format(user_id, photo_id)):
		return True
	else:
		return False

def commentPhoto(user_id, photo_id, comment):
	today = date.today()
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comments (user_id, photo_id, text, date) VALUES ('{0}','{1}', '{2}','{3}')".format(user_id, photo_id,comment,today))
	conn.commit()

def getComments(photo_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT user_id, text FROM Comments WHERE photo_id =  '{0}'"
	cursor.execute(SQLStatement.format(photo_id))
	comments = list(cursor.fetchall())
	for i in range(len(comments)):
		comments[i] = list(comments[i])
		comments[i][0] = getEmailFromUserID(comments[i][0])
		if(comments[i][0] == None):
			comments[i][0] = "Anonymous User"
	return comments

def getPhotoOwner(photo_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT user_id FROM Photos WHERE photo_id =  '{0}'"
	cursor.execute(SQLStatement.format(photo_id))
	return cursor.fetchone()[0]

def getPhotosTags(photo_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT tag_id FROM Tagged WHERE photo_id =  '{0}'"
	cursor.execute(SQLStatement.format(photo_id))
	tags = cursor.fetchall()
	tags = list(tags)
	if len(tags)>0:
		for i in range(len(tags)):
			tags[i] = list(tags[i])
			tags[i].append(getTagNamewithID(tags[i][0]))
		return tags
	else:
		return []

def deletePhoto(photo_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Likes WHERE photo_id = '{0}'".format(photo_id))
	cursor.execute("DELETE FROM Comments WHERE photo_id = '{0}'".format(photo_id))
	cursor.execute("DELETE FROM Tagged WHERE photo_id = '{0}'".format(photo_id))
	cursor.execute("DELETE FROM Photos WHERE photo_id = '{0}'".format(photo_id))
	conn.commit()



@app.route('/user_photo/<photo_id>', methods=['GET', 'POST'])
def user_photo(photo_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT data, photo_id, caption, albums_id, user_id FROM Photos WHERE photo_id = '{0}' "
	cursor.execute(SQLStatement.format(photo_id))
	photo = cursor.fetchone() 
	photo = list(photo)
	photo[3] = album_name_from_id(photo[3])
	photo[4] = getEmailFromUserID(photo[4])
	tags = getPhotosTags(photo[1])
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	likes = getLikes(photo_id)
	count = len(likes)
	comments = getComments(photo_id)
	if request.method == 'GET':
		return render_template('user_photo.html', photo = photo, base64=base64, likes = likes, count = count, comments = comments, tags = tags)
	else:
		if 'delete' in request.form:
			deletePhoto(photo_id)
			return render_template('hello.html', message='Welecome to Photoshare')
		if 'like' in request.form:
			if alreadyLiked(user_id, photo_id) == True:
				return render_template('user_photo.html', photo = photo, base64=base64, likes = likes, comments = comments, count = count, alreadyLiked = 'True', tags = tags)
			likePhoto(user_id, photo_id)
			return flask.redirect(flask.url_for('user_photo', photo_id = photo_id))

def getAnonymousID():
	cursor = conn.cursor()
	password = "password"
	SQLStatement = "INSERT INTO USERS (password) VALUES ('{0}')"
	cursor.execute(SQLStatement.format(password))
	cursor.execute("SELECT LAST_INSERT_ID()")
	user_id = cursor.fetchone()[0]
	conn.commit()
	return user_id


@app.route('/photo/<photo_id>', methods=['GET', 'POST'])
def photo(photo_id):
	cursor = conn.cursor()
	SQLStatement = "SELECT data, photo_id, caption, albums_id, user_id FROM Photos WHERE photo_id = '{0}' "
	cursor.execute(SQLStatement.format(photo_id))
	photo = cursor.fetchone() 
	photo = list(photo)
	photo[3] = album_name_from_id(photo[3])
	photo[4] = getEmailFromUserID(photo[4])
	tags = getPhotosTags(photo[1])
	if  flask_login.current_user.is_authenticated == True:
		user_id = getUserIdFromEmail(flask_login.current_user.id)
	likes = getLikes(photo_id)
	count = len(likes)
	comments = getComments(photo_id)
	if request.method == 'GET':
		return render_template('photo.html', photo = photo, base64=base64, likes = likes, count = count, comments = comments, tags = tags)
	else:
		if 'like' in request.form:
			if  flask_login.current_user.is_authenticated == True:
				if alreadyLiked(user_id, photo_id) == True:
					return render_template('photo.html', photo = photo, base64=base64, likes = likes, comments = comments, count = count, alreadyLiked = 'True', tags = tags)
				likePhoto(user_id, photo_id)
				return flask.redirect(flask.url_for('photo', photo_id = photo_id))
			else:
				anonLikeId = getAnonymousID()
				likePhoto(anonLikeId,photo_id)
				return flask.redirect(flask.url_for('photo', photo_id = photo_id))
		if 'comment' in request.form:
			comment = request.form.get('comment')
			if  flask_login.current_user.is_authenticated == True:
				if getPhotoOwner(photo_id) == user_id:
					return render_template('photo.html', photo = photo, base64=base64, likes = likes, comments = comments, count = count, sameUser = 'True', tags = tags)
				commentPhoto(user_id,photo_id,comment)
			else:
				anonCommentId = 13
				commentPhoto(anonCommentId,photo_id,comment)
			return flask.redirect(flask.url_for('photo', photo_id = photo_id))

def getPhotosofTagofUser(user_id,tag_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, Photos.photo_id, caption, albums_id, user_id FROM Photos, Tagged WHERE Tagged.photo_id = Photos.photo_id AND Tagged.tag_id  = '{0}' AND Photos.user_id = '{1}'".format(tag_id, user_id))
	return cursor.fetchall()


def getPhotoSearchTags(tags):
	for i in range(len(tags)):
		tags[i] = getTagIDwithName(tags[i])
	if (len(tags) > 1):
		tags = tuple(tags)
		print(tags)
		cursor = conn.cursor()
		cursor.execute("SELECT DISTINCT data, Photos.photo_id, caption, albums_id, user_id FROM Photos, Tagged WHERE Tagged.photo_id = Photos.photo_id AND Tagged.tag_id IN {0}".format(tags))
	else:
		cursor = conn.cursor()
		cursor.execute("SELECT DISTINCT data, Photos.photo_id, caption, albums_id, user_id FROM Photos, Tagged WHERE Tagged.photo_id = Photos.photo_id AND Tagged.tag_id = '{0}'".format(tags[0]))
	return cursor.fetchall()
	
def getPhotoSearchCaption(caption):
	print(caption)
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT data, photo_id, caption, albums_id, user_id FROM Photos WHERE caption = '{0}'".format(caption))
	return cursor.fetchall()
	

def getAllTagged(tag_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, Photos.photo_id, caption, albums_id, user_id FROM Photos, Tagged WHERE Tagged.photo_id = Photos.photo_id AND Tagged.tag_id  = '{0}'".format(tag_id))
	return cursor.fetchall()


@app.route('/tag/<tag_id>', methods=['GET', 'POST'])
def tags(tag_id):
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'GET':
		return render_template('tag.html')
	if 'your_photos' in request.form:
		photos = getPhotosofTagofUser(user_id, tag_id)
		photos = processPhotos(photos)
		photos = fixTags(photos)
		return render_template('tag.html', photos = photos, base64 = base64)
	if 'all_photos' in request.form:
		photos = getAllTagged(tag_id)
		photos = processPhotos(photos)
		photos = fixTags(photos)
		return render_template('tag.html', photos = photos, base64 = base64)

def getPopularTags():	
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM (Select tag_id, COUNT(tag_id) AS count FROM tagged GROUP BY tag_id) S WHERE S.count = (Select MAX(S1.count) FROM (Select tag_id, COUNT(tag_id) AS count FROM tagged GROUP BY tag_id) S1)")
	tags = cursor.fetchall()
	tags = tupleToList(tags)
	for i in range(len(tags)):
		tags[i].append(getTagNamewithID(tags[i][0]))
	return tags
	

@app.route('/popular_tags', methods=['GET', 'POST'])
def popular_tags():
	tags = getPopularTags()
	
	print(tags)
	return render_template('popular_tags.html', tags = tags)




@app.route('/photo_search', methods=['GET', 'POST'])
def photo_search():
	if request.method == 'GET':
		return render_template('photo_search.html')
	if request.method == 'POST':
		tags = request.form.get('search')
		tags = tags.split()
		photos = getPhotoSearchTags(tags)
		photos = processPhotos(photos)
		photos = fixTags(photos)
		return render_template('photo_search.html', photos = photos, base64 = base64)

@app.route('/photo_search_caption', methods=['GET', 'POST'])
def photo_search_by_caption():
	if request.method == 'GET':
		return render_template('photo_search_caption.html')
	if request.method == 'POST':
		caption = request.form.get('search')
		photos = getPhotoSearchCaption(caption)
		photos = processPhotos(photos)
		photos = fixTags(photos)
		return render_template('photo_search_caption.html', photos = photos, base64 = base64)

'''
def addToDict(ls,dict):
	for i in range(len(ls)):
		dict[ls[i][0]] += ls[i][1]
	return dict
'''


def tupleToList(x):
	x = list(x)
	for i in range(len(x)):
		x[i] = list(x[i])
	return x



'''
@app.route('/user_contributions', methods=['GET'])
def user_contribution():
	cursor = conn.cursor()
	cursor.execute("Select Comments.user_id, COUNT(comment_id) FROM Comments, Users WHERE Comments.user_id = Users.user_id and Users.email != '{0}' GROUP BY user_id".format(None))
	comment_count = cursor.fetchall()
	comment_count = tupleToList(comment_count)
	cursor = conn.cursor()
	cursor.execute("Select Photos.user_id, COUNT(Photos.photo_id) FROM Photos, Users WHERE Photos.user_id = Users.user_id and Users.email != '{0}'  GROUP BY user_id".format(None))
	photo_count = cursor.fetchall()
	photo_count = tupleToList(photo_count)
	cursor = conn.cursor()
	cursor.execute("Select Distinct Users.user_id from comments,photos,users WHERE (Users.user_id = comments.user_id OR Users.user_id = Photos.user_id) AND Users.email != '{0}'".format(None))
	users = cursor.fetchall()
	users = tupleToList(users)
	users = [x for inner in users for x in inner]
	users_emails = [getEmailFromUserID(x) for x in users]
	#users_emails = [x for x in users_emails if x != None]
	users = { i : 0 for i in users }
	users = addToDict(photo_count,users)
	users = addToDict(comment_count,users)
	users = dict(zip(users_emails, list(users.values()))) 
	#print(users)
	users = sorted(users.items(), key= lambda count :count[1], reverse=True)
	#users = list(users.items())
	if(len(users) > 10):
		users = users[:10]
	print(users)
	print(photo_count)
	print(comment_count)
	return render_template('user_contributions.html', users = users)

	'''
		
@app.route('/comment_search', methods=['GET', 'POST'])
def comment_search():
	if request.method == 'GET':
		return render_template('comment_search.html')
	else:
		text = request.form.get('search')
		users = getUsersOfComments(text)
		print(users)
		return render_template('comment_search.html', users = users)

def getUsersOfComments(text):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, count(comments.text) as count from Comments WHERE comments.text = '{0}' group by user_id ORDER BY count DESC".format(text))
	users = cursor.fetchall()
	users = tupleToList(users)
	for i in range(len(users)):
		users[i][0] = getEmailFromUserID(users[i][0])
		if(users[i][0] == None):
			users[i][0] = "Anonymous"
	return users

def getRecommendations(friends, user_id):
	cursor = conn.cursor()
	if(len(friends) > 1):
		cursor.execute("SELECT user_id1, count(user_id1) as count FROM ((SELECT user_id1 FROM Friends WHERE (user_id1 in {0}  or user_id2 in {0}) and user_id1 != '{1}' AND user_id2 != {1}) UNION ALL (SELECT user_id2 FROM Friends WHERE (user_id1 in {0}  or user_id2 in {0}) and user_id1 != '{1}' AND user_id2 != '{1}')) A where A.user_id1 NOT IN {0} GROUP by user_id1 ORDER BY count desc".format(friends,user_id))
	else:
		cursor.execute("SELECT user_id1, count(user_id1) as count FROM ((SELECT user_id1 FROM Friends WHERE (user_id1 = '{0}'  or user_id2 = '{0}') and user_id1 != '{1}' AND user_id2 != {1}) UNION ALL (SELECT user_id2 FROM Friends WHERE (user_id1 = '{0}'  or user_id2 = '{0}') and user_id1 != '{1}' AND user_id2 != '{1}')) A where A.user_id1 != '{0}' GROUP by user_id1 ORDER BY count desc".format(friends[0],user_id))
	return cursor.fetchall()

#################### FRIEND REC ##########################


@app.route('/friend_recommendation', methods=['GET'])
@flask_login.login_required
def friend_recommendation():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friends = getUsersFriends(uid)
	friends = tupleToList(friends)
	friends = [x for inner in friends for x in inner]
	friends = [getUserIdFromEmail(x) for x in friends]
	if len(friends) > 1:
		friends = tuple(friends)
	recommendations = getRecommendations(friends,uid)
	recommendations = tupleToList(recommendations)
	for i in range(len(recommendations)):
		recommendations[i][0] = getEmailFromUserID(recommendations[i][0])
	print(recommendations)
	return render_template('friend_recommendation.html', recommendations = recommendations)



def usersTopTags(uid):
	cursor = conn.cursor()
	cursor.execute("SElECT name FROM (SELECT Tagged.tag_id, COUNT(Tagged.tag_id) as count, Tags.name FROM Tagged, Photos, Tags WHERE Tags.tag_id = Tagged.tag_id and Photos.photo_id = Tagged.photo_id AND Photos.user_id = '{0}' GROUP BY tagged.tag_id ORDER BY count DESC LIMIT 5) S".format(uid))
	return cursor.fetchall()

def getAlsoLikeSearch(tags,uid):
	for i in range(len(tags)):
		tags[i] = getTagIDwithName(tags[i])
	if(len(tags) == 0):
		return 0
	if (len(tags) > 1):
		tags = tuple(tags)
		#print(tags)
		cursor = conn.cursor()
		cursor.execute("SELECT DISTINCT data, Photos.photo_id, caption, albums_id, user_id FROM Photos, Tagged WHERE Photos.user_id != '{1}' AND Tagged.photo_id = Photos.photo_id AND Tagged.tag_id IN {0}".format(tags, uid))
	else:
		cursor = conn.cursor()
		cursor.execute("SELECT DISTINCT data, Photos.photo_id, caption, albums_id, user_id FROM Photos, Tagged WHERE Photos.user_id != '{1}' AND Tagged.photo_id = Photos.photo_id AND Tagged.tag_id = '{0}'".format(tags[0],uid))
	return cursor.fetchall()

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
