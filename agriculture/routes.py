
# Importing essential libraries and modules
from agriculture import app, db
from agriculture.models import Field, User
from agriculture.forms import CreateFieldForm, DeleteFieldForm
from agriculture.forms import LoginForm, RegisterForm, EditUserDetailsForm

from flask import  Flask, render_template, redirect, url_for, flash, request, Markup
from flask import jsonify
from flask_login import login_user, logout_user, current_user, login_required

from pyproj import Geod
import numpy as np
import pandas as pd
import json
from  agriculture.utils.disease import disease_dic
from  agriculture.utils.fertilizer import fertilizer_dic

import requests
import  agriculture.config
import pickle
import io
import torch
from torchvision import transforms
from PIL import Image
from  agriculture.utils.model import ResNet9
# ==============================================================================================


###################################################################################



# -------------------------LOADING THE TRAINED MODELS -----------------------------------------------

# Loading plant disease classification model

disease_classes = ['Apple___Apple_scab',
                   'Apple___Black_rot',
                   'Apple___Cedar_apple_rust',
                   'Apple___healthy',
                   'Blueberry___healthy',
                   'Cherry_(including_sour)___Powdery_mildew',
                   'Cherry_(including_sour)___healthy',
                   'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
                   'Corn_(maize)___Common_rust_',
                   'Corn_(maize)___Northern_Leaf_Blight',
                   'Corn_(maize)___healthy',
                   'Grape___Black_rot',
                   'Grape___Esca_(Black_Measles)',
                   'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
                   'Grape___healthy',
                   'Orange___Haunglongbing_(Citrus_greening)',
                   'Peach___Bacterial_spot',
                   'Peach___healthy',
                   'Pepper,_bell___Bacterial_spot',
                   'Pepper,_bell___healthy',
                   'Potato___Early_blight',
                   'Potato___Late_blight',
                   'Potato___healthy',
                   'Raspberry___healthy',
                   'Soybean___healthy',
                   'Squash___Powdery_mildew',
                   'Strawberry___Leaf_scorch',
                   'Strawberry___healthy',
                   'Tomato___Bacterial_spot',
                   'Tomato___Early_blight',
                   'Tomato___Late_blight',
                   'Tomato___Leaf_Mold',
                   'Tomato___Septoria_leaf_spot',
                   'Tomato___Spider_mites Two-spotted_spider_mite',
                   'Tomato___Target_Spot',
                   'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
                   'Tomato___Tomato_mosaic_virus',
                   'Tomato___healthy']

disease_model_path = 'agriculture/models/plant_disease_model.pth'
disease_model = ResNet9(3, len(disease_classes))
disease_model.load_state_dict(torch.load(
    disease_model_path, map_location=torch.device('cpu')))
disease_model.eval()


# Loading crop recommendation model

crop_recommendation_model_path = 'agriculture/models/RandomForest.pkl'
crop_recommendation_model = pickle.load(
    open(crop_recommendation_model_path, 'rb'))


# =========================================================================================

# Custom functions for calculations

def weather_fetch(city_name):
    """
    Fetch and returns the temperature and humidity of a city
    :params: city_name
    :return: temperature, humidity
    """
    # https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API key}
    api_key = agriculture.config.weather_api_key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    #5.349390, -4.017050
    latitude = "29.3846"
    longitude="70.9116"
    #complete_url = base_url + "appid=" + api_key + "&q=" + city_name
    complete_url = base_url + "appid=" + api_key + "&lat=" + latitude+"&lon="+longitude
    response = requests.get(complete_url)
    x = response.json()
    print(x)
    if x["cod"] != "404":
        y = x["main"]

        temperature = round((y["temp"] - 273.15), 2)
        humidity = y["humidity"]
        return temperature, humidity
    else:
        return None






def predict_image(img, model=disease_model):
    """
    Transforms image to tensor and predicts disease label
    :params: image
    :return: prediction (string)
    """
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.ToTensor(),
    ])
    image = Image.open(io.BytesIO(img))
    img_t = transform(image)
    img_u = torch.unsqueeze(img_t, 0)

    # Get predictions from model
    yb = model(img_u)
    # Pick index with highest probability
    _, preds = torch.max(yb, dim=1)
    prediction = disease_classes[preds[0].item()]
    # Retrieve the class label
    return prediction

# ===============================================================================================

# render home page


@app.route('/')
def home():
    title = 'AGRI SMART - Home'
    return render_template('recommandation/index.html', title=title)

# render crop recommendation form page


@app.route('/crop-recommend')
def crop_recommend():
    title = 'AGRI SMART - Crop Recommendation'
    return render_template('recommandation/crop.html', title=title)

