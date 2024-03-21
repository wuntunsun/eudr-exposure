# Decent Exposure: Deforestation and Physical Assets

The task we set ourselves, in collaboration with [Climate & Company](https://climateandcompany.org), was to take observation data related to deforestation and combine it meaningfully with physical asset data to support Geospatial ESG. In addition, we wanted to apply what we had learned during the three-month Data Science Bootcamp at [SPICED](https://www.spiced-academy.com).

See the results in our [final presentation](docs/decent_exposure_deforestation_and_physical_assets.pdf).

## Technology Stack

Pandas, NumPy, GeoPandas, Rasterio, rioxarray, Cartopy, scikit-learn, XGBoost and Streamlit.

## Set up your Environment

The added [requirements file](requirements.txt) contains all libraries and dependencies.

### **`macOS`** type the following commands : 

- Install the virtual environment and the required packages by following commands:

    ```BASH
    pyenv local 3.11.3
    python -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
### **`WindowsOS`** type the following commands :

- Install the virtual environment and the required packages by following commands.

   For `PowerShell` CLI :

    ```PowerShell
    pyenv local 3.11.3
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

    For `Git-bash` CLI :
  
    ```BASH
    pyenv local 3.11.3
    python -m venv .venv
    source .venv/Scripts/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
     **`Note:`**
    If you encounter an error when trying to run `pip install --upgrade pip`, try using the following command:

    ```Bash
    python.exe -m pip install --upgrade pip
    ```

## Streamlit Dashboard

There is a Streamlit app that allows the data we produced to be examined.

```
streamlit run Decent_Exposure.py
```

It has also been deployed to their community cloud [Decent Exposure](https://eudr-exposure.streamlit.app).

Pick a geograpy first e.g. regression_sample.csv, limit the range of latitude and longitude to the area you are interested in and press 'Apply'.

Alternatively, from the Map page, zoom and pan to an area then press 'Filter' which will update the chosen geography.

## Python Module

We established a Python module called 'leaf' that provides the basis for the exposure.py script, and can be used from Python code and/or Jupyter notebooks. It supports caching of the Hansen dataset that we used for our analysis.

See def earthenginepartners_hansen in deforestaton.py, and its use in deforestation-sample.ipynb, for details.

## Python Script

The exposure.py script takes command line arguments to allow for the manipulation of downloaded files from the Hansen dataset.

```
python -m exposure --help
```

It was predominately used for testing purposes but could form part of a CLI toolchain.



