import streamlit as st
from utilities import learn_more, sidebar_menu, services, about_us
from calculator import main_calculation

# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'

st.set_page_config(
    page_title="Bergvarmekalkulatoren",
    page_icon="src/bilder/icons8-dry-32.png",
    layout="centered",
    initial_sidebar_state="collapsed")
    #initial_sidebar_state=st.session_state.sidebar_state)

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)


main_calculation()
