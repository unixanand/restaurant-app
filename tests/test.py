import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta, date
import time
import pytz
import oracledb
import os
import re
from dotenv import load_dotenv
import logging

def get_connection():
    """Load DB credentials from environment variables and connect to Oracle."""
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    dsn = os.environ.get('DB_DSN')
    if not all([user, password, dsn]):
        st.error("Missing DB environment variables: DB_USER, DB_PASSWORD, DB_DSN")
        return None
    try:
        connection = oracledb.connect(user=user, password=password, dsn=dsn)
        st.success("Connected to Oracle Database!")
        return connection
    except Exception as e:
        st.error(f"DB Connection Error: {e}")
        return None

get_connection()
