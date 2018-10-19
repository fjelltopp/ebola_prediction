from flask import Flask, render_template
from ebola_data import EbolaWrapper
from flask_sqlalchemy import SQLAlchemy
import config
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
db = SQLAlchemy(app)
EW = EbolaWrapper(db)

@app.route("/")
def ebola():
    return render_template("ebola.html",
                           date=EW.latest_time.strftime("%d/%m/%Y"),
                           cumulative_chart=EW.json_chart("cases_by_time"),
                           estimated_r=EW.json_chart("estimated_r"),
                           cfr_chart=EW.json_chart("cfr"),
                           prediction_chart=EW.json_chart("predicted_cases"))

