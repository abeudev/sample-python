from agriculture import db, login_manager
from agriculture import bcrypt
from flask_login import UserMixin


################################################################################

fields_images = db.Table('fields_images',
                            db.Column('satellite_image_id', db.Integer(), db.ForeignKey('field.field_id')),
                            db.Column('field_id', db.Integer(), db.ForeignKey('satellite_image.satellite_image_id')) )

################################################################################

class Field(db.Model):
    __tablename__    = 'field'
    field_id         = db.Column(db.Integer(), primary_key=True)
    name             = db.Column(db.String(length=30), nullable=False, unique=True)
    crop             = db.Column(db.String(length=15), nullable=False, unique=False)
    area             = db.Column(db.Float(), nullable=False, unique=False)
    geometry         = db.Column(db.String(), nullable=False, unique=False)
    satellite_images = db.relationship("SatelliteImage", secondary=fields_images)
    msi_index        = db.relationship("MultiSpectraIndex", backref="owned_index" ,lazy=True)
    owner            = db.Column(db.Integer(), db.ForeignKey('user.user_id'))

################################################################################

class MultiSpectraIndex(db.Model):
    __tablename__  = 'multi_spectral_index'
    msi_id         = db.Column(db.Integer(), primary_key=True)
    date           = db.Column(db.String(), nullable=False)
    latitude       = db.Column(db.String(), nullable=False)
    longitude      = db.Column(db.String(),nullable=False)
    ndvi           = db.Column(db.String(), nullable=False)
    field          = db.Column(db.Integer(), db.ForeignKey('field.field_id'))

################################################################################

class SatelliteImage(db.Model):
    __tablename__      = 'satellite_image'
    satellite_image_id = db.Column(db.Integer(), primary_key=True)
    product_id         = db.Column(db.String(length=256), nullable=False, unique=True)
    product_name       = db.Column(db.String(length=256), nullable=False, unique=True)
    date               = db.Column(db.String(length=50), nullable=False, unique=False)
    downloaded         = db.Column(db.Boolean(), nullable=False, default=False)
    fields             = db.relationship("Field", secondary=fields_images)

################################################################################

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(user_id=user_id).first()

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    user_id              = db.Column(db.Integer(), primary_key=True)
    username             = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address        = db.Column(db.String(length=50), nullable=False, unique=True)
    company_name         = db.Column(db.String(length=100))
    farm_address         = db.Column(db.String(length=512))
    fiscal_code          = db.Column(db.String(length=40))
    fields               = db.relationship('Field', backref='owned_field', lazy=True)
    password_hash        = db.Column(db.String(length=60), nullable=False)

    @property
    def id(self):
        return self.user_id

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)



################################################################################
