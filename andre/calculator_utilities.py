from bz2 import compress
import streamlit as st
from utilities import Frontpage
import numpy as np
import pandas as pd
import altair as alt
import mpu
from shapely.geometry import Point, shape
import json
#from annotated_text import annotated_text
import pydeck as pdk
from io import BytesIO
from datetime import date
from fpdf import FPDF
from PIL import Image
import requests
from st_keyup import st_keyup
import time
from streamlit_folium import st_folium
import folium
import base64

def render_svg(svg):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)

def hour_to_month (hourly_array):
    monthly_array = []
    summert = 0
    for i in range(0, len(hourly_array)):
        verdi = hourly_array[i]
        if np.isnan(verdi):
            verdi = 0
        summert = verdi + summert
        if i == 744 or i == 1416 or i == 2160 or i == 2880 \
                or i == 3624 or i == 4344 or i == 5088 or i == 5832 \
                or i == 6552 or i == 7296 or i == 8016 or i == 8759:
            monthly_array.append(int(summert))
            summert = 0
    return monthly_array  


class Prerequisites:
    def __init__(self):
        pass

    def show(self, address, energy):
        st.write(f"📍{address} | ⚡Estimert oppvarmingsbehov: {round(energy, -1):,} kWh".replace(',', ' '))

    def disclaimer(self):
        with st.container():
            st.write("**Bergvarmekalkulatoren erstatter ikke faktiske beregninger for din bolig**")

            st.write(""" Beregningene i bergvarmekalkulatoren er forenklet, og tar ikke hensyn til alle forhold. 
            Kalkulatoren er ment for å gi en pekepinn på størrelse, lønnsomhet og miljøgevinst for et bergvarmeanlegg, 
            og ikke som et verktøy for å dimensjonere.""")

            st.write(""" *Asplan Viak og Norsk Varmepumpeforening tar ikke ansvar for 
            resultatene hvis disse forenklete beregningene brukes til å dimensjonere et bergvarmeanlegg.* """)

        
      

    def calculation(self):
        diff = self.elprice_average - self.elspot_average
        if diff == 0:
            self.elprice_hourly = self.elspot_hourly
        else:
            self.elprice_hourly = self.elspot_hourly + diff

    def plot(self):
        x = np.arange(8760)
        source = pd.DataFrame({
        'x': x,
        'y': self.elprice_hourly})

        c = alt.Chart(source).mark_line().encode(
            x=alt.X('x', scale=alt.Scale(domain=[0,8760]), title="Timer i ett år"),
            y=alt.Y('y', scale=alt.Scale(domain=[0,7]), title="Pris på strøm (kr/kWh)"),
            color = alt.value("#1d3c34"))
        st.altair_chart(c, use_container_width=True)


class Geology:
    def __init__(self):
        self.depth_to_bedrock = int
        self.lat = 5
        self.long = 10

    def adjust(self):
        with st.form('4'):
            self.depth_to_bedrock = st.number_input("Oppgi dybde til fjell [m]", min_value= 0, value=0, max_value=150, 
            help = """Dybde til fjell påvirker kostnaden for å bore energibrønn, og 
            kan variere mye fra sted til sted. Brønnborer bør sjekke dette 
            opp mot NGU sine databaser for grunnvannsbrønner og grunnundersøkelser. """)
            submitted = st.form_submit_button("Oppdater")

class Input:
    def __init__(self):
        self.lat = float
        self.long = float
        self.name = str
        self.area = int
        self.start_calculation = False

    def search(self, adr):
        options_list = []
        lat_list = []
        long_list = []
        postnummer_list = []
        r = requests.get(f"https://ws.geonorge.no/adresser/v1/sok?sok={adr}&fuzzy=true&treffPerSide=5&sokemodus=OR", auth=('user', 'pass'))
        if r.status_code == 200 and len(r.json()["adresser"]) == 5:   
            for i in range(0, 5):
                json = r.json()["adresser"][i]
                adresse_tekst = json["adressetekst"]
                poststed = (json["poststed"]).capitalize()
                postnummer = json["postnummer"]
                postnummer_list.append(postnummer)
                opt = f"{adresse_tekst}, {poststed}"
                options_list.append(opt)
                lat_list.append(json["representasjonspunkt"]["lat"])
                long_list.append(json["representasjonspunkt"]["lon"])
        return options_list, lat_list, long_list, postnummer_list
            
    def process(self):
        st.title("Hvor befinner boligen seg?")
        adr = st_keyup("📍 Skriv inn adresse", key="adresse1")
        if len(adr) == 0:
            Frontpage()
        options_list, lat_list, long_list, postcode_list = self.search(adr)
        c1, c2 = st.columns(2)
        if len(options_list) > 0:
            with c1:
                s1 = st.checkbox(options_list[0])
                s2 = st.checkbox(options_list[1])
            with c2:
                s3 = st.checkbox(options_list[2])
                s4 = st.checkbox(options_list[3])

            if s1 == False and s2 == False and s3 == False and s4 == False:
                selected_adr = 0
            elif s1 == False and s2 == False and s3 == False and s4 == True:
                selected_adr = options_list[3]
                selected_lat = lat_list[3]
                selected_long = long_list[3]
                selected_postcode = postcode_list[3]  
            elif s1 == False and s2 == False and s3 == True and s4 == False:
                selected_adr = options_list[2]
                selected_lat = lat_list[2]
                selected_long = long_list[2]
                selected_postcode = postcode_list[2]
            elif s1 == False and s2 == True and s3 == False and s4 == False:
                selected_adr = options_list[1]
                selected_lat = lat_list[1]
                selected_long = long_list[1]
                selected_postcode = postcode_list[1]
            elif s1 == True and s2 == False and s3 == False and s4 == False:
                selected_adr = options_list[0]
                selected_lat = lat_list[0]
                selected_long = long_list[0]
                selected_postcode = postcode_list[0]
            else:
                selected_adr = 0
                st.error("Du kan kun velge én adresse!", icon="🚨")

            if selected_adr != 0:
                st.title("Hvor stor er boligen?")
                selected_area = st_keyup(f"🏠 Tast inn oppvarmet boligareal [m\u00B2]", key="areal2")
                

                if len(selected_area) == 0:
                    st.markdown("---")
                elif not selected_area.isnumeric():
                    st.error("Input må være tall!", icon="🚨")
                    st.markdown("---")
                else:
                    if len(selected_area) > 0 and int(selected_area) < 100 or int(selected_area) > 500:
                        time.sleep(2)
                        st.error("Oppvarmet boligareal må være mellom 100 og 500 m\u00b2", icon="🚨")
                    elif len(selected_area) > 0 and int(selected_area) >= 100 and int(selected_area) <= 500:
                        st.markdown("---")
                        self.start_calculation = True
                        self.lat = selected_lat
                        self.long = selected_long
                        self.name = selected_adr
                        self.area = int(selected_area)
                        self.postcode = selected_postcode

                        

        
