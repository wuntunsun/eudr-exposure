import streamlit as st
from streamlit_app import sidebar

import random
print(f'Risk {random.randint(0,99)}')

st.sidebar.header('Risk')
#st.header('Risk')

sidebar()