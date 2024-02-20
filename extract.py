from fhirpy import AsyncFHIRClient
from datetime import datetime
import pandas as pd

def calculate_age(date_of_birth):   
    dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
    current_date = datetime.now()
    age = current_date.year - dob.year - ((current_date.month, current_date.day) < (dob.month, dob.day))
    return age

def diagnostic_freq(issued, effectivetime):
    if issued is not None and effectivetime is not None:
        issued = pd.to_datetime(issued).replace(tzinfo=None)     # Remove timezone information
        effectivetime = pd.to_datetime(effectivetime).replace(tzinfo=None)    # Remove timezone information
        time_diff = (issued - effectivetime).total_seconds() / 3600
        return time_diff

def ethnicities(value):
    if value == "2186-5":
        return 1
    else:
        return 0

# Define extract_from_fhir_api function
async def extract_from_fhir_api(api_url, token):
    """
    Here's what each part of the query does:

    await client.resources('DiagnosticReport'): This specifies that we want to fetch resources of the type DiagnosticReport.

    .include('DiagnosticReport', 'subject', target_resource_type='Patient'): This instructs the FHIR server to include Patient resources related to each DiagnosticReport resource retrieved. The 'subject' field in DiagnosticReport resources typically references the patient associated with the report. By specifying target_resource_type='Patient', we're indicating that we want to include Patient resources specifically.

    .include('DiagnosticReport', 'result', target_resource_type='Observation'): This instructs the FHIR server to include Observation resources related to each DiagnosticReport resource retrieved. The 'result' field in DiagnosticReport resources typically references the observations that are the result of the diagnostic report. By specifying target_resource_type='Observation', we're indicating that we want to include Observation resources specifically.

    .fetch_all(): This executes the query and retrieves all DiagnosticReport resources along with their related Patient and Observation resources as specified.
    """
    client = AsyncFHIRClient(
        api_url,
        authorization=f'Bearer {token}'
    )

    bundle = await client.resources('DiagnosticReport').include('DiagnosticReport', 'subject', target_resource_type='Patient').include('DiagnosticReport', 'result', target_resource_type='Observation').fetch_all()

    data = []

    for rep_data in bundle:
        blood_leukocytes_volume = None
        blood_erythrocyte_volume = None
        blood_hemoglobin_volume = None
        blood_hematocrit_volume = None
        mcv_count = None
        mch_count = None
        mchc_count = None
        erythrocyte_distribution_width_count = None
        platelets_volume_count = None
        platelet_mean_volume_count = None

        if rep_data is not None:
            date_reported = rep_data.get('effectiveDateTime')
            date_authorised = rep_data.get('issued')
            elapsed_time_days = elapsed_time(date_authorised)

            patient_data = rep_data.get_by_path('subject.reference')
            if patient_data is not None and '/' in patient_data:
                patient_id = patient_data.split('/')[1]
                patients = await client.resources('Patient').search(_id=patient_id).fetch_all()
                for patient in patients:
                    dob = patient.get('birthDate')
                    age = calculate_age(dob)
                    gender = patient.get('gender')
                    race = patient.get_by_path("extension.0.extension.0.valueCoding.code")
                    ethnicity = ethnicities(patient.get_by_path("extension.1.extension.0.valueCoding.code"))
                    
            for observation in rep_data.get('result', []):
                reference = observation.get('reference')
                if reference:
                    obs_id = reference.split('/')[1]
                    blood = await client.resources('Observation').search(_id=obs_id).fetch_all()
                    if blood:
                        code = blood[0].get_by_path('code.coding.0.code')
                        value = blood[0].get_by_path('valueQuantity.value') 

                        # Extracting values based on observation codes
                        if code == "6690-2":  # Leukocytes
                            blood_leukocytes_volume = value
                        elif code == "789-8":  # Erythrocytes
                            blood_erythrocyte_volume = value
                        elif code == "718-7":  # Hemoglobin
                            blood_hemoglobin_volume = value
                        elif code == "4544-3":  # Hematocrit
                            blood_hematocrit_volume = value
                        elif code == "787-2":  # MCV
                            mcv_count = value
                        elif code == "785-6":  # MCH
                            mch_count = value
                        elif code == "786-4":  # MCHC
                            mchc_count = value
                        elif code == "21000-5":  # Erythrocyte distribution width
                            erythrocyte_distribution_width_count = value
                        elif code == "32207-3":  # Platelets
                            platelets_volume_count = value
                        elif code == "32623-1":  # Platelet mean volume
                            platelet_mean_volume_count = value 

                        # Extracting encounter-related information
                        encounter_id = blood[0].get('encounter.reference')
                        if encounter_id is not None and '/' in encounter_id:
                            enc_id = encounter_id.split('/')[1]
                            encounters = await client.resources('Encounter').search(_id=enc_id).fetch_all()
                            for encounter in encounters:
                                if encounter is not None and encounter.get_by_path("type.0.coding.0.code") == "50849002":
                                    encounter_type = encounter.get("type.0.coding.0.code")
                                    reason_code = encounter.get_by_path("reasonCode.0.coding.0.code")
                                    hospitalization_status = encounter.get_by_path("hospitalization.dischargeDisposition.coding.0.code") 

            data.append({
                "elapsed_time_days": elapsed_time_days,
                "age": age,
                "gender": gender,
                "race": race,
                "blood_leukocytes_volume": blood_leukocytes_volume,
                "blood_erythrocyte_volume": blood_erythrocyte_volume,
                "blood_hemoglobin_volume": blood_hemoglobin_volume,
                "blood_hematocrit_volume": blood_hematocrit_volume,
                "mcv_count": mcv_count,
                "mch_count": mch_count,
                "mchc_count": mchc_count,
                "erythrocyte_distribution_width_count": erythrocyte_distribution_width_count,
                "platelets_volume_count": platelets_volume_count,
                "platelet_mean_volume_count": platelet_mean_volume_count,
                "ethnicity": ethnicity
            })

    df = pd.DataFrame(data)
    return df
