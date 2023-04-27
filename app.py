import streamlit as st
import time
from src.scripts import input, adjust, temperature, demand, geology, geoenergy, environment, costs

st.set_page_config(
    page_title="Bergvarmekalkulatoren",
    layout="centered")

with open("src/styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

placeholder_1 = st.empty()
with placeholder_1.container():
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
    adjust_obj = adjust.Adjust(1.5, demand_obj.space_heating_sum, demand_obj.dhw_sum, 10, 5, 3.0, demand_obj.dhw_arr, demand_obj.space_heating_arr)

# resultater
if adjust_obj.start == True:
    placeholder_1.empty()
    st.title('Resultater')
    st.write("**Energibrønn og varmepumpe**")
    # grunnvarmeberegning
    energy_arr = (demand_obj.dhw_arr + demand_obj.space_heating_arr)
    geoenergy_obj = geoenergy.Geoenergy(energy_arr, 
    temperature_obj.average_temperature, adjust_obj.cop, adjust_obj.thermal_conductivity, 
    adjust_obj.groundwater_table, adjust_obj.energycoverage)

    environment = environment.Environment(adjust_obj.energyoption, adjust_obj.energymix)
    environment.calculate_emissions(energy_arr, 
    geoenergy_obj.energy_gshp_compressor_arr, geoenergy_obj.energy_gshp_peak_arr)
    st.write("**Strømsparing og utslippskutt med bergvarme**")
    environment.text_after()
    with st.expander("Mer om strømsparing og utslippskutt", expanded=False):
        environment.text_before()
        environment.plot()
    st.text("")

    costs = costs.Costs(adjust_obj.payment_time, adjust_obj.interest)
    costs.calculate_investment(geoenergy_obj.heat_pump_size, geoenergy_obj.meter, adjust_obj.depth_to_bedrock)

    st.write("**Lønnsomhet**")
    tab1, tab2 = st.tabs(["Direkte kjøp", "Lånefinansiert"])

    with tab1:
        costs.calculate_monthly_costs(energy_arr, geoenergy_obj.energy_gshp_compressor_arr, geoenergy_obj.energy_gshp_peak_arr, adjust_obj.elprice, 0)
        costs.operation_show_after()
        with st.expander("Mer om lønnsomhet med bergvarme"):
            costs.operation_show()
            costs.plot("Driftskostnad")
        costs.profitibality_operation()

    with tab2:
        costs.calculate_monthly_costs(energy_arr, 
        geoenergy_obj.energy_gshp_compressor_arr, geoenergy_obj.energy_gshp_peak_arr, adjust_obj.elprice, costs.investment)

        costs.operation_and_investment_show()
        with st.expander("Mer om lønnsomhet med bergvarme"):
            costs.operation_and_investment_after()
            costs.plot("Totalkostnad")
        costs.profitibality_operation_and_investment()
    
    st.text("")
    
    