# render fertilizer recommendation form page


@app.route('/fertilizer')
def fertilizer_recommendation():
    title = 'AGRI SMART - Fertilizer Suggestion'

    return render_template('recommandation/fertilizer.html', title=title)

# render disease prediction input page




# ===============================================================================================

# RENDER PREDICTION PAGES

# render crop recommendation result page


@app.route('/crop-predict', methods=['POST'])
def crop_prediction():
    title = 'AGRI SMART - Crop Recommendation'

    if request.method == 'POST':
        N = int(request.form['nitrogen'])
        P = int(request.form['phosphorous'])
        K = int(request.form['pottasium'])
        ph = float(request.form['ph'])
        rainfall = float(request.form['rainfall'])

        # state = request.form.get("stt")
        city = request.form.get("city")

        if weather_fetch(city) != None:
            temperature, humidity = weather_fetch(city)
            data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
            my_prediction = crop_recommendation_model.predict(data)
            final_prediction = my_prediction[0]

            return render_template('recommandation/crop-result.html', prediction=final_prediction, title=title)

        else:

            return render_template('recommandation/try_again.html', title=title)

# render fertilizer recommendation result page


@app.route('/fertilizer-predict', methods=['POST'])
def fert_recommend():
    title = 'AGRI SMART - Fertilizer Suggestion'

    crop_name = str(request.form['cropname'])
    N = int(request.form['nitrogen'])
    P = int(request.form['phosphorous'])
    K = int(request.form['pottasium'])
    # ph = float(request.form['ph'])

    df = pd.read_csv('agriculture/Data/fertilizer.csv')

    nr = df[df['Crop'] == crop_name]['N'].iloc[0]
    pr = df[df['Crop'] == crop_name]['P'].iloc[0]
    kr = df[df['Crop'] == crop_name]['K'].iloc[0]

    n = nr - N
    p = pr - P
    k = kr - K
    temp = {abs(n): "N", abs(p): "P", abs(k): "K"}
    max_value = temp[max(temp.keys())]
    if max_value == "N":
        if n < 0:
            key = 'NHigh'
        else:
            key = "Nlow"
    elif max_value == "P":
        if p < 0:
            key = 'PHigh'
        else:
            key = "Plow"
    else:
        if k < 0:
            key = 'KHigh'
        else:
            key = "Klow"

    response = Markup(str(fertilizer_dic[key]))

    return render_template('recommandation/fertilizer-result.html', recommendation=response, title=title)

# render disease prediction result page


@app.route('/disease-predict', methods=['GET', 'POST'])
def disease_prediction():
    title = 'AGRI SMART - Disease Detection'

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return render_template('recommandation/disease.html', title=title)
        try:
            img = file.read()

            prediction = predict_image(img)

            prediction = Markup(str(disease_dic[prediction]))
            return render_template('recommandation/disease-result.html', prediction=prediction, title=title)
        except:
            pass
    return render_template('recommandation/disease.html', title=title)


# ===============================================================================================
# End recommandation
################################################################################

# @app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login_page():

    form = LoginForm()

    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()

        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data) :
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('home_page'))
        else:
            flash("Le nom d'utilisateur et le mot de passe ne correspondent pas ! Veuillez réessayer", category='danger')

    return render_template('login.html', form=form)

################################################################################

@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash("Déconnecté avec succès!", category='info')
    return redirect(url_for("login_page"))

################################################################################

@app.route('/register', methods=['GET','POST'])
def register_page():
    form = RegisterForm()

    if form.validate_on_submit():

        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)

        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('login_page'))

    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f"Une erreur s'est produite lors de la création d'un utilisateur: {err_msg}", category='danger')

    return render_template('register.html', form=form)

################################################################################

@app.route('/home')
@app.route('/dashboard')
@login_required
def home_page():

    # Retrieve current user
    user = current_user

    # Get user fields
    fields = user.fields

    print("Fields",fields)

    fields_dataset = []

    minlat = 1000
    minlon = 1000
    maxlat = -1000
    maxlon = -1000

    for field in fields:

        lat = [float(l) for l in field.geometry.split(',')[::2]]
        lon = [float(l) for l in field.geometry.split(',')[1::2]]

        current_minlat, current_maxlat = min(lat), max(lat)
        current_minlon, current_maxlon = min(lon), max(lon)

        if current_minlat < minlat : minlat = current_minlat
        if current_maxlat > maxlat : maxlat = current_maxlat
        if current_minlon < minlon : minlon = current_minlon
        if current_maxlon > maxlon : maxlon = current_maxlon

        _f = {}
        _f['name'] = field.name
        _f['crop'] = field.crop
        _f['area'] = field.area

        _f['geometry'] = [(float(lat),float(lon)) for lat,lon in zip(field.geometry.split(',')[::2],field.geometry.split(',')[1::2])]

        fields_dataset.append(_f)

    map_center = (minlat, minlon, maxlat, maxlon)

    return render_template('home.html', fields=fields, fields_dataset=json.dumps(fields_dataset), map_center=map_center)

