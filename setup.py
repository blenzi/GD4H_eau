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

        
        data_AtlaSante = pd.read_csv('data/info_AtlaSante.csv')
        if not data_AtlaSante['Fichier'].apply(lambda x: Path(x).exists()).all():
            data_AtlaSante['Fichier'].apply(lambda x: Path(x).parent.mkdir(exist_ok=True))
            url_AtlaSante = "https://osmose.numerique.gouv.fr/front/publicLink/publicDownload.jsp?id=a8e0ff0b-2fc0-40de-868d-a1458151ab825e139cbc-81ec-492f-8716-c0d415c8f7db"  # noqa: E501
            dload.save_unzip(url_AtlaSante, extract_path='data/', delete_after=True)


setup(
    name="GD4H_eau",
    version='0.0.4',
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
