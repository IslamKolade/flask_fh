import os
import pathlib
from flask import Flask, redirect, render_template, flash, request, url_for
from werkzeug.utils import secure_filename
import uuid as uuid

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user


from forms import SignInForm, SignUpForm, UpdateForm, PostForm, SearchForm, EditPostForm


#Create a flask instance
app = Flask(__name__)
#SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///FootballHouse.db'

#POSTGRES DATABASE
#app.config['SQLALCHEMY_DATABASE_URI'] = ('postgres://ienbtdonqdopui:39face1b3665e16811b0408cb4200785f4bdfa2bcfed10b10c95b78fe8a1d853@ec2-3-218-171-44.compute-1.amazonaws.com:5432/db22tu20hnjves').replace("://", "ql://", 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'nonsense'
UPLOAD_FOLDER = 'static/Uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
UPLOADVID_FOLDER = os.path.join(pathlib.Path().absolute(), 'static\\Uploads')
app.config['UPLOADVID_FOLDER'] = UPLOADVID_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
#MYSQL Database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Kolade16@localhost/footballhouse_users'
#Secret Key
#app.config['SECRET_KEY'] = 'gfgrytyujggfff'
#Initialize Database
db = SQLAlchemy(app)
migrate = Migrate(app,db)



#Flask Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'SignIn'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#Pass Form to Nav Bar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)



#Search function
@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        #Get data from submitted form
        postsearched = form.searched.data
        #Query the database
        posts = posts.filter(Posts.content.like('%' + postsearched + '%'))
        posts = posts.order_by(Posts.topics).all()
        return render_template('search.html', form=form, searched = postsearched, posts = posts) 




@app.route('/SignIn', methods = ['GET', 'POST'])
def SignIn():
    form = SignInForm()
    #Validate Form
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            #Check the hashed password
            if check_password_hash(user.password_hash, form.password_hash.data):
                login_user(user)
                flash('Login Successful')
                return redirect(url_for('home'))
            else:
                flash('Incorrect Password, try again.')
        else:
            flash('Email does not exist.')
    return render_template('SignIn.html', form = form)

#LogOut
@app.route('/LogOut', methods = ['GET', 'POST'])
@login_required
def LogOut():
    logout_user()
    flash('Log out successful')
    return redirect(url_for('home'))



#Profile
@app.route('/Profile', methods = ['GET', 'POST'])
@login_required
def Profile():
    return render_template('Profile.html')


@app.route('/SignUp', methods = ['GET', 'POST'])
def SignUp():
    form = SignUpForm()
    #Validate Form
    if form.validate_on_submit():
        user = Users.query.filter_by(email = form.email.data).first()
        if user is None:
            #Hash Password
            hashed_pw = generate_password_hash(form.password_hash.data, 'sha256')
            user = Users(email = form.email.data, 
            first_name = form.first_name.data,
            last_name = form.last_name.data,
            username = form.username.data,
            about= form.about.data,
            password_hash = hashed_pw)
            db.session.add(user)
            db.session.commit()
            form.email.data = ''
            form.first_name.data = ''
            form.last_name.data = ''
            form.username.data = ''
            form.about.data = ''
            form.password_hash.data = ''
            flash('User added successfully, now sign in to Football House.')
            return redirect (url_for('SignIn'))
        else:
            flash("An account already exists with this email address, sign in here " '<a href="SignIn" style="color: blue;">Sign In</a>')
    my_users = Users.query.order_by(Users.date_joined)
    return render_template('SignUp.html', form = form, my_users = my_users)






#Update Database Records
@app.route('/update/<int:id>', methods = ['GET', 'POST'])
@login_required
def update(id):
    form = UpdateForm()
    username_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        username_to_update.email = request.form['email']
        username_to_update.first_name = request.form['first_name']
        username_to_update.last_name = request.form['last_name']
        username_to_update.username = request.form['username']
        username_to_update.about = request.form['about']

        #Check for Profile Picture
        if request.files['profile_pic']:
            username_to_update.profile_pic = request.files['profile_pic']
            #Take Image
            pic_filename = secure_filename(username_to_update.profile_pic.filename)
            #Set UUID to change profile pic name to random to avoid duplication.
            pic_name = str(uuid.uuid1()) + '' + pic_filename
            #Save Image
            saver = request.files['profile_pic']
            #Convert Image to string to save to database
            username_to_update.profile_pic = pic_name

            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                flash('User Updated Successfully')
                return redirect (url_for('Profile', form = form, username_to_update = username_to_update))
            except:
                flash('Error, looks like there was a problem. Try again!!')
                return redirect (url_for('Profile', form = form, username_to_update = username_to_update))
        else:
            db.session.commit()
            flash('User Updated Successfully')
            return redirect (url_for('Profile', form = form, username_to_update = username_to_update))
    else:
        return render_template('update.html', form = form, username_to_update = username_to_update)

