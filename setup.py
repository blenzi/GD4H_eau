from setuptools import setup, find_packages
from setuptools.command.install import install
import os
from pathlib import Path


with open('README.md') as f:
    readme = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


class PostInstall(install):
    """
    Post-installation: download and unpack package data if needed:
    files from s3 if available, DIS files from data.gouv and json files from Osmose
    """
    def finalize_options(self):
        install.finalize_options(self)
        import dload
        import pandas as pd

        os.system('mc Ap -r s3/blenzi/GD4H_eau/data .')

        url_DIS = {
            2021: "https://www.data.gouv.fr/fr/datasets/r/d2b432cc-3761-44d3-8e66-48bc15300bb5",
            2020: "https://www.data.gouv.fr/fr/datasets/r/a6cb4fea-ef8c-47a5-acb3-14e49ccad801",
            2019: "https://www.data.gouv.fr/fr/datasets/r/861f2a7d-024c-4bf0-968b-9e3069d9de07",
            2018: "https://www.data.gouv.fr/fr/datasets/r/0513b3c0-dc18-468d-a969-b3508f079792",
            2017: "https://www.data.gouv.fr/fr/datasets/r/5785427b-3167-49fa-a581-aef835f0fb04",
            2016: "https://www.data.gouv.fr/fr/datasets/r/483c84dd-7912-483b-b96f-4fa5e1d8651f"
        }

        for year, url in url_DIS.items():
            output_dir = Path(f'data/DIS_{year}')
            if not output_dir.exists():
                output_dir.mkdir(parents=True)
                dload.save_unzip(url, extract_path=str(output_dir), delete_after=True)

        data_AtlaSante = pd.read_csv('data/info_AtlaSante.csv')
        if not data_AtlaSante['Fichier'].apply(lambda x: Path(x).exists()).all():
            # data_AtlaSante['Fichier'].apply(lambda x: Path(x).parent.mkdir(exist_ok=True))
            url_AtlaSante = "https://osmose.numerique.gouv.fr/front/publicLink/publicDownload.jsp?id=a8e0ff0b-2fc0-40de-868d-a1458151ab825e139cbc-81ec-492f-8716-c0d415c8f7db"  # noqa: E501
            dload.save_unzip(url_AtlaSante, extract_path='data/', delete_after=True)


setup(
    name="GD4H_eau",
    version='0.0.3',
    author="Bruno Lenzi",
    author_email="bruno.lenzi@developpement-durable.gouv.fr",
    description="GD4H: cas d’usage qualité de l'eau du robinet",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/blenzi/GD4H_eau",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=requirements,
    include_package_data=True,
    cmdclass={'install': PostInstall}
)
