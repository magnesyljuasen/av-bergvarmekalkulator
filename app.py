import streamlit as st
import time
from src.scripts import input, adjust, temperature, demand, geology, geoenergy, environment, costs

st.set_page_config(
    page_title="Bergvarmekalkulatoren",
    layout="centered")

with open("src/styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

# adresse og boligareal
input_obj = input.Input()

# hente inn temperatur
temperature_obj = temperature.Temperature()
temperature_obj.closest_station(input_obj.lat, input_obj.long)
temperature_obj.process(temperature_obj.id)

# beregne energibehov
demand_obj = demand.Demand()
demand_obj.from_file(input_obj.area, temperature_obj.id)
demand_obj.update()

# justere forutsetninger
adjust_obj = adjust.Adjust(1.5, demand_obj.space_heating_sum, demand_obj.dhw_sum, 10, 5, 3.0)
adjust_obj.adjust_input()

# resultater
if adjust_obj.start == True:
    st.title('Resultater')

    # grunnvarmeberegning
    geoenergy_obj = geoenergy.Geoenergy((demand_obj.dhw_arr + demand_obj.space_heating_arr), 
    temperature_obj.average_temperature, adjust_obj.cop, adjust_obj.thermal_conductivity, 
    adjust_obj.groundwater_table)
    st.subheader(f'- Brønnmeter : {int(geoenergy_obj.meter)} m')
    st.subheader(f'- kWh/m : {geoenergy_obj.kWh_per_meter} m')
    st.subheader(f'- Minimumstemperatur i borehull : {"{:.2f}".format(geoenergy_obj.min_temperature)} grader')
    
    
