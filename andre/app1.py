import streamlit as st
from streamlit_searchbox import st_searchbox
import requests
from src.scripts import _pygfunction, _utils, adjust, costs, demand, electricity, environment, geoenergy, geology, input, temperature, utils

with open("src/styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
    
def address_search(adr):
    options_list = []
    lat_list = []
    long_list = []
    postnummer_list = []
    antall = 5
    r = requests.get(f"https://ws.geonorge.no/adresser/v1/sok?sok={adr}&fuzzy=true&treffPerSide={antall}&sokemodus=OR", auth=('user', 'pass'))
    if r.status_code == 200 and len(r.json()["adresser"]) == antall:   
        for i in range(0, antall):
            json = r.json()["adresser"][i]
            adresse_tekst = json["adressetekst"]
            poststed = (json["poststed"]).capitalize()
            postnummer = json["postnummer"]
            postnummer_list.append(postnummer)
            opt = f"{adresse_tekst}, {poststed}"
            options_list.append(opt)
            lat_list.append(json["representasjonspunkt"]["lat"])
            long_list.append(json["representasjonspunkt"]["lon"])
    return options_list
    #return options_list, lat_list, long_list, postnummer_list

st.title("Bergvarmekalkulatoren")
selected_value = st_searchbox(
    address_search,
    key="wiki_searchbox",
    placeholder="Søk...",
    label="📍 Skriv inn adresse"
)
area = st.text_input('🏠 Tast inn oppvarmet boligareal [m²]')
minimum_area, maximum_area = 100, 500
if area == 'None' or area == '':
    area = ''
    st.stop()
elif area.isdecimal() and int(area) >= minimum_area and int(area) <= maximum_area:
    area = int(area)
else:
    st.error(f'🚨 Oppvarmet boligareal må være mellom {minimum_area} og {maximum_area} m²')
    st.stop()

option_list = ['Gulvvarme', 'Radiator', 'Kun varmtvann']
selected = st.selectbox('Velg type varmesystem', options=option_list)
x = {option_list[0] : 4, option_list[1] : 3, option_list[2] : 2}
COP = x[selected]

c1, c2 = st.columns(2)
thermal_sum = int(area * 500)
heat_demand = st.slider("Hva er boligens årlige varmebehov? [kWh/år]", value = thermal_sum, help="Her har vi har estimert varmebehov ut ifra størrelsen på ditt hus. Boligens varmebehov utgjør ca. 50-60% av det årlige strømforbruket.")

st.title('Counter Example')
if 'count' not in st.session_state:
    st.session_state.count = 0

increment = st.button('Increment')
if increment:
    st.session_state.count += 1

st.write('Count = ', st.session_state.count)