class Demand:
    def __init__(self):
        self.space_heating_arr = np.zeros(8760)
        self.dhw_arr = np.zeros(8760)
        self.energy_arr = np.zeros(8760)
        self.space_heating_sum = int
        self.dhw_sum = int
        self.energy_sum = int
    
    def update(self):
        self.space_heating_sum = int(np.sum(self.space_heating_arr))
        self.dhw_sum = int(np.sum(self.dhw_arr))
        self.energy_sum = int(np.sum(self.energy_arr))

    def from_file(self, area, weather_station_id):
        factor = 1
        dhw = 'src/database/' + 'SN180' + '_dhw.csv'
        space_heating = 'src/temperature/_' + weather_station_id + '_romoppvarming.csv'
        self.dhw_arr = (pd.read_csv(dhw, sep=',', on_bad_lines='skip').to_numpy() * area) * factor
        self.space_heating_arr = (pd.read_csv(space_heating, sep=',', on_bad_lines='skip').to_numpy() * area) * factor
        self.energy_arr = self.dhw_arr + self.space_heating_arr

    def plot(self):
        dhw_arr = hour_to_month (self.dhw_arr)
        romoppvarming_arr = hour_to_month (self.space_heating_arr)
        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        data = pd.DataFrame({'Måneder' : months, 'Romoppvarmingsbehov' : romoppvarming_arr, 'Varmtvannsbehov' : dhw_arr, })
        c = alt.Chart(data).transform_fold(
            ['Romoppvarmingsbehov', 'Varmtvannsbehov'],
            as_=['Forklaring', 'Oppvarmingsbehov (kWh)']).mark_bar().encode(
            x=alt.X('Måneder:N', sort=months, title=None),
            y='Oppvarmingsbehov (kWh):Q',
            color=alt.Color('Forklaring:N', scale=alt.Scale(domain=['Romoppvarmingsbehov', 'Varmtvannsbehov'], 
            range=['#4a625c', '#8e9d99']), legend=alt.Legend(orient='top', direction='vertical', title=None)))
        st.altair_chart(c, use_container_width=True)

    def adjust(self):
        with st.form('1'):
            dhw_sum = self.dhw_sum
            dhw_sum_new = st.number_input('Varmtvann [kWh]', min_value = int(round(dhw_sum - dhw_sum/2, -1)), 
            max_value = int(round(dhw_sum + dhw_sum/2, -1)), value = round(dhw_sum, -1), step = int(500), help="""
            Erfaring viser at varmtvannsbehovet avhenger 
            av hvor mange som bor i en bolig, og bør justeres etter dette. 
            Bor dere mange i din bolig, bør du øke dette tallet. """)

            space_heating_sum = self.space_heating_sum
            space_heating_sum_new = st.number_input('Romoppvarming [kWh]', min_value = int(round(space_heating_sum - space_heating_sum/2, -1)), 
            max_value = int(round(space_heating_sum + space_heating_sum/2, -1)), value = round(space_heating_sum, -1), step = int(500), help= """
            Behovet for romoppvarming er beregnet ut fra oppgitt oppvarmet areal, 
            byggeår og temperaturdata fra nærmeste værstasjon for de 30 siste årene. """)
            dhew_percentage = dhw_sum_new / dhw_sum
            romoppvarming_prosent = space_heating_sum_new / space_heating_sum

            self.dhw_arr = (self.dhw_arr * dhew_percentage).flatten()
            self.space_heating_arr = (self.space_heating_arr * romoppvarming_prosent).flatten()
            self.energy_arr = (self.dhw_arr + self.space_heating_arr).flatten()
            submitted = st.form_submit_button("Oppdater")
    #---


class Temperature:
    def __init__(self):
        self.temperature_arr = np.zeros(8760)
        self.lat = float
        self.long = float
        self.id = str

    def from_file(self, id):
        temperature_array = 'src/temperature/_' + id + '_temperatur.csv'
        self.temperature_arr = pd.read_csv(temperature_array, sep=',', on_bad_lines='skip').to_numpy()

    def process(self, id):
        self.from_file(id)
        average = float("{:.2f}".format(np.average(self.temperature_arr)))
        text = ""
        if average < 3:
            text = """ Ettersom gjennomsnittstemperaturen er lav kan det være en 
            driftsstrategi å fryse grunnvannet i energibrønnen (merk at dette ikke 
            må gjøres hvis det er sensitive løsmasser / kvikkleire i området). """
        self.average_temperature = average
        self.average_temperature_text = text

    @st.cache
    def import_csv (self):
        station_list = pd.read_csv('src/temperature/Stasjoner.csv', sep=',',on_bad_lines='skip')
        return station_list

    def closest_station (self, lat, long):
        distance_min = 1000000
        df = self.import_csv()
        for i in range (0, len (df)):
            distance = mpu.haversine_distance((df.iat [i,1], df.iat [i,2]), (lat, long))
            if distance != 0 and distance < distance_min:
                distance_min = distance
                self.id = df.iat [i,0]
                self.lat = df.iat [i,1]
                self.long = df.iat [i,2]
                self.distance_min = distance_min


