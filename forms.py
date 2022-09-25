from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, PasswordField
from flask_ckeditor import CKEditorField
from wtforms.validators import DataRequired, Length, Optional


class Notes(FlaskForm):
    book = SelectField("Book*", validators=[DataRequired()])
    chapter = StringField("Chapter")
    key_words = StringField("Keywords")
    notes = CKEditorField("Notes*", validators=[DataRequired()])

    quote1 = StringField("Quote:")
    quote1_speaker = StringField("Speaker:")
    quote1_page = IntegerField("Page#:", validators=[Optional()])

    quote2 = StringField("Quote:")
    quote2_speaker = StringField("Speaker:")
    quote2_page = IntegerField("Page#:", validators=[Optional()])

    quote3 = StringField("Quote:")
    quote3_speaker = StringField("Speaker:")
    quote3_page = IntegerField("Page#:", validators=[Optional()])

    quote4 = StringField("Quote:")
    quote4_speaker = StringField("Speaker:")
    quote4_page = IntegerField("Page#:", validators=[Optional()])

    quote5 = StringField("Quote:")
    quote5_speaker = StringField("Speaker:")
    quote5_page = IntegerField("Page#:", validators=[Optional()])

    submit = SubmitField()


class BookSearch(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    author = StringField("Author")
    search = SubmitField()


class CreateTheory(FlaskForm):
    theory = CKEditorField("Theory")
    evidence_cite = StringField("Evidence")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Login")


class RegistryForm(FlaskForm):
    username = StringField("Username",
                           validators=[DataRequired(), Length(min=5,
                                                              message="Username must be at least 5 characters long")])
    password = PasswordField("Password",
                             validators=[DataRequired(), Length(min=6,
                                                                message="Password must be at least 6 characters long")])
    password_confirmation = PasswordField("Re-Enter Password", validators=[DataRequired(), Length(min=6)])
    register = SubmitField("Register")

class SearchForm(FlaskForm):
    quote_contains = StringField("Quote Includes")
    note_contains = StringField("Note Includes")
    speaker = StringField("Speaker")
    keywords = StringField("Keywords")
    submit = SubmitField("Submit")