################################################################################

@app.route('/fields')
@login_required
def fields_page():

    # Retrieve user fields
    fields = current_user.fields

    return render_template('fields.html', fields=fields)

################################################################################

@app.route('/create-field', methods=["POST", "GET"])
@login_required
def create_field_page():
    form = CreateFieldForm()

    if form.validate_on_submit():

        lat = [float(l) for l in form.geometry.data.split(',')[::2]]
        lon = [float(l) for l in form.geometry.data.split(',')[1::2]]

        geod = Geod('+a=6378137 +f=0.0033528106647475126')
        poly_area, poly_perimeter = geod.polygon_area_perimeter(lon, lat)

        def PolyArea(x,y):
            return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

        field_to_create = Field(name=form.name.data,
                                crop=form.crop.data,
                                geometry=form.geometry.data,
                                area=np.round(np.abs(poly_area/1e4),2))


        current_user.fields.append(field_to_create)
        db.session.commit()

        return redirect(url_for('home_page'))

    if form.errors != {}: #If there are not errors from the validations
        for err_msg in form.errors.values():
            flash(f"Une erreur s'est produite lors de la création d'un nouveau champ: {err_msg}", category='danger')

    return render_template('create_field.html', form=form)

################################################################################

@app.route('/delete-field', methods=["POST","GET"])
@login_required
def delete_field_page():

    form = DeleteFieldForm()

    form.field.choices = [(g.name,g.name) for g in Field.query.all()]

    # Retrieve fields entries from Database
    fields = Field.query.all()

    if form.validate_on_submit():

        field_to_delete = Field.query.filter_by(name=form.field.data).first()
        db.session.delete(field_to_delete)
        db.session.commit()

        return redirect(url_for('home_page'))

    if form.errors != {}: #If there are not errors from the validations
        for err_msg in form.errors.values():
            flash(f"Une erreur s'est produite lors de la création d'un nouveau champ: {err_msg}", category='danger')


    return render_template('delete_field.html', form=form, fields=fields)

################################################################################

@app.route('/<string:name>')
@app.route('/<string:name>/<int:index>')
@login_required
def field_details_page(name, index=-1):

    field = Field.query.filter_by(name=name).first()

    field_data = {}
    field_data["geometry"]  = [(float(lat),float(lon)) for lat,lon in zip(field.geometry.split(',')[::2],field.geometry.split(',')[1::2])]

    msi_list = []

    for idx,multispectraindex in enumerate(field.msi_index):

        msi = {}
        print(multispectraindex)

        msi["date"]       = multispectraindex.date
        msi["latitude"]   = multispectraindex.latitude
        msi["longitude"]  = multispectraindex.longitude
        msi["ndvi"]       = multispectraindex.ndvi
        msi_list.append(msi)



    if(len(msi_list) == 0) :
        field_data["is_empty"] = True
    else:
        field_data["is_empty"] = False

    if(field_data["is_empty"] == False):

        field_data["latitude"] = msi_list[index]["latitude"]
        field_data["longitude"] = msi_list[index]["longitude"]
        field_data["ndvi"] = msi_list[index]["ndvi"]
        field_data["date"] = msi_list[index]["date"]
        field_data["current_index"] = index

    mean_ndvi = np.average([float(el) for el in field_data["ndvi"].split(',')])
    api_key = agriculture.config.weather_api_key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    latitude = "29.3846"
    longitude="70.9116"
    complete_url = base_url + "appid=" + api_key + "&lat=" + latitude+"&lon="+longitude
    response = requests.get(complete_url)
    x = response.json()
    print(x)
    if x["cod"] != "404":
        weather =x
    else:
        weather = ""

    return render_template('field_details.html', mean_ndvi=mean_ndvi, weather=weather, current_index=index, field_data=json.dumps(field_data), name=field.name, crop=field.crop, area=field.area, date=field_data["date"])

################################################################################

@app.route('/edit-user-details', methods=["POST","GET"])
@login_required
def edit_user_detail_page():

    user = current_user

    form = EditUserDetailsForm()

    if form.validate_on_submit():

        user.company_name = form.company_name.data
        user.farm_address = form.farm_address.data
        user.fiscal_code = form.fiscal_code.data

        db.session.commit()


    return render_template('edit_user_details.html', form=form, user=user)

################################################################################
