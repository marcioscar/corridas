from dotenv import load_dotenv
import pandas as pd
from pymongo import MongoClient
import streamlit as st
import pymongo
from datetime import datetime
import os

filtro = {
    "data": {"$gte": datetime(2025, 1, 1)}  # Data maior ou igual a 1 de janeiro de 2025
}

filtro_despesas = {
    "data": {"$gte": datetime(2025, 1, 1)},  # Data maior ou igual a 1 de janeiro de 2025
    "$or": [
        {"pago": True},   # Registros onde pago é True
        {"pago": {"$exists": False}}  # Registros onde pago não existe
    ]
}
@st.cache_resource
def conexao():
    try:
        load_dotenv()
        uri = os.getenv("DATABASE_URL")
        client = MongoClient(uri, server_api=pymongo.server_api.ServerApi(
        version="1", strict=True, deprecation_errors=True))
    except Exception as e:
        raise Exception(
            "Erro: ", e)
    db = client["corridas"]
    st.session_state.db = db
    return db