#Delete Database Records
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if id == current_user.id or current_user.id == 1:
        form = SignUpForm()
        user_to_delete = Users.query.get_or_404(id)
        first_name = None
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('Account Deleted')
            my_users = Users.query.order_by(Users.date_joined)
            return redirect(url_for('SignUp', first_name = first_name, form = form, my_users = my_users))
        except:
            flash('Whoops! There was a problem deleting this user.')
            return redirect(url_for('SignUp', first_name = first_name, form = form, my_users = my_users))
    else:
        flash("Access Denied")
        posts = Posts.query.order_by(Posts.date_posted)
        return redirect(url_for('home', posts = posts))

#Routes
@app.route('/', methods = ['GET', 'POST'])
def home():
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template('index.html', posts = posts)

#Admin Page
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 1:
        my_users = Users.query.order_by(Users.date_joined)
        return render_template('admin.html', my_users = my_users)
    else:
        flash('Access Denied!')
        return redirect(url_for('Profile'))



#Delete Posts
@app.route('/post/delete/<int:id>')
@login_required
def delete_post(id):
    delete_post = Posts.query.get_or_404(id)
    id = current_user.id
    if id == delete_post.poster.id or current_user.id == 1:
        try:
            db.session.delete(delete_post)
            db.session.commit()
            flash('Post Deleted Successfully')
            posts = Posts.query.order_by(Posts.date_posted)
            return redirect(url_for('home', posts = posts))
        except:
            flash('Oops, there was a problem deleting post. Try again')
            return redirect(url_for('home'))
    else:
        flash("You aren't authorized to delete that post")
        posts = Posts.query.order_by(Posts.date_posted)
        return redirect(url_for('home', posts = posts))

        



