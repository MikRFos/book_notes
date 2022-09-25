from flask import Flask, render_template, url_for, redirect, flash, request
from flask_ckeditor import CKEditor
from model import db, User, Book, Note, Quote, association_table
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import forms
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///book_notes.db")
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
    db.create_all()

ckeditor = CKEditor(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register_user():
    form = forms.RegistryForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            # User already Exists
            flash("Username Taken")
        else:
            if form.password.data == form.password_confirmation.data:
                hashed_salted_pass = generate_password_hash(form.password.data, salt_length=32)
                new_user = User(username=form.username.data, password=hashed_salted_pass)
                db.session.add(new_user)
                db.session.commit()

                login_user(new_user)

                return redirect(url_for("add_book"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("add_book"))
            flash("Incorrect Password")
            return redirect(url_for("login"))
        flash("Username Does Not Exist")
        return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/add_notes", methods=["GET", "POST"])
@login_required
def add_notes():
    form = forms.Notes()
    books = [book.title for book in current_user.books]
    form.book.choices = books
    if request.args:
        form.book.data = request.args["book"]
    if form.validate_on_submit():
        book_id = Book.query.filter_by(title=form.book.data).first().id
        notes = Note(chapter=form.chapter.data,
                     notes=form.notes.data,
                     user_id=current_user.id,
                     book_id=book_id)
        db.session.add(notes)
        db.session.commit()
        if form.quote1.data:
            new_quote = Quote(quote=form.quote1.data, speaker=form.quote1_speaker.data, page=form.quote1_page.data,
                              user_id=current_user.id, book_id=book_id, note_id=notes.id)
            db.session.add(new_quote)
            db.session.commit()
        return redirect(url_for("home"))
    return render_template("add_notes.html", form=form)


@app.route("/show_notes/<username>/<book_title>/<id>")
def show_notes(username, book_title, id):
    note_user = User.query.filter_by(username=username).first()
    book = Book.query.filter_by(title=book_title).first()

    notes = Note.query.get(id)
    if book in note_user.books and notes in book.notes:
        return render_template("show_notes.html", notes=notes, username=username, orig_user=note_user)
    return redirect(url_for("home"))


@app.route("/edit/<note_id>", methods=["GET", "POST"])
@login_required
def edit_notes(note_id):
    notes = Note.query.get(note_id)
    quotes = Quote.query.filter_by(note_id=note_id).all()
    print(quotes)
    form = forms.Notes()
    books = [book.title for book in current_user.books]
    form.book.choices = books
    form.book.data = notes.book
    form.chapter.data = notes.chapter
    form.notes.data = notes.notes
    if quotes:
        try:
            if quotes[0]:
                form.quote1.data = quotes[0].quote
                form.quote1_speaker.data = quotes[0].speaker
                form.quote1_page.data = quotes[0].page
            if quotes[1]:
                form.quote2.data = quotes[1].quote
                form.quote2_speaker.data = quotes[1].speaker
                form.quote2_page.data = quotes[1].page
            if quotes[2]:
                form.quote3.data = quotes[2].quote
                form.quote3_speaker.data = quotes[2].speaker
                form.quote3_page.data = quotes[2].page
            if quotes[3]:
                form.quote4.data = quotes[3].quote
                form.quote4_speaker.data = quotes[3].speaker
                form.quote4_page.data = quotes[3].page
            if quotes[4]:
                form.quote5.data = quotes[4].quote
                form.quote5_speaker.data = quotes[4].speaker
                form.quote5_page.data = quotes[4].page
        except IndexError:
            print("list over")
    return render_template("add_notes.html", form=form)


@app.route("/delete/<note_id>", methods=["GET", "POST"])
@login_required
def delete_notes(note_id):
    note = Note.query.get(note_id)
    quotes = Quote.query.filter_by(note_id=note_id).all()
    for quote in quotes:
        db.session.delete(quote)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("book_list"))


@app.route("/add_book", methods=["GET", "POST"])
@login_required
def add_book():
    form = forms.BookSearch()
    if form.search.data and form.validate_on_submit():
        books = book_api_call(form.title.data, form.author.data)
        return render_template("book_search.html", form=form, books=books)
    return render_template("book_search.html", form=form)


@app.route("/book_clicked/<title>/<author>")
@login_required
def book_clicked(title, author):
    book = Book.query.filter_by(title=title, author=author).first()
    if book:
        if book in current_user.books:
            flash("This book is already in your booklist.")
            return redirect(url_for("add_book"))
        else:
            book.users.append(current_user)
            current_user.books.append(book)
            db.session.commit()
            return redirect(url_for("add_notes", book=book.title))
    new_book = Book(title=title, author=author)
    db.session.add(new_book)
    current_user.books.append(new_book)
    db.session.commit()
    return redirect(url_for("add_notes", book=new_book.title))


@app.route("/booklist")
def book_list():
    book_data = []
    books = current_user.books
    for book in books:
        temp_dict = {
            "book": book,
            "notes": Note.query.filter_by(user_id=current_user.id, book_id=book.id).all(),
            "quotes": Quote.query.filter_by(user_id=current_user.id, book_id=book.id).all()
        }
        book_data.append(temp_dict)
    return render_template("book_list.html", books=book_data)


@app.route("/quotes", methods=["GET", "POST"])
@login_required
def quote_display():
    form = forms.SearchForm()
    quotes = Quote.query.filter_by(user_id=current_user.id).all()
    if form.validate_on_submit():
        if form.speaker.data and form.quote_contains.data:
            quotes = Quote.query.filter(Quote.quote.contains(form.quote_contains.data)).filter_by(
                user_id=current_user.id,
                speaker=form.speaker.data)
        elif form.speaker.data:
            quotes = Quote.query.filter_by(user_id=current_user.id, speaker=form.speaker.data.title())
        elif form.quote_contains.data:
            quotes = Quote.query.filter(Quote.quote.contains(form.quote_contains.data)).filter_by(
                user_id=current_user.id)
        return render_template("quotes.html", form=form, quotes=quotes)
    return render_template("quotes.html", form=form, quotes=quotes)


@app.route("/note_search", methods=["GET", "POST"])
@login_required
def note_search():
    form = forms.SearchForm()
    if form.validate_on_submit():
        notes = Note.query.filter(Note.notes.contains(form.note_contains.data)).filter_by(user_id=current_user.id).all()
        return render_template("note_search.html", form=form, results=notes)
    return render_template("note_search.html", form=form)


def book_api_call(title, author):
    temp = []
    api_key = {
        "key": os.environ.get("BOOKS_API_KEY")
    }
    if author:
        param = f"{title}+inauthor:{author}"
    else:
        param = title
    data = {
        "q": param
    }
    response = requests.get("https://www.googleapis.com/books/v1/volumes", params=data, headers=api_key)
    response.raise_for_status()
    data = response.json()["items"]
    for item in data:
        try:
            temp_dict = {
                "title": item["volumeInfo"]["title"],
                "author": item["volumeInfo"]["authors"][0],
                "img_url": item["volumeInfo"]["imageLinks"]["thumbnail"],
            }
        except KeyError:
            print("Key is missing")
        else:
            temp.append(temp_dict)
    return temp


if __name__ == "__main__":
    app.run(debug=True)
