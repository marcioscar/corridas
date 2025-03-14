import pandas as pd
import streamlit as st
import plotly.express as px
import polyline
import folium
from streamlit_folium import st_folium
from polyline import decode
from datetime import date, datetime

import streamlit_shadcn_ui as ui




st.set_page_config(layout="wide")
st.logo(
    'LOGO.png',size="large"
)


df = pd.read_csv("data/atvidades_12_03_2025.csv", parse_dates=['start_date_local'])

#fill Nan with empty
df['map.summary_polyline'] = df['map.summary_polyline'].fillna('')
# remove non string values
df = df[df['map.summary_polyline'].apply(lambda x: isinstance(x, str))]


# df.columns
df['moving_time_minutes'] = round(df['moving_time']/60, 2)
df['moving_time_minutes'].head()
df['distance_km'] = round(df['distance'] / 1000, 2)
df['pace'] = df['moving_time_minutes'] / df['distance_km']
df['Tempo'] = df['moving_time_minutes'].apply(
    lambda x: f"{int(x // 60)}h {int(x % 60)}m"
)

df['avg_speed_kmh'] = round(60/df['pace'], 2)

def kmh_to_min_km(speed_kmh):
    if speed_kmh > 0:  # Evitar divisão por zero
        pace = 60 / speed_kmh
        minutes = int(pace)
        seconds = int((pace - minutes) * 60)
        return f"{minutes}:{seconds:02d} min/km"
    else:
        return None  # Retorna None para velocidades inválidas

df['avg_speed_kmh'] = pd.to_numeric(df['avg_speed_kmh'], errors='coerce')
df['pace_real'] = df['avg_speed_kmh'].apply(kmh_to_min_km)
# add decoded summary polylines

# Corrected line with safe decode
def decode_polyline_safe(polyline_str):
    if isinstance(polyline_str, str):
        return polyline.decode(polyline_str)
    else:
        return []  # or None or some other default for non-string values


df['map.polyline'] = df['map.summary_polyline'].apply(polyline.decode)


cols = ['start_date_local','name', 'type','distance_km', 'pace_real', 'moving_time_minutes', 'avg_speed_kmh',  
        'total_elevation_gain',
           'map.polyline', 'Tempo'
       ]

corridas = df[cols]

runs = corridas.loc[corridas['type'] == 'Run'] 

# Make 'start_date_local' timezone-naive
runs['start_date_local'] = runs['start_date_local'].dt.tz_localize(None)


# Data inicial e final padrão

# Get the first day of the current month
today = date.today()
start_date = date(today.year, today.month, 1)
# Get today as end_date
end_date = date.today()

datas_selecionadas = st.sidebar.date_input(
    "Selecione o período:",
    (start_date, end_date),
    format="DD/MM/YYYY"
   
)
todas = st.sidebar.toggle("Todas as corridas")

distancias = [
    ("Todas", 0),
    ("Até 10km", 10),
    ("de 11-20km", 20),
    ("de 21-30km", 30),
    ("Meia", 211),
    (">31km", 31),
    ("Maratona", 42),

    
]

distancia = st.sidebar.select_slider(
    "Selecione a distância:",
    options=[label for label, value in distancias],

)
distancia_valor = next(value for label, value in distancias if label == distancia)



# Convert selected date to datetime objects for comparison
if len(datas_selecionadas) == 2:
    selected_start_datetime = datetime.combine(datas_selecionadas[0], datetime.min.time())
    selected_end_datetime = datetime.combine(datas_selecionadas[1], datetime.max.time())
    runs_filtered = runs[(runs['start_date_local'] >= selected_start_datetime) &
                         (runs['start_date_local'] <= selected_end_datetime)]
    if todas:
         runs_filtered = runs   

    # Format 'start_date_local' to Brazilian format and rename
    runs_filtered.loc[:, 'Data'] = runs_filtered['start_date_local'].dt.strftime('%d/%m/%Y %H:%M:%S')
    # Remove the old column
    runs_filtered = runs_filtered.drop('start_date_local', axis=1)
    # Reorder columns with 'Data' as the first one
    cols = ['Data'] + [col for col in runs_filtered.columns if col != 'Data']
    runs_filtered = runs_filtered[cols]
    
    # runs_filtered
    
    
    if distancia_valor == 0:
        runs_filtered = runs_filtered
        # runs_filtered

    if distancia_valor == 10:
        runs_filtered = runs_filtered[runs_filtered['distance_km'].between( 0 ,float(distancia_valor + 0.99)) ]     
        # runs_filtered 

    if distancia_valor == 20:
        runs_filtered = runs_filtered[runs_filtered['distance_km'].between( 11 ,float(distancia_valor + 0.99)) ]     
        # runs_filtered

    if distancia_valor == 30:
        runs_filtered = runs_filtered[runs_filtered['distance_km'].between( 21 ,float(distancia_valor + 0.99)) ]     
        # runs_filtered    

    if distancia_valor == 31:
        runs_filtered = runs_filtered[runs_filtered['distance_km'].between( 31 ,float(distancia_valor + 100)) ]     
        # runs_filtered      

    if distancia_valor == 211:
        runs_filtered = runs_filtered[runs_filtered['distance_km'].between( 21 , 22) ]     
        # runs_filtered    

    if distancia_valor == 42:
        runs_filtered = runs_filtered[runs_filtered['distance_km'].between( 41 , 45) ]     
        # runs_filtered        
