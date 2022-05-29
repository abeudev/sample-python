from flask_wtf import FlaskForm
from wtforms.validators import Length, DataRequired, EqualTo, Email
from wtforms import StringField, SubmitField, SelectField, HiddenField, PasswordField
from wtforms.widgets import HiddenInput

################################################################################

class RegisterForm(FlaskForm):

    username      = StringField(label="Nom d'utilisateur:", validators=[Length(min=2,max=30), DataRequired()])
    email_address = StringField(label='Adresse:', validators=[Email(), DataRequired()])
    password1     = PasswordField(label='Mot de passe:', validators=[Length(min=6), DataRequired()])
    password2     = PasswordField(label='Confirmer Mot de passe:', validators=[EqualTo('password1'), DataRequired()])
    submit        = SubmitField(label='Créer le compte')

################################################################################

class LoginForm(FlaskForm):
    username = StringField(label="Nom utilisateur: ", validators=[DataRequired()])
    password = PasswordField(label='Mot de passe:', validators=[DataRequired()])
    submit   = SubmitField(label='Connecter')

################################################################################

class EditUserDetailsForm(FlaskForm):

    company_name    = StringField(label="Entreprise", validators=[DataRequired()])
    farm_address    = StringField(label="Adresse", validators=[DataRequired()])
    fiscal_code     = StringField(label="Code identification", validators=[DataRequired()])
    submit          = SubmitField(label='Enregistrer')

################################################################################

class CreateFieldForm(FlaskForm):

    name     = StringField(label='Intitulé champs :', validators=[Length(min=4,max=25),DataRequired()])
    crop     = SelectField('Intitulé plantation :', choices=[('mais', 'Mais'), ('barley', 'Barley'), ('soybean', 'Soybean')], validators=[DataRequired()])
    geometry = HiddenField(label='Geometrie :', validators=[Length(min=4, message="Définir parcelle")])
    submit   = SubmitField(label='Enregistrer parcelle')

################################################################################

class DeleteFieldForm(FlaskForm):

    field              = SelectField(label='Nom du champ', validators=[DataRequired()])
    confirm_field_name = StringField(label='Confirmer le nom', validators=[DataRequired(), EqualTo('field')])
    submit             = SubmitField(label="Supprimer le champ")

################################################################################
