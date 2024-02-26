# Project description
Fast Healthcare Interoperability Resources (FHIR) revolutionizes data exchange in healthcare, enhancing interoperability across systems. One of the reasons for performing machine learning (ML) using FHIR data is to show an end-to-end process of ML healthcare workflows for patient care improvement.

# Getting started
To demonstrate the machine learning model building, API creation, and data modeling in FHIR. It is good to know the following:
1. FHIR Standards:
Familiarize yourself with the Fast Healthcare Interoperability Resources (FHIR) standard using the [FHIR Documentation](https://fhir-ru.github.io/documentation.html). However, a good knowledge of [FHIR resources RESTful APIs, searching, and the principles](https://fhir-ru.github.io/search.html) of data exchange in healthcare is important.

2. Knowledge of `pycaret`:
This is one of the best machine-learning frameworks for easy machine-learning processes and workflows. [Pycaret](https://pycaret.gitbook.io/docs/get-started/installation) makes ML easy to understand and code.
4. Choose a FHIR Client framework:
Utilize FHIR client libraries in [Python](https://docs.smarthealthit.org/client-py/) in your chosen programming language. These libraries simplify the process of working with FHIR data management. In our case, we are using [fhirpy](https://github.com/beda-software/fhir-py#readme)

# Setting the ML process
1. To be able to perform this, set up your FHIR server as discussed above.
2. Download your synthetic data from [synthea](https://mitre.box.com/shared/static/ydmcj2kpwzoyt6zndx4yfz163hfvyhd0.zip)
3. If you are using Azure API for FHIR use [FhirLoader](https://github.com/hansenms/FhirLoader) as recommended by Microsoft Azure to upload it to the API.
4. Else, if you are using your own Hapi FHIR, [upload](https://rajvansia.com/synthea-hapi-fhir.html) your data as described by the author.
     Here the process of ETL will change with some variations, which is to be updated later.
5. Download this repository `https://github.com/EthelEz/machine-learning-fhir.git` in your preferred directory.
6. Install necessary packages by running `python -r requirements.txt`
7. Create a `.env` file and add
     ```
     api_url="add-your-azure-fhir-url-here"
     client_id="add-client-id-here"
     client_secret="add-client-secret-here"
     tenant_id="add-client-tenant_id-here"
     ```
10. If the setup and every other thing is installed correctly, then run `python fhir_ml_model.py` to perform the extract data from FHIR API, process, train and save the ML model.
    
      **Please Note** This process takes about 15 to 20 minutes to run. This is due to the size of the dataset we're extracting from the API and loading to Postgres.
11. After training the model, run `python fhir_ml_api.py` and then go to your preferred browser and run `http://127.0.0.1:8005/docs#`.
12. You can also use the `Postman` or `Curl` command to test the API.


### Using `Postman` to send data to the `Azure FHIR API`

If you are using `Postman`, you can try this example data
```
{
    "patient": {
        "id": "67d8cf29-e6d8-4661-9776-69d72ba7c96b",
        "name": {
            "firstname": "Lowe",
            "lastname": "Kevin"
        }
    },
    "observation": {
        "elapsed_time_days": 1813,
        "age": 4,
        "gender": "male",
        "race": "2106-3",
        "blood_leukocytes_volume": 8.243,
        "blood_erythrocyte_volume": 4.1092,
        "blood_hemoglobin_volume": 16.348,
        "blood_hematocrit_volume": 36.004,
        "mcv_count": 82.019,
        "mch_count": 29.171,
        "mchc_count": 33.903,
        "erythrocyte_distribution_width_count": 42.179,
        "platelets_volume_count": 391.02,
        "platelet_mean_volume_count": 11.111
    }
}
```