runs_filtered = runs_filtered[['Data', 'name', 'distance_km','Tempo', 'pace_real', 'total_elevation_gain', 'map.polyline' ]].rename(columns={
    'name': 'Descrição',
    'distance_km': 'Distância',
    'pace_real': 'Pace',
    'total_elevation_gain':'Ganho Elev.'
})





# *** FORMATTING THE SUM ***
total = runs_filtered['Distância'].sum()
total_formatted = "{:,.2f}".format(total).replace(",", "X").replace(".", ",").replace("X", ".")

# *** END FORMATTING ***

# *** PACE MEAN ***
def pace_to_minutes(pace_str):
    if pace_str is None:
        return None
    minutes, seconds_km = map(int, pace_str.split(" min/km")[0].split(":"))
    total_minutes = minutes + seconds_km / 60
    return total_minutes
runs_filtered['pace_minutes'] = runs_filtered['Pace'].apply(pace_to_minutes)
pace_medio = runs_filtered['pace_minutes'].mean()

#format the result
def format_pace(pace_minutes):
    if pd.isna(pace_minutes):
        return "0:00 min/km"
    minutes = int(pace_minutes)
    seconds = int((pace_minutes - minutes) * 60)
    return f"{minutes}:{seconds:02d} min/km"

pace_medio_formatted = format_pace(pace_medio)
# *** END PACE MEAN ***



cols = st.columns(2)
with cols[0]:
    ui.metric_card(title="Total de Km corridos", content=total_formatted, description=f"De {datas_selecionadas[0].strftime('%d/%m/%Y')} - {datas_selecionadas[1].strftime('%d/%m/%Y')}", key="card1")
with cols[1]:
    ui.metric_card(title="Pace Medio", content=pace_medio_formatted, description="+20.1% from last month", key="card2")


df_visivel = runs_filtered.drop(columns=['map.polyline', 'pace_minutes' ])


event = st.dataframe(
    df_visivel,
    key="data",
    on_select="rerun",
    selection_mode=["single-row"],
)

if event.selection.rows:
    linha_selecionada = event.selection.rows[0]
else:
    linha_selecionada = 0


# # define function to get elevation data using the open-elevation API
# def get_elevation(latitude, longitude):
#     base_url = 'https://api.open-elevation.com/api/v1/lookup'
#     payload = {'locations': f'{latitude},{longitude}'}
#     r = requests.get(base_url, params=payload).json()['results'][0]
#     return r['elevation']
# # get elevation data
# elevation_data = list()

# elevation = [get_elevation(coord[0], coord[1]) for coord in runs_filtered['map.polyline'].iloc[linha_selecionada]]
# elevation_data.append(elevation)    
# elevation_data


# runs_filtered

# corridas_filtradas = runs['start_date_local'] >= datas_selecionadas[0] & runs['start_date_local'] <= datas_selecionadas[1]
if not runs_filtered.empty: 
    rota = runs_filtered['map.polyline'].iloc[linha_selecionada]

    m = folium.Map(location=rota[0], zoom_start=13)
    

    # Adiciona a polyline (rota) ao mapa
    folium.PolyLine(rota, color='blue', weight=5, opacity=0.7).add_to(m)

    # Adiciona marcador verde na primeira posição
    folium.Marker(location=rota[0], tooltip="Inicio", icon=folium.Icon(color='green', icon='play')).add_to(m)

    # Adiciona marcador vermelho na última posição
    folium.Marker(location=rota[-1], tooltip="Final",icon=folium.Icon(color='red', icon='flag')).add_to(m)

    # Exibe o mapa no Streamlit
    st_folium(m, center=True, width="100%", height=400)






# https://towardsdatascience.com/visualize-your-strava-data-on-an-interactive-map-with-python-92c1ce69e91d/
# https://medium.com/towards-data-science/analysing-strava-data-with-python-b8a5badb019f







