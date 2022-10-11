__doc__ = "Download DIS data from data.gouv.fr"

import os
import dload
from pathlib import Path


os.system('mc cp -r s3/blenzi/GD4H_eau/data .')

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
        print(f'Downloading data for {year}')
        output_dir.mkdir(parents=True)
        dload.save_unzip(url, extract_path=str(output_dir), delete_after=True)
