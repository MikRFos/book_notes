from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

association_table = db.Table("association",
                             db.Column("book_id", db.Integer, db.ForeignKey("books.id"), primary_key=True),
                             db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True))

class User(db.Model, UserMixin):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    books = db.relationship("Book", secondary=association_table, back_populates="users")
    notes = db.relationship("Note", back_populates="user")
    quotes = db.relationship("Quote", back_populates="user")


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    notes = db.relationship("Note", back_populates="book")
    quotes = db.relationship("Quote", back_populates="book")
    users = db.relationship("User", secondary=association_table, back_populates="books")
    
    
class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    user = db.relationship("User", back_populates="notes")
    book = db.relationship("Book", back_populates="notes")
    chapter = db.Column(db.String(150), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    quotes = db.relationship("Quote", back_populates="note_section")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)


class Quote(db.Model):
    __tablename__ = "quotes"
    id = db.Column(db.Integer, primary_key=True)
    user = db.relationship("User", back_populates="quotes")
    quote = db.Column(db.Text, nullable=False)
    speaker = db.Column(db.String(50))
    book = db.relationship("Book", back_populates="quotes")
    page = db.Column(db.Integer)
    note_section = db.relationship("Note", back_populates="quotes")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=False)
