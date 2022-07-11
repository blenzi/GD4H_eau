import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import os
import requests
from shapely.geometry import Point



@st.cache
def read_pars():
    with open('data/par.json') as f:
        d = json.load(f)
    return pd.DataFrame(d['REFERENTIELS']['Referentiel']['Parametre'])

@st.cache
def read_info():
    return pd.read_csv('data/info_AtlaSante.csv')

def get_info_region(region):
    return read_info().query(f'Région == "{region}"')

@st.cache
def read_carte_region(region):
    return gpd.read_file(get_info_region(region)['Fichier'].values[0])


st.write("# Reseau et résultat de prélèvement pour une adresse")

regions = read_info()['Région'].to_list()
region = st.sidebar.selectbox('Région', regions, regions.index('Bretagne'))

annees = get_info_region(region)['Année'].to_list()
annee = st.sidebar.selectbox('Année', annees)

code_region = pd.read_json('https://geo.api.gouv.fr/regions').set_index('nom').loc[region, 'code']
if code_region >= 10:
    df_communes = pd.read_json(f'https://geo.api.gouv.fr/communes?codeRegion={code_region}')
else:
    df_communes = pd.read_json(f'https://geo.api.gouv.fr/communes?codeDepartement=97{code_region}')
if len(df_communes):
    commune = st.sidebar.selectbox('Commune', df_communes['nom'].sort_values().to_list())

parametres = read_pars()['NomParametre'].to_list()
parametre = st.sidebar.selectbox('Paramètre', parametres, parametres.index('Nitrates'))

st.write(f'Région sélectionnée: {region}')
st.write(f'Commune sélectionnée: {commune}')
st.write(f'Paramètre sélectionné: {parametre}')

code_commune = df_communes.query(f'nom == "{commune}" and codeRegion == {code_region}')['code'].values[0]
result = requests.get(f'https://hubeau.eaufrance.fr/api/vbeta/qualite_eau_potable/communes_udi?code_commune={code_commune}&annee={annee}')
st.write('Unités de distributions (UDIs):')
if result.status_code in (200, 206):
    st.write(pd.DataFrame(result.json()['data']))

code_parametre = read_pars().set_index('NomParametre').loc[parametre, 'CdParametre']
date_min = f'{annee}-01-01 00:00:00'
date_max = f'{annee+1}-01-01 00:00:00'
result = requests.get(f'https://hubeau.eaufrance.fr/api/vbeta/qualite_eau_potable/resultats_dis?code_commune={code_commune}&code_parametre={code_parametre}&date_min_prelevement={date_min}&date_max_prelevement={date_max}&fields=libelle_parametre,code_lieu_analyse,resultat_numerique,libelle_unite,date_prelevement')
if result.status_code in (200, 206):
    st.write('Prelevements:')
    data = pd.DataFrame(result.json()['data'])
    st.write(data)
    st.caption(f'{len(data)} prelevements en {annee}')


# 'date_min_prelevement'



address = st.sidebar.text_input('Adresse')
proxies = {}
geoapi_key = os.getenv('GEOAPI_KEY') or open('.geoapi_key').read()  #[:-1]

def search_address(address):
    result = requests.get(f'https://api.geoapify.com/v1/geocode/search?text="{address}"&apiKey={geoapi_key}', proxies=proxies)
    if result.status_code == 200:
        d = result.json()
        try:
            return d['features'][0]  # first adress to appear
        except (ValueError, IndexError):
            raise  # TODO: exception, adress not found

def get_code_reseau(df, point, field='c_ins_code'):
    return df.loc[df.contains(point), field].values[0]

def get_info_reseau(code_reseau, annee=2021):
    result = requests.get(f'https://hubeau.eaufrance.fr/api/vbeta/qualite_eau_potable/communes_udi?code_reseau={code_reseau}&annee={annee}')
    if result.status_code == 200:
        return result.json()

def get_dernier_prelevement(code_reseau, annee=2021):
    result = requests.get(f'https://hubeau.eaufrance.fr/api/vbeta/qualite_eau_potable/resultats_dis?code_reseau={code_reseau}&annee={annee}&code_parametre=1340&size=1&fields=libelle_parametre,code_lieu_analyse,resultat_numerique,libelle_unite,date_prelevement&sort=desc')
    if result.status_code in (200, 206):
        return result.json()['data'][0]

if address:
    try:
        add = search_address(address)
    except Exception(e):
        st.write(f'Adresse non trouvée: {address}')
        st.write(e)
    else:
        p = Point(*add['geometry']['coordinates'])
        code_reseau = get_code_reseau(read_carte_region(region=region), p, field=get_info_region(region)['Champ AtlaSante'].values[0])
        info_reseau = get_info_reseau(code_reseau)
        data = get_dernier_prelevement(code_reseau)

        # st.write(f"Adresse: {add['properties']['street']}, {add['properties']['city']}, {add['properties']['state']}, {add['properties']['country']}")
        # st.write(f"Adresse: {add['properties']['street']}, {add['properties']['city']}, {add['properties']['country']}")
        st.write(f"Adresse: {add['properties']}, {add['properties']['city']}, {add['properties']['country']}")
        p = Point(*add['geometry']['coordinates'])
        st.write(f"Coordonnées: lat {p.x}, lon {p.y}")

        st.write(f"Code de l'unité de distribution: {code_reseau}")
        s = (f"{item['nom_commune']} ({item['nom_quartier']})" for item in info_reseau['data'])
        st.write(f"Communes desservies: {', '.join(s)}")

        st.write(f"Date du dernier prélèvement: {pd.Timestamp(data['date_prelevement'])}")
        st.write(f"Concentration en {data['libelle_parametre']}: {data['resultat_numerique']} {data['libelle_unite']}")

    #ax = df.plot('c_ins_code', cmap="Blues", figsize=(12,8))
    # ax = df.plot(color='lightblue', figsize=(12,8), missing_kwds={'color': 'lightgrey'}, edgecolor='black')
    # ax.set_xlabel('Latitude')
    # ax.set_ylabel('Longitude')
    # ax.set_title('Unités de distribution en Bretagne')
    # _ = ax.scatter([p.x], [p.y], color='red')
