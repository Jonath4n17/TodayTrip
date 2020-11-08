from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import urllib.request

API_KEY = "AIzaSyBlT-HpvBFNEDO3Bw1msw8ytcYr8IkAwFI"
FINDLOCATION_BASE_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
GEOCODE_BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

def geocode(address):
  params = urllib.parse.urlencode({"address": address, "key": API_KEY,})
  url = f"{GEOCODE_BASE_URL}?{params}"
  result = json.load(urllib.request.urlopen(url))

  if result["status"] in ["OK", "ZERO_RESULTS"]:
    return result["results"]

  raise Exception(result["error_message"])

def findLocations(location, radius, typeL):
  params = urllib.parse.urlencode({"location": location, "radius": radius, "type": typeL, "key": API_KEY,})
  url = f"{FINDLOCATION_BASE_URL}?{params}"

  result = json.load(urllib.request.urlopen(url))

  final = []

  if result["status"] in ["OK", "ZERO_RESULTS"]:
    for i in range(len(result["results"])):
      if result["results"][i]["business_status"] == 'OPERATIONAL':
        final.append(result["results"][i])
      
  return final
  raise Exception(result["error_message"])

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coordinates = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(200), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    keywords = db.Column(db.String(200), nullable=True)
    icon = db.Column(db.String(400), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

history = []

@app.route('/handle_data', methods=['POST', 'GET'])
def handle_data():
    if request.method == 'POST':
        country = request.form['country']
        city = request.form['city']
        address = request.form['address']
        location = address.replace(" ", "+") + ",+" + city.replace(" ","+") + ",+" + country
        radius = str(int(int(request.form['radius']) * 1609.34))
        keywords = request.form['keywords'].split(',')

        history.append(country + ", " + city)

        locNum = geocode(address=location)
        locNum = locNum[0]["geometry"]["location"]
        locNumS = str(locNum["lat"]) + "," + str(locNum["lng"])

        for i in range(len(keywords)):
            NLocations = findLocations(location=locNumS, radius=radius, typeL=keywords[i])

            list=[]
            for i in range(len(NLocations)):
                numString = str(NLocations[i]["geometry"]["location"]["lat"]) + "," + str(NLocations[i]["geometry"]["location"]["lng"])
                typesString = ','.join(NLocations[i]["types"])
                list.append(Todo(
                    coordinates=numString,
                    name=NLocations[i]["name"], 
                    address=NLocations[i]["vicinity"],
                    keywords=typesString,
                    icon=NLocations[i]["icon"],        
                ))
            print(list)

            try:
                for i in range(len(list)):
                    db.session.add(list[i])
                    db.session.commit()
            except:
                return "There was an issue processing your location"
        return redirect('/')

@app.route('/getHistory', methods=['POST', 'GET'])
def getHistory():
    if request.method == 'GET':
        return history[0]
    redirect('/')

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', tasks=tasks)

    return render_template('index.html')

@app.route('/indextoprofile', methods=['GET', 'POST'])
def indextoprofile():
    if request.method == 'POST':
        return redirect(url_for('index'))
    
    return render_template('profile.html')

@app.route('/profiletoindex', methods=['GET', 'POST'])
def profiletoindex():
    if request.method == 'POST':
        return redirect(url_for('profile'))

    return render_template('index.html')

@app.route('/indextologin', methods=['GET', 'POST'])
def indextologin():
    if request.method == 'POST':
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logintoindex', methods=['GET', 'POST'])
def logintoindex():
    if request.method == 'POST':
        return redirect(url_for('login'))

    return render_template('index.html')

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that location'

@app.route('/delete_all')
def delete_all():
    try:
        db.session.query(db.Model).delete()
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting all locations'

if __name__ == "__main__":
    app.run(debug=True)
