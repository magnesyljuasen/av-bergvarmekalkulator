import streamlit as st
from st_keyup import st_keyup
import requests
import time 

class Adjust:
    def __init__(self, elprice, spaceheating, dhw, depth_to_bedrock, groundwater_table, thermal_conductivity):
        self.elprice = elprice
        self.spaceheating = spaceheating
        self.dhw = dhw
        self.energycoverage = 95
        self.depth_to_bedrock = depth_to_bedrock
        self.groundwater_table = groundwater_table
        self.thermal_conductivity = thermal_conductivity
        self.borehole_resistance = 0.10

    def adjust_input(self):
        with st.form('input'):
            with st.expander("⚡ Energi og effekt"):
                c1, c2 = st.columns(2)
                with c1:
                    self.spaceheating_f()
                    self.dhw_f()
                with c2:
                    self.heatsystem_f()
                    self.energycoverage_f() 
            with st.expander("🌱 Kostnad- og miljøanalyse"):
                c1, c2 = st.columns(2)
                with c1:
                    self.elprice_f()
                with c2:
                    self.energymix_f()
            with st.expander("⛰️ Grunnforhold"):
                c1, c2 = st.columns(2)
                with c1:
                    self.groundwater_table_f()
                    self.depth_to_bedrock_f()
                with c2:
                    self.thermal_conductivity_f()
                    self.borehole_resistance_f()              
            if st.form_submit_button('🖩 Start beregning'):
                self.start = True
            else:
                self.start = False
    
    def heatsystem_f(self):
        option_list = ['Gulvvarme', 'Gulvvarme | Radiator', 'Radiator']
        selected = st.selectbox('Velg type varmesystem', options=option_list)
        x = {option_list[0] : 4, option_list[1] : 3, option_list[2] : 2}
        self.cop = x[selected]

    def elprice_f(self):
        self.elprice = st.number_input('Velg strømpris [kr/kWh]', min_value=0.5, value=self.elprice, max_value=10.0, step=0.1)

    def energymix_f(self):
        option_list = ['Norsk', 'Norsk-europeisk', 'Europeisk']
        selected = st.selectbox('Velg type energimiks for strømproduksjon', options=option_list)
        x = {option_list[0] : 16.2, option_list[1] : 116.9, option_list[2] : 123}
        self.energymix = x[selected]

    def energycoverage_f(self):
        self.energycoverage = st.number_input('Velg energidekningsgrad [%]', min_value=80, value=95, max_value=100)

    def spaceheating_f(self):
        self.spaceheating = st.number_input('Juster romoppvarmingsbehov [kWh]', min_value=0, value=self.spaceheating, max_value=100000, step=1000)

    def dhw_f(self):
        self.dhw = st.number_input('Juster tappevannsbehov [kWh]', min_value=0, value=self.dhw, max_value=100000, step=1000)

    def depth_to_bedrock_f(self):
        self.depth_to_bedrock = st.number_input('Dybde til fjell [m]', min_value=0, value=self.depth_to_bedrock, max_value=100, 
        help=''' Dybde til fjell påvirker kostnaden for å 
        bore energibrønn, og kan variere mye fra sted til sted. 
        Brønnborer bør sjekke dette opp mot NGU sine databaser for 
        grunnvannsbrønner og grunnundersøkelser.''')

    def groundwater_table_f(self):
        self.groundwater_table = st.number_input('Dybde til grunnvannspeil [m]', min_value=0, value=self.groundwater_table, max_value=100)

    def thermal_conductivity_f(self):
        self.thermal_conductivity = st.number_input('Effektiv varmeledningsevne [W/m*K]', min_value=2.0, value=self.thermal_conductivity, max_value=10.0, step=0.1)
    
    def borehole_resistance_f(self):
        self.borehole_resistance = st.number_input('Borehullsmotstand [m*K/W]', min_value=0.01, value=self.borehole_resistance, max_value=0.15)







    
