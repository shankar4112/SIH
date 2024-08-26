
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import sqlite3
from datetime import datetime
import subprocess
import os
import pandas as pd
import re
import mysql.connector
from mysql.connector import Error
from flask import render_template, request
from datetime import datetime
import requests
import numpy as np
import tensorflow as tf
from PIL import Image
import matplotlib.pyplot as plt
from fastapi import FastAPI, File, UploadFile
import io
from flask_cors import CORS, cross_origin
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'


def potato(image):
    # Load the trained model
    model = tf.keras.models.load_model('1.h5')

    # Define the class names (replace with your actual class names)
    class_names = ['Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy']

    # Preprocess the image (assuming the image is already loaded as a PIL Image object)
    image = image.resize((256, 256))  # Resize to the model's expected input size
    image = np.array(image) / 255.0    # Normalize to [0, 1]
    image = np.expand_dims(image, axis=0)  # Add batch dimension

    # Make prediction
    predictions = model.predict(image)
    predicted_class = np.argmax(predictions, axis=1)[0]
    predicted_label = class_names[predicted_class]

    # Display the image with prediction (optional)
    # plt.imshow(np.squeeze(image))  # Remove batch dimension before displaying
    # plt.title(f'Predicted: {predicted_label}')
    # plt.show()

    return predicted_label

app = Flask(__name__)
app.secret_key = 'xyzsdfg'  # Same secret key as in the login system

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Abhinaya@2004'
app.config['MYSQL_DB'] = 'disease'

db_connection = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)



@app.route('/')
def index():
    if 'loggedin' in session:
        return render_template('index.html', selected_date='', no_data=False)
    else:
        return redirect(url_for('login_page'))
    

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        # Creating cursor within a with statement
        with db_connection.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password))
            user = cursor.fetchone()
            if user:
                session['loggedin'] = True
                session['userid'] = user['userid']
                session['name'] = user['name']
                session['email'] = user['email']
                message = 'Logged in successfully !'
                return redirect(url_for('index'))
            else:
                message = 'Please enter correct email / password !'
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        language = request.form['language']
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        # Creating cursor within a with statement
        with db_connection.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
            account = cursor.fetchone()
            if account:
                message = 'Account already exists !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                message = 'Invalid email address !'
            elif not userName or not password or not email:
                message = 'Please fill out the form !'
            else:
                cursor.execute('INSERT INTO user (name, email, password, language) VALUES (%s, %s, %s, %s)', (userName, email, password, language))
                db_connection.commit()  # Commit directly on the connection object
                message = 'You have successfully registered !'
                return render_template('next.html', message=message)
    elif request.method == 'POST':
        message = 'Please fill out the form !'
    return render_template('register.html', message=message)

@app.route('/getloc', methods=['GET'])
def get_location():
    try:
        # Extract latitude and longitude from query parameters
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        # Input validation (optional but recommended)
        if not latitude or not longitude:
            return jsonify({'error': 'Missing required parameters: latitude and longitude'}), 400

        apiKey = '3bf457a72550477e98a9dad1159578c1'
        encodedLatitude = requests.utils.quote(latitude)
        encodedLongitude = requests.utils.quote(longitude)
        url = f'https://api.opencagedata.com/geocode/v1/json?key={apiKey}&q={encodedLatitude},{encodedLongitude}&pretty=1&no_annotations=1'

        response = requests.get(url)
        data = response.json()

        if data['status']['code'] == 200 and data.get('results') and len(data['results']) > 0:
            firstResult = data['results'][0]
            components = firstResult.get('components', {})
            city = components.get('city', 'City not found')
            print(city)
            result = requests.get(f'https://api.weatherapi.com/v1/current.json?key=8868e7d431964dd89a265801230604&q={city}&aqi=no')
            # print(result.text)
            return make_response(result.text, 200)
        else:
            errorMessage = data['status'].get('message', 'Location not found')
            return jsonify({'error': errorMessage}), 404  # Use 404 for location not found

    except Exception as error:
        print(f'Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/predict', methods=['POST'])
def predict():
    try:
        print("Inside")
        # Get the image file from the request
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if file:
            image = Image.open(file.stream)  # Open the image file
            plant = request.args.get('plant')
            if plant == 'Potato':
                response = potato(image)
                print(response)
            return jsonify({"prediction": response}), 200
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({"error": "An error occurred"}), 500

    




if __name__ == '__main__':
    app.run(debug=True)