class Groundsource:
    def __init__(self):
        self.coverage = int
        self.cop = float
        self.energy_gshp_arr = np.array(0)
        self.energy_gshp_sum = int
        self.heat_pump_size = float
    
    def update(self):
        self.energy_sum = int(np.sum(self.energy_arr))

    def adjust(self):
        with st.form("2"):    
            self.coverage = st.number_input("Energidekningsgrad for bergvarme [%]", 
            value=98, min_value=80, max_value=100, step = 1, 
            help="""Dekningsgraden viser hvor stor andel av boligens varmebehov bergvarmeanlegget 
            skal dekke. 100 % betyr at det dekker all oppvarming. Er dekningsgraden under 100 %, 
            trenger du litt vedfyring i tillegg  på de aller kaldeste dagene.  """)
            
            self.cop = st.number_input("Årsvarmefaktor (SCOP) til varmepumpen", 
            value=3.0, min_value=2.0, max_value=4.0, step = 0.1, 
            help="""Årsvarmefaktoren forteller hvor mye varme anlegget 
            leverer i forhold til hvor mye strøm det bruker i løpet av et år. """)

            submitted = st.form_submit_button("Oppdater")

    def demands(self, energy_arr):
        self.energy_arr = energy_arr
        self.update()

    def temperature(self, undisturbed_temperature):
        self.undisturbed_temperature = undisturbed_temperature

    def calculation(self):
        self.energy_gshp_arr, self.energy_gshp_sum, self.heat_pump_size = self.coverage_calculation()
        self.heat_pump_size_adjustment()
        self.energy_gshp_delivered_arr, self.energy_gshp_compressor_arr, self.energy_gshp_peak_arr, \
        self.energy_gshp_delivered_sum, self.energy_gshp_compressor_sum, self.energy_gshp_peak_sum = self.cop_calculation()
        self.meter = self.meter_calculation()
        self.number_of_wells = self.wellnumber_calculation()

    @st.cache
    def coverage_calculation(self):
        coverage = self.coverage
        energy_arr = self.energy_arr
        energy_sum = self.energy_sum
        heat_pump_size = max(energy_arr)
        calculated_coverage = 100.5
        if coverage == 100:
            return np.array(energy_arr), int(np.sum(energy_arr)), float("{:.1f}".format(heat_pump_size))

        while (calculated_coverage / coverage) > 1:
            tmp_list = np.zeros (8760)
            for i, effect in enumerate (energy_arr):
                if effect > heat_pump_size:
                    tmp_list[i] = heat_pump_size
                else:
                    tmp_list[i] = effect
            
            calculated_coverage = (sum (tmp_list) / energy_sum) * 100
            heat_pump_size -= 0.05

        return np.array(tmp_list), int(np.sum(tmp_list)), float("{:.1f}".format(heat_pump_size))

    def cop_calculation(self):
        cop = self.cop
        energy_arr = self.energy_arr
        energy_gshp_arr = self.energy_gshp_arr
        energy_gshp_delivered_arr = energy_gshp_arr - energy_gshp_arr / cop
        energy_gshp_compressor_arr = energy_gshp_arr - energy_gshp_delivered_arr
        energy_gshp_peak_arr = energy_arr - energy_gshp_arr

        energy_gshp_delivered_sum = int(np.sum(energy_gshp_delivered_arr))
        energy_gshp_compressor_sum = int(np.sum(energy_gshp_compressor_arr))
        energy_gshp_peak_sum = int(np.sum(energy_gshp_peak_arr))

        return energy_gshp_delivered_arr, energy_gshp_compressor_arr, energy_gshp_peak_arr, energy_gshp_delivered_sum, energy_gshp_compressor_sum, energy_gshp_peak_sum

    def meter_calculation(self):
        temperature = self.undisturbed_temperature
        kWh_per_meter = 0.0011*temperature**4 - 0.0537*temperature**3 + 1.0318*temperature**2 + 6.2816*temperature + 36.192
        upper_limit = 110
        lower_limit = 70
        if kWh_per_meter > upper_limit:
            kWh_per_meter = upper_limit
        if kWh_per_meter < lower_limit:
            kWh_per_meter = lower_limit
        self.kWh_per_meter = kWh_per_meter
        meters = int(self.energy_gshp_delivered_sum / kWh_per_meter)
        if meters < 80:
            meters = 80
        return meters

    def wellnumber_calculation(self):
        meters = self.meter
        bronnlengde = 0
        for i in range(1,10):
            bronnlengde += 350
            if meters <= bronnlengde:
                return i

    def heat_pump_size_adjustment(self):
        heat_pump_size = self.heat_pump_size

        #if heat_pump_size > 0 and heat_pump_size < 6:
        #    heat_pump_size = 6
        #if heat_pump_size > 6 and heat_pump_size < 8:
        #    heat_pump_size = 8
        #if heat_pump_size > 8 and heat_pump_size < 10:
        #    heat_pump_size = 10
        #if heat_pump_size > 10 and heat_pump_size < 12:
        #    heat_pump_size = 12
        #if heat_pump_size > 12 and heat_pump_size < 15:
        #    heat_pump_size = 15
        #if heat_pump_size > 14 and heat_pump_size > 17:
        #    heat_pump_size = 17

        self.heat_pump_size = heat_pump_size

    def diagram(self):
        wide_form = pd.DataFrame({
            'Varighet (timer)' : np.array(range(0, len(self.energy_arr))),
            'Spisslast (ikke bergvarme)' : np.sort(self.energy_arr)[::-1], 
            'Levert energi fra brønn(er)' : np.sort(self.energy_gshp_arr)[::-1],
            'Strømforbruk varmepumpe' : np.sort(self.energy_gshp_compressor_arr)[::-1]
            })

        c = alt.Chart(wide_form).transform_fold(
            ['Spisslast (ikke bergvarme)', 'Levert energi fra brønn(er)', 'Strømforbruk varmepumpe'],
            as_=['key', 'Effekt (kW)']).mark_area().encode(
                x=alt.X('Varighet (timer):Q', scale=alt.Scale(domain=[0, 8760])),
                y='Effekt (kW):Q',
                color=alt.Color('key:N', scale=alt.Scale(domain=['Spisslast (ikke bergvarme)', 'Levert energi fra brønn(er)', 'Strømforbruk varmepumpe'], 
                range=['#ffdb9a', '#48a23f', '#1d3c34']), legend=alt.Legend(orient='top', direction='vertical', title=None))
            )

        st.altair_chart(c, use_container_width=True)

    def show_results(self):
        #st.subheader("Forenklet dimensjonering")
        number_of_wells = self.number_of_wells
        meters = self.meter
        heat_pump_size = self.heat_pump_size
        text = " brønn"
        text1 = " energibrønn"
        text2 = "dybde"
        
        column_1, column_2 = st.columns(2)
        with column_1:
            svg = """ <svg width="27" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="505" y="120" width="27" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-505 -120)"><path d="M18.6875 10.8333C20.9312 10.8333 22.75 12.6522 22.75 14.8958 22.75 17.1395 20.9312 18.9583 18.6875 18.9583L2.97917 18.9583C2.82959 18.9583 2.70833 19.0796 2.70833 19.2292 2.70833 19.3787 2.82959 19.5 2.97917 19.5L18.6875 19.5C21.2303 19.5 23.2917 17.4386 23.2917 14.8958 23.2917 12.353 21.2303 10.2917 18.6875 10.2917L3.63946 10.2917C3.63797 10.2916 3.63678 10.2904 3.63678 10.2889 3.6368 10.2882 3.63708 10.2875 3.63756 10.2871L7.23315 6.69148C7.33706 6.58388 7.33409 6.41244 7.22648 6.30852 7.12154 6.20715 6.95514 6.20715 6.85019 6.30852L2.78769 10.371C2.68196 10.4768 2.68196 10.6482 2.78769 10.754L6.85019 14.8165C6.95779 14.9204 7.12923 14.9174 7.23315 14.8098 7.33452 14.7049 7.33452 14.5385 7.23315 14.4335L3.63756 10.8379C3.63651 10.8369 3.63653 10.8351 3.63759 10.8341 3.6381 10.8336 3.63875 10.8333 3.63946 10.8333Z" stroke="#1D3C34" stroke-width="0.270833" fill="#1D3C34" transform="matrix(6.12323e-17 1 -1.03846 6.35874e-17 532 120)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Brønndybde ", value=f"{meters} m")
        with column_2:
            svg = """ <svg width="31" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="395" y="267" width="31" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-395 -267)"><path d="M24.3005 0.230906 28.8817 0.230906 28.8817 25.7691 24.3005 25.7691Z" stroke="#1E3D35" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M1.40391 2.48455 1.40391 25.5936 6.41918 25.5936 6.41918 2.48455C4.70124 1.49627 3.02948 1.44085 1.40391 2.48455Z" stroke="#1E3D35" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M24.3005 25.7691 1.23766 25.7691" stroke="#1F3E36" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M24.3005 0.230906 6.59467 0.230906 6.59467 25.7691" stroke="#1F3E36" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="#FBFDF6" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M24.3005 17.6874 6.59467 17.6874" stroke="#1F3E36" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M24.3005 8.33108 6.59467 8.33108" stroke="#1F3E36" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M9.71652 12.4874 10.1691 12.4874 10.1691 14.0114 11.222 14.7133 11.222 16.108 10.2153 16.8007 9.71652 16.8007" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M9.72575 12.4874 9.26394 12.4874 9.26394 14.0114 8.22025 14.7133 8.22025 16.108 9.21776 16.8007 9.72575 16.8007" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M14.27 12.4874 14.7226 12.4874 14.7226 14.0114 15.7663 14.7133 15.7663 16.108 14.7687 16.8007 14.27 16.8007" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M14.27 12.4874 13.8174 12.4874 13.8174 14.0114 12.7645 14.7133 12.7645 16.108 13.7712 16.8007 14.27 16.8007" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M1.40391 5.90195 0.230906 5.90195 0.230906 10.9542 1.40391 10.9542" stroke="#1E3D35" stroke-width="0.461812" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M1.40391 13.0046 0.230906 13.0046 0.230906 25.0025 1.40391 25.0025" stroke="#1E3D35" stroke-width="0.461812" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M28.0412 4.58117 25.2611 4.58117 25.2611 2.73393 25.2611 2.10586 28.0412 2.10586 28.0412 4.58117Z" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M25.4366 2.73393 28.0412 2.73393" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M25.4366 3.34352 28.0412 3.34352" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M25.4366 3.95311 28.0412 3.95311" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M9.71652 20.6799 10.1691 20.6799 10.1691 22.2131 11.222 22.9059 11.222 24.3005 10.2153 25.0025 9.71652 25.0025" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M9.72575 20.6799 9.26394 20.6799 9.26394 22.2131 8.22025 22.9059 8.22025 24.3005 9.21776 25.0025 9.72575 25.0025" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M14.27 20.6799 14.7226 20.6799 14.7226 22.2131 15.7663 22.9059 15.7663 24.3005 14.7687 25.0025 14.27 25.0025" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M14.27 20.6799 13.8174 20.6799 13.8174 22.2131 12.7645 22.9059 12.7645 24.3005 13.7712 25.0025 14.27 25.0025" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M20.0149 1.05293 23.4139 1.05293 23.4139 7.56448 20.0149 7.56448Z" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M17.9552 13.0046 23.4046 13.0046 23.4046 15.5538 17.9552 15.5538Z" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M19.0913 11.6931C19.0913 11.9073 18.9176 12.081 18.7034 12.081 18.4891 12.081 18.3155 11.9073 18.3155 11.6931 18.3155 11.4788 18.4891 11.3052 18.7034 11.3052 18.9176 11.3052 19.0913 11.4788 19.0913 11.6931Z" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M18.7034 13.0046 18.7034 12.081" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M20.4028 11.6931C20.4028 11.9073 20.2292 12.081 20.0149 12.081 19.8007 12.081 19.627 11.9073 19.627 11.6931 19.627 11.4788 19.8007 11.3052 20.0149 11.3052 20.2292 11.3052 20.4028 11.4788 20.4028 11.6931Z" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M20.0149 13.0046 20.0149 12.081" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M21.7421 11.6931C21.7421 11.9073 21.5684 12.081 21.3542 12.081 21.1399 12.081 20.9663 11.9073 20.9663 11.6931 20.9663 11.4788 21.1399 11.3052 21.3542 11.3052 21.5684 11.3052 21.7421 11.4788 21.7421 11.6931Z" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M21.3542 13.0046 21.3542 12.081" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M23.0536 11.6931C23.0536 11.9073 22.88 12.081 22.6657 12.081 22.4515 12.081 22.2778 11.9073 22.2778 11.6931 22.2778 11.4788 22.4515 11.3052 22.6657 11.3052 22.88 11.3052 23.0536 11.4788 23.0536 11.6931Z" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#F3F8E8" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M22.6657 13.0046 22.6657 12.081" stroke="#1E3D35" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Varmepumpestørrelse", value=str(int(heat_pump_size)) + " kW")

        if number_of_wells > 1:
            text = " brønner" 
            text1 = " energibrønner"
            text2 = "total dybde"
            st.info(f"Brønndybden bør fordeles på {number_of_wells} brønner á {int(meters/number_of_wells)} m med 15 meter avstand")

        with st.expander("Mer om brønndybde og varmepumpestørrelse"):
            st.write(""" Vi har gjort en forenklet beregning for å dimensjonere et bergvarmeanlegg med 
            energibrønn og varmepumpe for din bolig. Dybde på energibrønn og størrelse på varmepumpe 
            beregnes ut ifra et anslått oppvarmingsbehov for boligen din og antakelser om 
            egenskapene til berggrunnen der du bor. Varmepumpestørrelsen gjelder on/off 
            og ikke varmepumper med inverterstyrt kompressor.""")
        
            st.write(""" Før du kan installere bergvarme, må entreprenøren gjøre en grundigere beregning. 
            Den må baseres på reelt oppvarmings- og kjølebehov, en mer nøyaktig vurdering av grunnforholdene, 
            inkludert berggrunnens termiske egenskaper, og simuleringer av temperaturen i energibrønnen. """)

