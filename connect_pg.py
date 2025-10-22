import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta, date
import time
import pytz
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re
from dotenv import load_dotenv
import logging
import io

from streamlit.web import cli as stcli
import sys

# Define BASE_DIR for consistent file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_DIR = os.environ.get('FILES_DIR', os.path.join(BASE_DIR, 'Files'))
BULK_DIR = os.environ.get('BULK_DIR', os.path.join(BASE_DIR, 'Bulk_Import'))
REPORTS_DIR = os.environ.get('REPORTS_DIR', os.path.join(BASE_DIR, 'reports'))
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(BULK_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

load_dotenv()  # Load environment variables from .env file

def get_connection():
    """Load DB credentials from environment variables and connect to PostgreSQL."""
    host = os.environ.get('DB_HOST')
    port = os.environ.get('DB_PORT', '6543')
    dbname = os.environ.get('DB_NAME')
    user = os.environ.get('DBP_USER')
    password = os.environ.get('DBP_PASSWORD')
    print("host=", host)
    if not all([host, dbname, user, password]):
        st.error("Missing DB environment variables: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        return None
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode='require'  # For Supabase/SSL-enabled PG
        )
        st.success("Connected to PostgreSQL Database!")
        return connection
    except Exception as e:
        st.write(f"DB Connection Error: {e}")
        return None

get_connection()