#Edit  Image Posts
@app.route('/post/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_post(id):
    edit_post = Posts.query.get_or_404(id)
    form = EditPostForm()
    if request.method == 'POST':
        edit_post.content = request.form['content']
        db.session.commit()
        flash('Post Edited Successfully')
        fullpost = Posts.query.get_or_404(id)
        return redirect (url_for('fullpost', id = fullpost.id))
    else:
        if current_user.id == edit_post.poster_id or current_user.id == 1:
            return render_template('edit_post.html', edit_post = edit_post, form = form)
        else:
            flash("You aren't authorized to edit this post")
            fullpost = Posts.query.get_or_404(id)
            return redirect(url_for('fullpost', id = fullpost.id))


#Full Post
@app.route('/fullpost/<int:id>')
def fullpost(id):
    fullpost = Posts.query.get_or_404(id)
    return render_template('fullpost.html', fullpost = fullpost)

#Choose Post Type
@app.route('/post-type')
def post_type():
    return render_template('post_type.html')

#Add Post Page
@app.route('/add-post', methods=['GET','POST'])
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        topics = request.form['topics']
        #Check for Post Picture
        if request.files['post_pic']:
            post_pic = request.files['post_pic']
            #Take Image
            pic_filename = secure_filename(post_pic.filename)
            #Set UUID to change post pic name to random to avoid duplication.
            pic_name = str(uuid.uuid1()) + '' + pic_filename
            #Save Image
            savepic = request.files['post_pic']
            #Convert Image to string to save to database
            post_pic = pic_name
            poster = current_user.id
            post = Posts(topics=topics, content=form.content.data, poster_id=poster, post_pic=post_pic)
            #Clear the Form
            topics=topics = ''
            content=form.content.data = ''
            #Add post data to database
            db.session.add(post)
            db.session.commit()
            savepic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            flash('Posted Successfully')
            return redirect(url_for('home'))
        else:
            poster = current_user.id
            post = Posts(topics=topics, content=form.content.data, poster_id=poster)
            #Clear the Form
            topics=topics = ''
            content=form.content.data = ''
            #Add post data to database
            db.session.add(post)
            db.session.commit()
            flash('Posted Successfully')
            return redirect(url_for('home'))
    return render_template('add_post.html', form = form)


#Add Video Post Page
@app.route('/addvid-post', methods=['GET','POST'])
def add_vidpost():
    form = PostForm()
    if form.validate_on_submit():
        topics = request.form['topics']
        #Check for Post Picture
        if request.files['post_vid']:
            post_vid = request.files['post_vid']
            #Take Image
            vid_filename = secure_filename(post_vid.filename)
            #Set UUID to change post pic name to random to avoid duplication.
            vid_name = str(uuid.uuid1()) + '' + vid_filename
            #Save Image
            savevid = request.files['post_vid']
            #Convert Image to string to save to database
            post_vid = vid_name
            poster = current_user.id
            post = Posts(topics=topics, content=form.content.data, poster_id=poster, post_vid=post_vid)
            #Clear the Form
            topics=topics = ''
            content=form.content.data = ''
            #Add post data to database
            db.session.add(post)
            db.session.commit()
            savevid.save(os.path.join(app.config['UPLOAD_FOLDER'], vid_name))
            flash('Posted Successfully')
            return redirect(url_for('home'))
        else:
            poster = current_user.id
            post = Posts(topics=topics, content=form.content.data, poster_id=poster)
            #Clear the Form
            topics=topics = ''
            content=form.content.data = ''
            #Add post data to database
            db.session.add(post)
            db.session.commit()
            flash('Posted Successfully')
            return redirect(url_for('home'))
    return render_template('addvid_post.html', form = form)

#Add Audio Post Page
@app.route('/addaud-post', methods=['GET','POST'])
def add_audpost():
    form = PostForm()
    if form.validate_on_submit():
        topics = request.form['topics']
        #Check for Post Picture
        if request.files['post_aud']:
            post_aud = request.files['post_aud']
            #Take Image
            aud_filename = secure_filename(post_aud.filename)
            #Set UUID to change post pic name to random to avoid duplication.
            aud_name = str(uuid.uuid1()) + '' + aud_filename
            #Save Image
            saveaud = request.files['post_aud']
            #Convert Image to string to save to database
            post_aud = aud_name
            poster = current_user.id
            post = Posts(topics=topics, content=form.content.data, poster_id=poster, post_aud=post_aud)
            #Clear the Form
            topics=topics = ''
            content=form.content.data = ''
            #Add post data to database
            db.session.add(post)
            db.session.commit()
            saveaud.save(os.path.join(app.config['UPLOAD_FOLDER'], aud_name))
            flash('Posted Successfully')
            return redirect(url_for('home'))
        else:
            poster = current_user.id
            post = Posts(topics=topics, content=form.content.data, poster_id=poster)
            #Clear the Form
            topics=topics = ''
            content=form.content.data = ''
            #Add post data to database
            db.session.add(post)
            db.session.commit()
            flash('Posted Successfully')
            return redirect(url_for('home'))
    return render_template('addaud_post.html', form = form)




#Add Text Post Page
@app.route('/addtext-post', methods=['GET','POST'])
def add_textpost():
    form = PostForm()
    if form.validate_on_submit():
        topics = request.form['topics']
        poster = current_user.id
        post = Posts(topics=topics, content=form.content.data, poster_id=poster)
        #Clear the Form
        topics=topics = ''
        content=form.content.data = ''
        #Add post data to database
        db.session.add(post)
        db.session.commit()
        flash('Posted Successfully')
        return redirect(url_for('home'))
    return render_template('addtext_post.html', form = form)
    








#Custom Error Message
#Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#Internal error
@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 404


#Models
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, index=True)
    email = db.Column(db.String(500), unique=True)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(600), nullable=False, unique=True)
    about = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(400), nullable=True)
    date_joined = db.Column(db.Date, default=datetime.now())
    #Password
    password_hash = db.Column(db.String(400))

    #A User can have many posts
    posts = db.relationship('Posts', backref = 'poster')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    #string
    def __repr__(self) -> str:
        return '< User: %r>'% self.first_name


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topics = db.Column(db.String(400))
    content = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default= datetime.utcnow)
    post_pic = db.Column(db.String(400))
    post_vid = db.Column(db.String(400))
    post_aud = db.Column(db.String(400))
    # Foreign Key to Link Users (Going to refer to the primary key of the User)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))