class Costs:
    def __init__(self):
        pass

    def calculate_investment (self, heat_pump_size, meter, depth_to_bedrock):
        heat_pump_price = 141000
        
        if heat_pump_size > 12:
            heat_pump_price = int(heat_pump_price + (heat_pump_size - 12) * 10000)
        
        graving_pris = 30000
        rigg_pris = 15000
        etablering_pris = 3500
        odex_sko_pris = 575
        bunnlodd_pris = 1000
        lokk_pris = 700
        odex_i_losmasser_pris = 700  # per meter
        fjellboring_pris = 170  # per meter
        kollektor_pris = 90  # per meter

        kollektor = (meter - 1) * kollektor_pris
        boring = ((meter - depth_to_bedrock) * fjellboring_pris) + (depth_to_bedrock * odex_i_losmasser_pris)
        boring_faste_kostnader = etablering_pris + odex_sko_pris + bunnlodd_pris + lokk_pris + rigg_pris + graving_pris

        energibronn_pris = int(kollektor) + int(boring) + int(boring_faste_kostnader)
        komplett_pris = energibronn_pris + heat_pump_price
        self.investment = int(komplett_pris)

    def adjust(self):
        with st.form("5"):
            investment = self.investment
            self.investment = st.number_input("Juster investeringskostnad [kr]", 
            min_value = 10000, value = int(round(investment,-1)), 
            max_value = 1000000, step = 5000)
            self.interest = st.number_input("Juster effektiv rente [%]", value = 1.0, min_value = 0.0, max_value = 20.0, step = 0.1)
            submitted = st.form_submit_button("Oppdater")

    def calculate_monthly_costs(self, energy_arr, compressor_arr, peak_arr, elprice_arr, investment, repayment_period):
        
        instalment = 0
        if investment != 0:
            monthly_antall = repayment_period * 12
            monthly_rente = (self.interest/100) / 12
            if monthly_rente > 0:
                instalment = investment / ((1 - (1 / (1 + monthly_rente) ** monthly_antall)) / monthly_rente)
            else:
                instalment = investment / monthly_antall

        el_cost_hourly = energy_arr * elprice_arr
        gshp_cost_hourly = (compressor_arr + peak_arr) * elprice_arr

        self.el_cost_monthly = np.array(hour_to_month(el_cost_hourly))
        self.gshp_cost_monthly = np.array(hour_to_month(gshp_cost_hourly)) + instalment

        self.el_cost_sum = np.sum(self.el_cost_monthly)
        self.gshp_cost_sum = np.sum(self.gshp_cost_monthly)
        self.savings_sum = self.el_cost_sum - self.gshp_cost_sum


    def plot(self, kostnad):
        gshp_text_1 = "Bergvarme"        
        gshp_text_2 = f"{kostnad}: " + str(int(round(self.gshp_cost_sum, -1))) + " kr/år"
        el_text_1 = "Elektrisk oppvarming"
        el_text_2 = f"{kostnad}: " + str(int(round(self.el_cost_sum, -1))) + " kr/år"
        
        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        wide_form = pd.DataFrame({
            'Måneder' : months,
            gshp_text_1 : self.gshp_cost_monthly, 
            el_text_1 : self.el_cost_monthly})

        c1 = alt.Chart(wide_form).transform_fold(
            [gshp_text_1, el_text_1],
            as_=['key', 'Kostnader (kr)']).mark_bar(opacity=1).encode(
                x=alt.X('Måneder:N', sort=months, title=None),
                y=alt.Y('Kostnader (kr):Q',stack=None),
                color=alt.Color('key:N', scale=alt.Scale(domain=[gshp_text_1], 
                range=['#48a23f']), legend=alt.Legend(orient='top', 
                direction='vertical', title=gshp_text_2))).configure_view(strokeWidth=0)

        c2 = alt.Chart(wide_form).transform_fold(
            [gshp_text_1, el_text_1],
            as_=['key', 'Kostnader (kr)']).mark_bar(opacity=1).encode(
                x=alt.X('Måneder:N', sort=months, title=None),
                y=alt.Y('Kostnader (kr):Q',stack=None, title=None),
                color=alt.Color('key:N', scale=alt.Scale(domain=[el_text_1], 
                range=['#880808']), legend=alt.Legend(orient='top', 
                direction='vertical', title=el_text_2))).configure_view(strokeWidth=0)

        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(c1, use_container_width=True)  
        with col2:
            st.altair_chart(c2, use_container_width=True) 

    def operation_show(self):
        st.write(""" Investeringskostnaden omfatter en komplett installasjon av et 
        bergvarmeanlegg, inkludert energibrønn, varmepumpe og installasjon. 
        Merk at dette er et estimat. Endelig pris fastsettes av leverandøren. """)

        st.write(""" Investeringskostnaden dekker ikke installasjon av vannbåren varme i boligen. 
        Søylediagrammene viser årlige driftskostnader med bergvarme 
        sammenlignet med elektrisk oppvarming. """)

    def operation_show_after(self):
        investment = int(round(self.investment, -1))
        operation_saving = int(round(self.savings_sum, -1))
        total_saving = int(round(self.savings_sum*20 - self.investment,-1))
        self.total_saving = total_saving
        c1, c2, c3 = st.columns(3)
        with c1:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="369" y="79" width="26" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-369 -79)"><path d="M25.4011 12.9974C25.4011 19.8478 19.8478 25.4011 12.9974 25.4011 6.14699 25.4011 0.593654 19.8478 0.593654 12.9974 0.593654 6.14699 6.14699 0.593654 12.9974 0.593654 19.8478 0.593654 25.4011 6.14699 25.4011 12.9974Z" stroke="#1E3D35" stroke-width="0.757136" stroke-miterlimit="10" fill="#FBFDF6" transform="matrix(1 0 0 1.03846 369 79)"/><path d="M16.7905 6.98727 11.8101 19.0075 11.6997 19.0075 9.20954 12.9974" stroke="#1E3D35" stroke-width="0.757136" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.03846 369 79)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Estimert investeringskostnad", value= f"{investment:,} kr".replace(',', ' '))
        with c2:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Reduserte utgifter til oppvarming", value= f"{operation_saving:,} kr/år".replace(',', ' '))
        with c3:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Samlet besparelse etter 20 år", value = f"{total_saving:,} kr".replace(',', ' '))
             
    def operation_and_investment_show(self):
        investment = int(round(self.investment, -1))
        savings1 = int(round(self.savings_sum, -1))
        savings2 = int(round(self.savings_sum*20, -1))
        c1, c2, c3 = st.columns(3)
        with c1:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="369" y="79" width="26" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-369 -79)"><path d="M25.4011 12.9974C25.4011 19.8478 19.8478 25.4011 12.9974 25.4011 6.14699 25.4011 0.593654 19.8478 0.593654 12.9974 0.593654 6.14699 6.14699 0.593654 12.9974 0.593654 19.8478 0.593654 25.4011 6.14699 25.4011 12.9974Z" stroke="#1E3D35" stroke-width="0.757136" stroke-miterlimit="10" fill="#FBFDF6" transform="matrix(1 0 0 1.03846 369 79)"/><path d="M16.7905 6.98727 11.8101 19.0075 11.6997 19.0075 9.20954 12.9974" stroke="#1E3D35" stroke-width="0.757136" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.03846 369 79)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Investeringskostnad", value= f"{0:,} kr".replace(',', ' '))
        with c2:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Reduserte utgifter til oppvarming", value= f"{savings1:,} kr/år".replace(',', ' '))
        with c3:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Samlet besparelse etter 20 år", value = f"{savings2:,} kr".replace(',', ' '))

    def operation_and_investment_after(self):

        st.write(f""" Mange banker har begynt å tilby billigere boliglån hvis boligen regnes som miljøvennlig; et såkalt grønt boliglån. 
        En oppgradering til bergvarme kan kvalifisere boligen din til et slikt lån. """)

        st.write(f""" Søylediagrammene viser årlige kostnader til oppvarming hvis investeringen finansieres 
        av et grønt lån. Her har vi forutsatt at investeringen nedbetales i 
        løpet av 20 år med effektiv rente på {round(self.interest,2)} %. Du kan endre betingelsene for lånet 
        i menyen til venstre.""")

    def investment_show(self):
        st.subheader("Investeringskostnad") 
        st.write(""" Investeringskostnaden omfatter en komplett installsjon av 
        bergvarme inkl. varmepumpe, montering og energibrønn. 
        Merk at dette er et estimat, og endelig pris må fastsettes av forhandler. """)
        st.metric(label="Investeringskostnad", value=(str(int(round(self.investment, -1))) + " kr"))

    def profitibality_operation_and_investment(self):
        if self.savings_sum < 0:
            st.warning("Bergvarme er ikke lønnsomt etter 20 år med valgte betingelser for lånefinansiering.", icon="⚠️")
            #st.stop()

    def profitibality_operation(self):
        if self.total_saving < 0:
            st.warning("Bergvarme er ikke lønnsomt etter 20 år med valgte forutsetninger for direkte kjøp.", icon="⚠️")
            st.stop()


