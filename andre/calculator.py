from pyrsistent import m
import streamlit as st
from calculator_utilities import Groundsource, Input, Temperature, Geology, Demand, Electricity, Prerequisites, Temperature, Costs, Environment, Gis, download_report
from utilities import Frontpage
import numpy as np
from bokeh.models.widgets import Div
from datetime import date
import time 
import database as db
from PIL import Image 
import base64
import json


def main_calculation():
    placeholder_1 = st.empty()
    with placeholder_1.container():
        input = Input()
        input.process()
    if input.start_calculation == True:
        placeholder_1.empty()
        temperature = Temperature()
        geology = Geology()
        demand = Demand()
        electricity = Electricity()

        temperature.closest_station(input.lat, input.long)
        temperature.process(temperature.id)
        prerequisites = Prerequisites()
        demand.from_file(input.area, temperature.id)
        demand.update()

        with st.sidebar:
            #image = Image.open('src/bilder/egen_logo3.PNG')
            #st.image(image)
            st.title("Forutsetninger")
        #with st.expander("Endre forutsetninger"):
            st.write("""Trykk på boksene under for å endre forutsetningene som brukes i beregningen.""")
            
            st.write(""" Den største usikkerheten i beregningen er oppvarmingsbehovet. 
            Prøv å oppgi det så nøyaktig som mulig, for eksempel ved å legge inn målt 
            strømforbruk til varmtvann og oppvarming i din bolig. """)

            with st.expander("Oppvarmingsbehov"):
                demand.adjust()
                demand.update()
                demand.plot()
                
            with st.expander("Årsvarmefaktor og dekningsgrad"):
                groundsource = Groundsource()
                groundsource.adjust()
                groundsource.demands(demand.energy_arr)
                groundsource.temperature(temperature.average_temperature)
                groundsource.update()
                groundsource.calculation()
                groundsource.diagram()

            with st.expander("Strømpris"):
                electricity.find_region(input.lat, input.long)
                electricity.input()
                electricity.calculation()
                electricity.plot()

            with st.expander("Dybde til fjell"):
                geology.adjust()

            with st.expander("Kostnader"):
                costs = Costs()
                costs.calculate_investment(groundsource.heat_pump_size, groundsource.meter, geology.depth_to_bedrock)
                costs.adjust()

            with st.expander("Energimiks"):
                environment = Environment()
                environment.adjust()
                environment.calculate_emissions(demand.energy_arr, 
                groundsource.energy_gshp_compressor_arr, groundsource.energy_gshp_peak_arr)

            with st.expander("Se kart"):
                gis = Gis()
                gis.kart(temperature.lat, input.lat, geology.lat, temperature.long, input.long, geology.long, input.name, temperature.average_temperature, temperature.id)

        st.title("Resultater")          
        prerequisites.show(input.name, demand.energy_sum)
        st.caption("Du kan justere forutsetningene som ligger til grunn for beregningene i menyen til venstre")
        st.markdown("---")
           
            
        #with st.expander("Ditt bergvarmeanlegg", expanded=True):
        st.write("**Energibrønn og varmepumpe**")
        groundsource.show_results()
        st.text("")

        st.write("**Strømsparing og utslippskutt med bergvarme**")
        environment.text_after()
        with st.expander("Mer om strømsparing og utslippskutt", expanded=False):
            environment.text_before()
            environment.plot()
        st.text("")
        
        st.write("**Lønnsomhet**")
        tab1, tab2 = st.tabs(["Direkte kjøp", "Lånefinansiert"])

        with tab1:
            costs.calculate_monthly_costs(demand.energy_arr, groundsource.energy_gshp_compressor_arr, groundsource.energy_gshp_peak_arr, electricity.elprice_average, 0, 0)
            costs.operation_show_after()
            with st.expander("Mer om lønnsomhet med bergvarme"):
                costs.operation_show()
                costs.plot("Driftskostnad")
            costs.profitibality_operation()

        with tab2:
            costs.calculate_monthly_costs(demand.energy_arr, 
            groundsource.energy_gshp_compressor_arr, groundsource.energy_gshp_peak_arr, electricity.elprice_average, costs.investment, 20)

            costs.operation_and_investment_show()
            with st.expander("Mer om lønnsomhet med bergvarme"):
                costs.operation_and_investment_after()
                costs.plot("Totalkostnad")
            costs.profitibality_operation_and_investment()
        
        st.text("")
        #if st.button('⚙️ Her kan du justere forutsetningene som ligger til grunn for beregningene'):
        #    st.session_state.sidebar_state = 'collapsed' if st.session_state.sidebar_state == 'expanded' else 'expanded'
        #    st.experimental_rerun()


        

        
        #st.write(db.fetch_all_data())

    
    #st.title("Veien videre")
    

