from flask import Flask, render_template, url_for, redirect, flash, request
from flask_ckeditor import CKEditor
from sqlalchemy import func

from model import db, User, Book, Note, Quote, association_table
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import forms
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///book_notes.db").replace("postgres://",
                                                                                                          "postgresql://",
                                                                                                          1)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()

ckeditor = CKEditor(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/")
def home():
    """Renders the homepage"""
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register_user():
    """Register a user.
    If successfull also logs user in.
    If unsuccessfull sends a flash message to the webpage to display the error.
    """
    form = forms.RegistryForm()
    if form.validate_on_submit():
        if User.query.filter(func.lower(User.username) == func.lower(form.username.data)).first():
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
    """Logs a user in if correct username/password is entered.
    Sends a flash message to the webpage if the login is unsuccessful
    """
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower(User.username) == func.lower(form.username.data)).first()
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
    """Logs the user out"""
    logout_user()
    return redirect(url_for("home"))


@app.route("/add_notes", methods=["GET", "POST"])
@login_required
def add_notes():
    """Get: Creates a form and renders the form on the add_notes.html page.
    POST: Using the filled out form, creates note and quote entries in the database.
    """
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
            add_quote(quote=form.quote1.data, speaker=form.quote1_speaker.data, page=form.quote1_page.data,
                      user_id=current_user.id, book=book_id, note_id=notes.id)
        if form.quote2.data:
            add_quote(quote=form.quote2.data, speaker=form.quote2_speaker.data, page=form.quote2_page.data,
                      user_id=current_user.id, book=book_id, note_id=notes.id)
        if form.quote3.data:
            add_quote(quote=form.quote3.data, speaker=form.quote3_speaker.data, page=form.quote3_page.data,
                      user_id=current_user.id, book=book_id, note_id=notes.id)
        if form.quote4.data:
            add_quote(quote=form.quote4.data, speaker=form.quote4_speaker.data, page=form.quote4_page.data,
                      user_id=current_user.id, book=book_id, note_id=notes.id)
        if form.quote5.data:
            add_quote(quote=form.quote5.data, speaker=form.quote5_speaker.data, page=form.quote5_page.data,
                      user_id=current_user.id, book=book_id, note_id=notes.id)
        return redirect(url_for("home"))
    return render_template("add_notes.html", form=form)


@app.route("/show_notes/<username>/<book_title>/<id>")
def show_notes(username, book_title, id):
    """Displays the notes and some other relevant info on the show_notes.html page.
    Login not required so this page can be shared.
    If the user that created the note is logged in, they are able to edit or delete the note.

    Keyword arguments:
    username -- The username of the user that created the note
    boot_title -- the title of the book that the note is for.
    id -- the note id.
    """
    note_user = User.query.filter_by(username=username).first()
    book = Book.query.filter_by(title=book_title).first()
    quotes = Quote.query.filter_by(note_id=id).all()
    notes = Note.query.get(id)
    if book in note_user.books and notes in book.notes:
        return render_template("show_notes.html", notes=notes, username=username, orig_user=note_user, quotes=quotes)
    return redirect(url_for("home"))


@app.route("/edit/<note_id>", methods=["GET", "POST"])
@login_required
def edit_notes(note_id):
    """Allows the user to edit notes
    Get: Retrieves the note item from the database and pre-fills in the form with the correct values
    Post: Saves the edited note in the database

    keyword arguments:
    note_id -- the note id to be edited.
    """
    #Required setup
    notes = Note.query.get(note_id)
    quotes = Quote.query.filter_by(note_id=note_id).all()
    form = forms.Notes()
    books = [book.title for book in current_user.books]
    form.book.choices = books

    #Submit Clicked
    if form.validate_on_submit():
        #TODO Edit Quotes
        book_id = Book.query.filter_by(title=form.book.data).first().id
        notes.chapter = form.chapter.data
        notes.notes = form.notes.data
        notes.book_id = book_id
        db.session.commit()
        return redirect(url_for("home"))

    #add form values if a get
    form.book.data = notes.book.title
    form.chapter.data = notes.chapter
    form.notes.data = notes.notes
    # TODO Fix this!!! Function?
    if quotes:
        try:
            if quotes[0]:
                form.quote1.data = quotes[0].quote
                form.quote1_speaker.data = quotes[0].speaker
                form.quote1_page.data = quotes[0].page
        except IndexError:
            pass
        try:
            if quotes[1]:
                form.quote2.data = quotes[1].quote
                form.quote2_speaker.data = quotes[1].speaker
                form.quote2_page.data = quotes[1].page
        except IndexError:
            pass
        try:
            if quotes[2]:
                form.quote3.data = quotes[2].quote
                form.quote3_speaker.data = quotes[2].speaker
                form.quote3_page.data = quotes[2].page
        except IndexError:
            pass
        try:
            if quotes[3]:
                form.quote4.data = quotes[3].quote
                form.quote4_speaker.data = quotes[3].speaker
                form.quote4_page.data = quotes[3].page
        except IndexError:
            pass
        try:
            if quotes[4]:
                form.quote5.data = quotes[4].quote
                form.quote5_speaker.data = quotes[4].speaker
                form.quote5_page.data = quotes[4].page
        except IndexError:
            pass

    return render_template("edit_notes.html", note_id=note_id, form=form)


@app.route("/delete/<note_id>", methods=["GET", "POST"])
@login_required
def delete_notes(note_id):
    """Deletes a note and any included quotes from the database."""
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
    """Get: Renders the booksearch form on the book_search page
    Post: renders a list of books on the book_search page after using the book_api_call function
    """
    form = forms.BookSearch()
    if form.search.data and form.validate_on_submit():
        books = book_api_call(form.title.data, form.author.data)
        return render_template("book_search.html", form=form, books=books)
    return render_template("book_search.html", form=form)


@app.route("/book_clicked/<title>/<author>")
@login_required
def book_clicked(title, author):
    """Adds a book to the database if the book does not currently exist in it.
    If it does exist add the book to the relationship with the current user
    """
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
@login_required
def book_list():
    """Renders a list of the books belonging to the current user with their associated notes and quotes."""
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
    """Displays the user's added quotes.

    Get: Renders all user added quotes and the search form on the quotes page
    Post: Renders the results of the search form in the quotes page.
    *Note only quotes the current user added are displayed on this page.
    """
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
    """Search the current users' notes based on their search terms.

    Get: Renders the search form on the note_search page.
    Post: Renders the results of the user query on the note_search page.
    """
    form = forms.SearchForm()
    if form.validate_on_submit():
        notes = Note.query.filter(Note.notes.contains(form.note_contains.data)).filter_by(user_id=current_user.id).all()
        return render_template("note_search.html", form=form, results=notes)
    return render_template("note_search.html", form=form)


def book_api_call(title, author):
    """Calls a get request from the google books API in order to find the book user requested.

    keyword arguments:
    title -- the title of the book.
    author -- the author of the book.
    """
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

def add_quote(quote, speaker, page, user_id, book, note_id):
    """Adds a qote to the database."""
    new_quote = Quote(quote=quote, speaker=speaker, page=page, user_id=user_id, book_id=book, note_id=note_id)
    db.session.add(new_quote)
    db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