class Environment:
    def __init__(self):
        self.co2_per_kwh = float 

    def adjust(self):
        options = ['Norsk energimiks', 'Norsk-europeisk energimiks', 'Europeisk energimiks ']
        selected = st.selectbox('Velg energimiks for produksjon av strøm', options, index=0)
        self.selected_option = selected 
        if selected == options[0]:
            self.co2_per_kwh = 16.2
        elif selected == options[1]:
            self.co2_per_kwh = 116.93
        elif selected == options[2]:
            self.co2_per_kwh = 123

        st.write(f"{round(self.co2_per_kwh, 1)} g CO\u2082-ekvivalenter/kWh")


    #i kilogram 
    def calculate_emissions(self, energy_arr, compressor_arr, peak_arr):
        co2_constant = self.co2_per_kwh/1000
        el_co2_hourly = energy_arr * co2_constant
        gshp_co2_hourly = (compressor_arr + peak_arr) * co2_constant

        self.el_co2_monthly = np.array(hour_to_month(el_co2_hourly))
        self.gshp_co2_monthly = np.array(hour_to_month(gshp_co2_hourly))

        self.el_co2_sum = np.sum(self.el_co2_monthly) * 20
        self.gshp_co2_sum = np.sum(self.gshp_co2_monthly) * 20
        self.savings_co2_sum = (self.el_co2_sum - self.gshp_co2_sum)

        self.gshp = int(round(np.sum(compressor_arr), -1))
        self.el = int(round(np.sum(energy_arr) + np.sum(peak_arr), -1))
        self.savings_power = int(round(self.el - self.gshp, -1))
    
    def plot(self):
        gshp = self.gshp
        el = self.el
        savings = self.savings_power

        #--1
        source = pd.DataFrame({"label" : [f'Strømforbruk: {gshp} kWh per år', f'Grønn energi'], 
        "value": [gshp, savings]})
        c1 = alt.Chart(source).mark_arc(innerRadius=35).encode(
            theta=alt.Theta(field="value", type="quantitative"),
            color=alt.Color(field="label", type="nominal", scale=alt.Scale(range=['#48a23f', '#a23f47']), 
            legend=alt.Legend(orient='top', direction='vertical', title=f'Bergvarme'))).configure_view(strokeWidth=0)
            
        #--2
        source = pd.DataFrame({"label" : [f'Strømforbruk: {el} kWh per år'], 
        "value": [el]})
        c2 = alt.Chart(source).mark_arc(innerRadius=35).encode(
            theta=alt.Theta(field="value", type="quantitative"),
            color=alt.Color(field="label", type="nominal", scale=alt.Scale(range=['#a23f47']), 
            legend=alt.Legend(orient='top', direction='vertical', title='Elektrisk oppvarming'))).configure_view(strokeWidth=0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(c1, use_container_width=True)
        with col2:
            st.altair_chart(c2, use_container_width=True) 
        
    def text_before(self):
        savings = round(self.savings_co2_sum/1000)
        flights = round(savings/(103/1000))

        st.write(f""" Vi har beregnet hvor mye strøm bergvarme vil spare i din bolig sammenlignet med å bruke elektrisk oppvarming.
        Figurene viser at du sparer {self.savings_power:,} kWh i året med bergvarme. 
        Hvis vi tar utgangspunkt i en {self.selected_option}
        vil du i løpet av 20 år spare {savings} tonn CO\u2082. 
        Dette tilsvarer **{flights} flyreiser** mellom Oslo - Trondheim. """.replace(',', ' '))

    def text_after(self):
        savings_co2 = round(self.savings_co2_sum/1000)

        savings = round(self.savings_co2_sum/1000)
        flights = round(savings/(103/1000))

        c1, c2 = st.columns(2)
        with c1:
            svg = """ <svg width="13" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="614" y="84" width="13" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-614 -84)"><path d="M614.386 99.81 624.228 84.3312C624.464 83.9607 625.036 84.2358 624.89 84.6456L621.224 95.1164C621.14 95.3522 621.32 95.5992 621.572 95.5992L626.3 95.5992C626.603 95.5992 626.777 95.9417 626.597 96.1831L616.458 109.691C616.194 110.039 615.644 109.725 615.823 109.326L619.725 100.456C619.838 100.203 619.63 99.9223 619.355 99.9447L614.74 100.36C614.437 100.388 614.229 100.057 614.392 99.7987Z" stroke="#1E3D35" stroke-width="0.308789" stroke-linecap="round" stroke-miterlimit="10" fill="#F0F3E3"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Strømbesparelse med bergvarme", value= f"{self.savings_power:,} kWh/år".replace(',', ' '))
        with c2:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="458" y="120" width="26" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-458 -120)"><path d="M480.21 137.875 480.21 135.438 472.356 129.885 472.356 124.604C472.356 123.548 471.814 122.167 471.001 122.167 470.216 122.167 469.647 123.548 469.647 124.604L469.647 129.885 461.793 135.438 461.793 137.875 469.647 133.948 469.647 139.852 466.939 142.208 466.939 143.833 471.001 142.208 475.064 143.833 475.064 142.208 472.356 139.852 472.356 133.948ZM472 140.261 474.522 142.455 474.522 143.033 471.203 141.706 471.001 141.624 470.8 141.706 467.481 143.033 467.481 142.455 470.003 140.261 470.189 140.099 470.189 133.072 469.403 133.463 462.335 136.999 462.335 135.718 469.96 130.328 470.189 130.166 470.189 124.604C470.189 123.645 470.703 122.708 471.001 122.708 471.341 122.708 471.814 123.664 471.814 124.604L471.814 130.166 472.043 130.328 479.668 135.718 479.668 136.999 472.598 133.463 471.814 133.072 471.814 140.099Z" stroke="#1D3C34" stroke-width="0.270833"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Utslippskutt med bergvarme etter 20 år", value= f"{flights:,} sparte flyreiser".replace(',', ' '))


class Gis:
    def __init__(self):
        pass

    @st.cache
    def bronnparker_api(self, lat, long):
        diff = 0.05
        x1 = long - diff
        x2 = lat - diff
        x3 = long + diff
        x4 = lat + diff

        antall = 100

        endpoint = f'https://ogcapitest.ngu.no/rest/services/granada/v1/collections/broennparkbroenn/items?f=json&limit={antall}&bbox={x1}%2C{x2}%2C{x3}%2C{x4}'
        r = requests.get(endpoint)
        bronnparker = r.json()
        
        return bronnparker

#    def depth_to_bedrock(self, bronnparker):
#        depth_to_bedrock_list = []
#        for i, value in enumerate(bronnparker["features"]):
#            depth_to_bedrock_list.append(value["properties"]["boret_lengde_til_berg"])
#
#        depth_to_bedrock_list = np.array(depth_to_bedrock_list)
#        return np.median(depth_to_bedrock_list)

    def mapping(self, adresse_lat, adresse_long, stasjon_lat, stasjon_long, station_id, average_temperature, adresse_navn, bronnparker):
        
        m = folium.Map(
            location=[adresse_lat, adresse_long], 
            zoom_start=12, 
            zoom_control=True, 
            dragging=True,
            scrollWheelZoom=False,
            tiles="OpenStreetMap", 
            no_touch=True, 
            )

        folium.Marker(
            [adresse_lat, adresse_long], 
            tooltip=f" {adresse_navn}",
            icon=folium.Icon(icon="glyphicon-home", color="red"),
        ).add_to(m)

        folium.Marker(
            [stasjon_lat, stasjon_long], 
            tooltip=f"Værstasjon {station_id}. Årsmiddeltemperatur: {average_temperature} °C.",
            icon=folium.Icon(icon="glyphicon-cloud", color="blue"),
        ).add_to(m)
        if bronnparker != 0:
            if len(bronnparker["features"]) > 0:
                folium.GeoJson(
                    bronnparker, 
                    name="Brønner i brønnpark", 
                    marker=folium.CircleMarker(
                        radius = 5,
                        weight = 0, #outline weight
                        fill_color = 'blue', 
                        fill_opacity = 1
                        ),
                    tooltip=folium.GeoJsonTooltip(
                        fields=["boret_lengde_til_berg"], 
                        aliases=['Dybde til fjell [m]:']
                        )
                ).add_to(m)

        st_folium(m, width = 500)

    def kart(self, stasjon_lat, adresse_lat, energibronn_lat, stasjon_long, adresse_long, energibronn_long, adresse_navn, average_temperature, station_id):
        #bronnparker = self.bronnparker_api(adresse_lat, adresse_long)
        bronnparker = 0
        self.mapping(adresse_lat, adresse_long, stasjon_lat, stasjon_long, station_id, average_temperature, adresse_navn, bronnparker)


class PDF(FPDF):
        def header(self):
            self.set_font('Times', 'B', 20)
            self.cell(0, 10, f'Resultater fra bergvarmekalkulatoren, {date.today().strftime("%d/%m/%Y")}', 0, 1, 'C')
            self.set_font('Times', '', 12)
            self.cell(0, 50, """Resultatene fra bergvarmekalkulatoren er estimater, \n
            og skal ikke brukes for endelig dimensjonering av energibrønn med varmepumpe. \n
            Endelig dimensjonering av energibrønn og varmepumpe skal utføres av  
            basert på reellt oppvarmingsbehov og stedlige geologiske forhold.""", 0, 1, 'C')
            self.ln(25)
        
        # Page footer
        def footer(self):
            # Position at 1.5 cm from bottom
            self.set_y(-15)
            # Arial italic 8
            self.set_font('Times', '', 10)
            # Page number
            self.cell(0, 10, 'Side ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

def download_report(average_temperature, weather_station_id, space_heating_sum, 
dhw_sum, kWh_per_meter, energy_gshp_delivered_sum, energy_gshp_compressor_sum, 
energy_gshp_peak_sum, cop, coverage, region, elprice_average):
    
    # Instantiation of inherited class
    pdf = PDF('P', 'mm', 'A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Times', '', 12)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    #Forutsetninger
    pdf.set_font('Times', 'B', 14)
    pdf.cell(0, 0, 'Forutsetninger', 0, 0, 'L')
    pdf.ln(5)
    pdf.set_font('Times', '', 12)
    lines = [
    f"1) Innhentet fra kart",
    f"- Årsmiddeltemperatur: {average_temperature} °C (år 1991 - 2020 fra værstasjon {weather_station_id})",
    f"- Strømregion: {region}",
    f"- Energi fra grunnen: {int(kWh_per_meter)} kWh per meter brønn "
    f"",
    f"2) Estimert energibehov",
    f"- Romoppvarming: {int(space_heating_sum)} kWh ",
    f"- Varmtvann: {int(dhw_sum)} kWh ",
    f"- Totalt energibehov: {int(space_heating_sum + dhw_sum)} kWh",
    f"3) Ditt bergvarmeanlegg",
    f"- Årsvarmefaktor (SCOP): {float((cop))}",
    f"- Energidekningsgrad for bergvarme: {int(coverage)} %",
    f"- Levert energi fra grunnen: {energy_gshp_delivered_sum} kWh",
    f"- Strømforbruk varmepumpe: {energy_gshp_compressor_sum} kWh",
    f"- Spisslast (dekkes ikke av bergvarme): {energy_gshp_peak_sum} kWh",
    f"- Totalkostnad for strøm: {float(elprice_average)} kr/kWh"
    ]
    for index, value in enumerate(lines):
        pdf.cell(0, 10, str(value), 0, 1)

    for index, value in enumerate(lines):
        pdf.cell(0, 10, str(value), 0, 1)



    st.download_button(
        "📈 Last ned resultater (PDF)",
        data=pdf.output(dest='S').encode('latin-1'),
        file_name="Resultater.pdf",
    )

        