#        st.header("Endelig dimensjonering")
#        st.write(""" Vi tilbyr en komplett rapport inkl. vurderinger av grunnforhold, 
#        energi- og effektbehov og beregninger i Energy Earth Designer (EED). 
#        Rapporten utarbeides av en rådgivende ingeniør innen bergvarme for 
#        å sikre riktig dimensjonering av bergvarmeanlegg. """)
#        st.write(" Komplett dimensjoneringsrapport: NOK 5 000,- ")
#        if st.button("📧 Kontakt oss"):
#            contact_form = """
#            <form action="https://formsubmit.co/ede88ce18b03e63b0b7ed514c3939f83" method="POST">
#                <input type="hidden" name="_captcha" value="false">
#                <input type="hidden" name="_template" value="table">
#                <input type="text" name="name" placeholder="Navn" required>
#                <input type="email" name="email" placeholder="E-post" required>
#                <textarea name="message" placeholder="Melding"></textarea>
#                <input type="hidden" name="_next" value="https://bergvarmekalkulatoren.webflow.io/skjema">
#                <button type="submit">Send</button>
#            </form>
#            """

#            st.markdown(contact_form, unsafe_allow_html=True)
#            st.write("")
#            st.markdown("""---""")

#            # Use Local CSS File
#            def local_css(file_name):
#                with open(file_name) as f:
#                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
#
#            local_css("styles/form.css")

#        with open("src/rapport/Eksempelrapport.pdf", "rb") as pdf_file:
#            PDFbyte = pdf_file.read()
    
#        st.download_button(label="📈 Last ned eksempelrapport",
#                    data=PDFbyte,
#                    file_name="Eksempelrapport.pdf",
#                    mime='application/octet-stream')   


        st.title("Sett i gang - finn en seriøs entreprenør")
        st.write(""" Sjekk hvilke entreprenører som kan montere varmepumpe 
        og bore energibrønn hos deg - riktig og trygt! Bruk en 
        entreprenør godkjent av Varmepumpeforeningen. """)


        # Standard Base64 Encoding
        data = {}
        data['bronndybde'] = groundsource.meter
        data['varmepumpe'] = groundsource.heat_pump_size
        data['oppvarmingsbehov'] = int(demand.space_heating_sum + demand.dhw_sum)
        data['boligareal'] = input.area
        json_data = json.dumps(data)      
        encodedBytes = base64.b64encode(json_data.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")

        address_str = input.name.split(",")[0].split(" ")

        st.write("Vi råder deg også til å:")
        st.write("- • Få entreprenør til å komme på befaring")
        st.write("- • Vurdere både pris og kvalitet")
        st.write("- • Skrive kontrakt før arbeidet starter")

        st.text("")
        if st.button("👷 Sjekk her hvem som kan installere bergvarme i din bolig"):
            st.markdown(f'<meta http-equiv="refresh" content="0;url=https://www.varmepumpeinfo.no/forhandler?postnr={input.postcode}&adresse={address_str[0]}+{address_str[1]}&type=bergvarme&meta={encodedStr}">', unsafe_allow_html=True)

        #st.info("Du kan justere forutsetningene som ligger til grunn for beregningene i menyen til venstre")

        #download_report(temperature.average_temperature, temperature.id, demand.space_heating_sum, 
        #demand.dhw_sum, groundsource.kWh_per_meter, groundsource.energy_gshp_delivered_sum, groundsource.energy_gshp_compressor_sum, 
        #groundsource.energy_gshp_peak_sum, groundsource.cop, groundsource.coverage, electricity.region, electricity.elprice_average)
        st.text("")
        st.text("")
        st.text("")
        st.markdown("""---""")
        prerequisites.disclaimer()
        st.text("")
        st.text("")
        st.text("")
        st.caption('Et verktøy fra Asplan Viak og Norsk Varmepeumpeforening (NOVAP) 🌱')

        #Database
        db.insert_data(input.name, input.lat, input.long, input.area, temperature.average_temperature, temperature.id, 
            electricity.region, groundsource.kWh_per_meter, demand.space_heating_sum, 
            demand.dhw_sum, groundsource.cop, groundsource.coverage, electricity.elprice_average, 
            groundsource.energy_gshp_delivered_sum, groundsource.energy_gshp_compressor_sum, 
            groundsource.energy_gshp_peak_sum, date.today().strftime("%d/%m/%Y"))    