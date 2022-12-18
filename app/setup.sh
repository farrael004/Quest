#!/bin/bash

python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
streamlit run streamlit_app.py