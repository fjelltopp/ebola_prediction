import pandas as pd
import altair as alt
import datetime
import numpy as np
import json
import simple_disease_model as disease_model
from scipy import stats
from config import DATABASE_URL
from model import DataSource

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


data_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSrr9DRaC2fXzPdmOxLW-egSYtxmEp_RKoYGggt-zOKYXSx4RjPsM4EO19H7OJVX1esTtIoFvlKFWcn/pub?gid=1564028913&single=true&output=csv"


def get_incidence(cumulative_cases):
    onset_dates = []
    prev = 0
    for date, n_cases in cumulative_cases.iteritems():
        new_cases_t = n_cases - prev
        onset_dates += [date]*new_cases_t
        prev += new_cases_t

    onset_dates = pd.Series(onset_dates)
    min_date = onset_dates.min()
    days = (onset_dates - min_date).dt.days
    max_days = np.max(days)
    incidence = []
    result_dates = []
    for i in range(max_days + 1):
        result_dates.append(min_date + datetime.timedelta(days=i))
        incidence.append(np.sum(days == i))
    incidence = np.array(incidence)
    return incidence, result_dates


def get_and_predict():
    data = pd.read_csv(data_url, skiprows=[1],
                       parse_dates=["report_date", "publication_date"])
    cases_by_time = data.groupby("report_date").sum()

    cases_by_time.to_sql("cases_by_time", engine, if_exists="replace")

    latest_update_date = data["publication_date"].max()

    incidence, result_dates = get_incidence(cases_by_time["total_cases"])

    ebola_gamma_params = {
        "a": 2.41975308641975,
        "scale": 4.74428571428571
    }
    ebola_gamma = disease_model.discrete_prob(stats.gamma, ebola_gamma_params)
    force_of_infection = disease_model.force_of_infection_time(incidence, ebola_gamma)

    mean_r, lower_r, upper_r, post_a, post_b = disease_model.estimated_r(
        incidence, force_of_infection, ebola_gamma)

    n_pred = 21
    sims = disease_model.simulate_from_end_N(incidence, ebola_gamma, n_pred,
                                             lambda x: stats.gamma.mean(a=post_a[-1], scale=post_b[-1]),
                                             N=100)
    cum_sims = np.cumsum(sims, axis=1)
    
    results = pd.DataFrame()
    results["date"] = result_dates
    results["incidence"] = incidence
    results["cumulative_incidence"] = np.cumsum(incidence)
    results["estimated_r"] = [0] * 9 + mean_r
    results["estimated_r_lower"] = [0] * 9 + lower_r
    results["estimated_r_upper"] = [0] * 9 + upper_r

    predictions = pd.DataFrame()

    predictions["date"] = [result_dates[0] + datetime.timedelta(days=i) for i in range(len(result_dates) + n_pred)]
    predictions["incidence"] = np.mean(sims, axis=0)
    predictions["incidence_upper"] = np.quantile(sims,0.95, axis=0)
    predictions["incidence_lower"] = np.quantile(sims,0.05, axis=0)
    predictions["cumulative_incidence"] = np.mean(cum_sims, axis=0)
    predictions["cumulative_incidence_upper"] = np.quantile(cum_sims, 0.95,axis=0)
    predictions["cumulative_incidence_lower"] = np.quantile(cum_sims,0.05, axis=0)
    
    results.to_sql("estimate_r", engine, if_exists="replace")
    predictions.to_sql("predictions", engine, if_exists="replace")

    session.add(DataSource(
        update_time=latest_update_date,
        data=json.dumps({"cases_by_time": "cases_by_time",
                         "estimate_r": "estimate_r",
                         "predictions": "predictions"}))
    )
    session.commit()
    

def nice_variables(var):
    return " ".join([part.capitalize() for part in var.split("_")])


class EbolaWrapper():

    def __init__(self):
        self.charts = {"cases_by_time": self.chart_cases_by_time,
                       "estimated_r": self.chart_estimated_r,
                       "predicted_cases": self.predicted_cases,
                       "cfr": self.chart_cfr}

        self.latest_id = 0
        self.latest_time = None
        data = self.get_latest_data()
        self.prepare_data(data)

    def get_latest_data(self):
        res = session.query(DataSource).order_by(DataSource.id.desc()).limit(1)
        record = res[0]
        if record.id == self.latest_id:
            return None
        self.latest_id = record.id
        self.latest_time = record.update_time
        return json.loads(record.data)

    def prepare_data(self, data):
        self.cases_by_time = pd.read_sql(data["cases_by_time"], engine).reset_index()
        self.cases_by_time_melted = self.cases_by_time.melt("report_date")
        self.cases_by_time_melted["variable"] = self.cases_by_time_melted["variable"].map(nice_variables)
        self.estimated_r = pd.read_sql(data["estimate_r"], engine)
        self.predictions = pd.read_sql(data["predictions"], engine)

    def chart(self, chart_name):
        return self.charts[chart_name]()
    
    def json_chart(self, chart_name):
        return self.chart(chart_name).to_json()
    
    def predicted_cases(self):
        data = self.predictions
        line = alt.Chart(data).mark_line().encode(
            x='date',
            y='cumulative_incidence'
        )
        confidence_interval = alt.Chart(
            data,
            title="Predicted number of Ebola cases",
            width=500, height=300).mark_area(opacity=0.3).encode(
                x=alt.Y('date', axis=alt.Axis(title='Date Reported')),
                y=alt.Y('cumulative_incidence_lower', axis=alt.Axis(title="Number")),
                y2='cumulative_incidence_upper'
            )

        return confidence_interval + line

    def chart_cfr(self):
        data = self.cases_by_time
        data["cfr"] = data["total_deaths"] / data["total_cases"] * 100
        print(data["cfr"])
        chart = alt.Chart(
            data, title="Case Fatality Ratio", width=500, height=300).mark_circle().encode(
                alt.X("report_date:T", axis=alt.Axis(title='Date Reported')),
                alt.Y('cfr:Q', axis=alt.Axis(title='Case Fatality Ratio (CFR) %'),scale=alt.Scale(domain=[50,100])),
        )
        return chart

    def chart_estimated_r(self):
        data = self.estimated_r[(self.estimated_r["estimated_r"] > 0) & (self.estimated_r["estimated_r"] < 20)]
        line = alt.Chart(data).mark_line().encode(
            x='date',
            y='estimated_r'
        )

        confidence_interval = alt.Chart(
            data, title="Estimated Reproduction Number",
            width=500, height=300).mark_area(opacity=0.3).encode(
                x=alt.Y('date', axis=alt.Axis(title='Date Reported')),
                y=alt.Y('estimated_r_lower', axis=alt.Axis(title="Estimated R")),
                y2='estimated_r_upper'
            )
        
        return confidence_interval + line
    
    def chart_cases_by_time(self):
        data = self.cases_by_time_melted[self.cases_by_time_melted["variable"].isin(
            ["Total Cases", "Total Deaths"])]
        chart = alt.Chart(
            data, title="Ebola cases and deaths", width=500, height=300).mark_circle().encode(
            alt.X("report_date:T", axis=alt.Axis(title='Date Reported')),
            alt.Y('value:Q', axis=alt.Axis(title='Number')),
            color=alt.Color('variable', legend=alt.Legend(title="", orient="top-left"))
        )
        return chart


if __name__ == "__main__":
    get_and_predict()
