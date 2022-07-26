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


st.write("# Reseau et résultat des prélèvements par région ou commune")

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
    communes = st.sidebar.multiselect('Communes', df_communes['nom'].sort_values().to_list())

code_communes = df_communes.loc[df_communes['nom'].isin(communes), 'code'].to_list()
code_communes = ",".join(f'{i:05}' for i in code_communes)  # need to prefix zeros

if communes:
    result = requests.get(f'https://hubeau.eaufrance.fr/api/vbeta/qualite_eau_potable/communes_udi?code_commune={code_communes}&annee={annee}')
    st.write('Unités de distributions (UDIs):')
    if result.status_code in (200, 206):
        st.write(pd.DataFrame(result.json()['data']))

parametres = st.sidebar.multiselect('Paramètres', read_pars()['NomParametre'].to_list())

if communes and parametres:
    code_parametres = ",".join(read_pars().loc[read_pars()['NomParametre'].isin(parametres), 'CdParametre'].astype(str).to_list())
    date_min = f'{annee}-01-01 00:00:00'
    date_max = f'{annee+1}-01-01 00:00:00'
    fields = ['date_prelevement', 'libelle_parametre', 'code_reseau', 'resultat_numerique', 'libelle_unite']
    result = requests.get(f'https://hubeau.eaufrance.fr/api/vbeta/qualite_eau_potable/resultats_dis?code_commune={code_communes}&code_parametre={code_parametres}&date_min_prelevement={date_min}&date_max_prelevement={date_max}&fields={",".join(fields)}')  # noqa: E501
    if result.status_code in (200, 206):
        st.write('Prelevements:')
        data = pd.DataFrame(result.json()['data'])
        if len(data):
            data = data.sort_values('date_prelevement').reset_index()[fields]
            st.write(data)
            st.download_button(
                label="Download as CSV",
                data=data.to_csv(index=False),
                file_name='data.csv',
                mime='text/csv',
            )
        st.caption(f'{len(data)} mesures en {annee}')
