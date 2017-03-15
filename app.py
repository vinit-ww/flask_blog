from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from forms import MyForm, LoginForm, RegisterForm, CommentForm
from flask_login import login_user, logout_user, UserMixin, LoginManager, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_bootstrap import Bootstrap
from werkzeug import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/posten'
app.config['UPLOAD_FOLDER'] = 'upload/'
app.secret_key = 's3cr3t'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

migrate = Migrate(app, db)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(10))
    email = db.Column(db.String(50), unique=True, index=True)
    picture = db.Column(db.String(255))
    posts = db.relationship('Post', backref='user', lazy="dynamic")
    comments = db.relationship('Comment', backref='user', lazy="dynamic")
    def __init__(self, password, email):
        self.password = password
        self.email = email


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(40), unique=True)
    title = db.Column(db.String(255), unique=True)
    content = db.Column(db.String(255), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Defining one to many relationship
    comments = db.relationship('Comment', backref="post", lazy="dynamic")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/posts', methods=['GET', 'POST'])
@login_required
def posts():
    form = MyForm()
    if request.method == 'POST':
        post = Post(title=form.title.data,
                    author=form.author.data,
                    content=form.content.data)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('posts'))
    else:
        posts = Post.query.all()
        return render_template('post_list.html', posts=posts)

@app.route('/post/<post_id>')
def show_post(post_id):
    post = Post.query.get(post_id)
    comment_form = CommentForm()
    return render_template('show_post.html', form=comment_form, post=post)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        file = request.files['file']

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_user.picture = filename
        db.session.add(current_user)
        db.session.commit()

        flash('File Uploaded successfully')
        return redirect(url_for('posts'))
    else:
        return render_template('upload.html')

@app.route('/post/new', methods=['GET'])
def new_post():
    form = MyForm()
    return render_template('post_form.html', form=form, url="/posts")


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/post/<post_id>/edit', methods=['GET'])
@login_required
def edit_post(post_id):
    post = Post.query.get(post_id)
    form = MyForm(obj=post)
    return render_template('post_form.html', form=form, url="/post/" + post_id + "/update")

@app.route('/post/<post_id>/update', methods=['POST'])
@login_required
def update_post(post_id):

    post = Post.query.get(post_id)
    form = MyForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.author = form.author.data
        post.content = form.content.data
        post.user_id = current_user.id
        db.session.add(post)
        db.session.commit()
        flash('Post is updated!')
        return redirect(url_for('posts'))
    else:
        return redirect(url_for('posts'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', form=login_form)
    if login_form.validate_on_submit():
        reg_user = User.query.filter_by(email=login_form.email.data,
                                        password=login_form.password.data).first()
        if reg_user is None:
            flash('Username or password is Invalid', 'error')
            return redirect(url_for('login'))
        login_user(reg_user)
        flash('Logged in successfully')
        return redirect(url_for('posts'))

@app.route('/post/<post_id>/delete')
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post has been delete successfully!!')
    return redirect(url_for('posts'))

@app.route('/post/<post_id>/comment', methods=['POST'])
def add_comment(post_id):
    post = Post.query.get(post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        comment = Comment(content=comment_form.content.data,
                          user_id=current_user.id,
                          post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        url = url_for('show_post', post_id=post.id)
        return redirect(url)


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if request.method == 'GET':
        return render_template('register.html', form=register_form)
    if register_form.validate_on_submit():
        register = User(email=register_form.email.data,
                        password=register_form.password.data)
        db.session.add(register)
        db.session.commit()
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('new_post'))

# Run the app
if __name__ == "__main__":
    app.run(debug=True)