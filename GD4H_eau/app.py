import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import os
import s3fs
import requests
from shapely.geometry import Point
import folium
from streamlit_folium import folium_static


proxies = {}
geoapi_key = os.getenv('GEOAPI_KEY') or open('.geoapi_key').read()[:-1]


def open_file(filename, mode='r'):
    """
    Return a file object, open with open(data/<filename>, <mode>) or fs.open(projet-connaissance-enr/filename, <mode>)
    for s3, depending if environment variable $AWS_S3_ENDPOINT is set
    Args:
        filename (str): file to open
        mode (str): open mode
    Returns:
        File object
    """
    if 'AWS_S3_ENDPOINT' in os.environ:
        # Create filesystem object
        S3_ENDPOINT_URL = "https://" + os.environ["AWS_S3_ENDPOINT"]
        fs = s3fs.S3FileSystem(client_kwargs={'endpoint_url': S3_ENDPOINT_URL})
        return fs.open(f'blenzi/GD4H_eau/{filename}', mode=mode)
    else:
        return open(filename, mode=mode)


@st.cache
def read_pars():
    with open_file('data/par.json') as f:
        d = json.load(f)
    return pd.DataFrame(d['REFERENTIELS']['Referentiel']['Parametre'])


@st.cache
def read_info():
    with open_file('data/info_AtlaSante.csv') as f:
        return pd.read_csv(f)


def get_info_region(region):
    return read_info().query(f'Région == "{region}"')


@st.cache
def read_carte_region(region):
    with open_file(get_info_region(region)['Fichier'].values[0]) as f:
        return gpd.read_file(f)


def get_code_reseau(df, point, field='c_ins_code'):
    return df.loc[df.contains(point), field].values[0]


st.write("# Reseau et résultat des prélèvements par adresse ou commune")

regions = read_info()['Région'].to_list()
region = st.sidebar.selectbox('Région', regions, regions.index('Bretagne'))
field = read_info().set_index('Région').loc[region, 'Champ AtlaSante']  # champ code réseau sur la carte AtlaSanté

annees = get_info_region(region)['Année'].to_list()
annee = st.sidebar.selectbox('Année', annees)

code_region = pd.read_json('https://geo.api.gouv.fr/regions').set_index('nom').loc[region, 'code']
if code_region >= 10:
    df_communes = pd.read_json(f'https://geo.api.gouv.fr/communes?codeRegion={code_region}')
else:
    df_communes = pd.read_json(f'https://geo.api.gouv.fr/communes?codeDepartement=97{code_region}')
if not len(df_communes):
    adresse_ou_commune = 'adresse'
else:
    adresse_ou_commune = st.sidebar.radio('Rechercher par:', ['adresse', 'commune(s)'])

point = None
selection = None

if adresse_ou_commune == 'adresse':
    adresse = st.sidebar.text_input('Adresse')
    if adresse:
        result = requests.get(f'https://api.geoapify.com/v1/geocode/search?name="{adresse}"&apiKey={geoapi_key}&country=France&state={region}', proxies=proxies)  # noqa: E501
        if result.status_code != 200:
            st.sidebar.write('Adresse non-trouvée')
            adresse = None
        else:
            options = [item['properties']['formatted'] for item in result.json()['features']]
            adresse = st.selectbox('Adresse choisie', options)
            index = options.index(adresse)
            point = Point(result.json()['features'][index]['geometry']['coordinates'])
            carte_region = read_carte_region(region)
            try:
                code_reseau = get_code_reseau(carte_region, point, field)
                selection = f'code_reseau={code_reseau}'
            except IndexError:
                pass

else:
    communes = st.sidebar.multiselect('Communes', df_communes['nom'].sort_values().to_list())
    code_communes = df_communes.loc[df_communes['nom'].isin(communes), 'code'].to_list()
    try:
        code_communes = ",".join(f'{i:05}' for i in code_communes)  # need to prefix zeros
    except ValueError:  # pour la Corse les codes sont du type 2A001, pas besoin de rajouter des zeros
        code_communes = ",".join(code_communes)
    if code_communes:
        selection = f'code_commune={code_communes}'

if selection:
    result = requests.get(f'https://hubeau.eaufrance.fr/api/vbeta/qualite_eau_potable/communes_udi?{selection}&annee={annee}')  # noqa: E501
    st.write('Unités de distributions (UDIs):')
    if result.status_code in (200, 206):
        df_reseau = pd.DataFrame(result.json()['data'])
        st.write(df_reseau)
        st.download_button(
                label="Download as CSV",
                data=df_reseau.to_csv(index=False),
                file_name='reseau.csv',
                mime='text/csv',
            )
        if len(df_reseau) and st.checkbox('Afficher la carte des UDIs'):
            carte_region = read_carte_region(region)
            carte_UDIs = carte_region.merge(df_reseau, left_on=field, right_on='code_reseau')
            if not len(carte_UDIs):
                st.caption('Contour des UDIs non disponible')
            if len(carte_UDIs) or point:
                if point:
                    location = [point.y, point.x]
                else:
                    location = [carte_UDIs.geometry.centroid.y.mean(), carte_UDIs.geometry.centroid.x.mean()]

                mapa = folium.Map(
                    min_zoom=2,
                    max_zoom=18,
                    location=location,
                    zoom_start=8,
                )
                if len(carte_UDIs):
                    tooltip = folium.GeoJsonTooltip(['nom_reseau'])
                    gjson = folium.GeoJson(carte_UDIs, name='UDIs', tooltip=tooltip)
                    gjson.add_to(mapa)

                if point:
                    folium.Marker(name=adresse, location=[point.y, point.x], tooltip=adresse).add_to(mapa)

                folium.LayerControl().add_to(mapa)
                folium_static(mapa)

# Parameters section
parametres = st.sidebar.multiselect('Paramètres', read_pars()['NomParametre'].to_list())

if selection and parametres:
    code_parametres = ",".join(read_pars().loc[read_pars()['NomParametre'].isin(parametres), 'CdParametre']
                                          .astype(str).to_list())
    date_min = f'{annee}-01-01 00:00:00'
    date_max = f'{annee+1}-01-01 00:00:00'
    fields = ['date_prelevement', 'libelle_parametre', 'code_reseau', 'resultat_numerique', 'libelle_unite']
    result = requests.get(f'https://hubeau.eaufrance.fr/api/vbeta/qualite_eau_potable/resultats_dis?{selection}&code_parametre={code_parametres}&date_min_prelevement={date_min}&date_max_prelevement={date_max}&fields={",".join(fields)}')  # noqa: E501
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
