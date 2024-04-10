import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import ServerFiles as sf
import os
import pandas as pd
from pandasgui import show

testing = False


#       ESO API Data Gathering
# =======================================================================================
def construct_query(start_date=datetime(2024, 3, 3), end_date=datetime(2024, 3, 3, 3)):
    try:
        # Your ESO Subscription ID
        load_dotenv(find_dotenv())
        subscription_id = os.getenv("ESO_API_KEY")
        # API endpoint
        url = "https://esoapis.net/incidents/v0/byLastModified"

        # Query parameters
        params = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "subscription-key": subscription_id,
        }
    except Exception as e:
        print(f"Failed to Contruct ESO Query: {e}")
        return None
    return {"url": url, "params": params}


def get_eso(eso_query):
    response = requests.get(eso_query["url"], params=eso_query["params"])

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve data:", response)
        return None


# def explode_data(data):
#     try:
#         # Extracting the 'Incidents' list and flattening it
#         incidents_df = pd.json_normalize(data, record_path=["incidents"])

#         # Adding the other attributes to the incidents DataFrame
#         for column in [
#             "lastModifiedDate",
#             "lastIncidentDate",
#             "lastIncidentDateString",
#         ]:
#             incidents_df[column] = data[column]
#         return incidents_df
#     except Exception as e:
#         print(f"Failed to Explode Data: {e}")
#         return None


#       Response Grouping
# =======================================================================================

groupings = {
    "Basic": {
        "entry_path": "incident.incidentId",
        "field_paths": {
            "IncidentId": "incident.incidentId",
            "NFIRSIncidentNumber": "incident.nfirsIncidentNumber",
            "IncidentNumber": "incident.incidentNumber",
            "IncidentDate": "incident.incidentDate",
            # Exposures
            "ExposureId": "exposure.exposureId",
            "sequenceNumber": "exposure.sequenceNumber",
            "IncidentTypeCode": "exposure.incidentType.code",
            "IncidentType": "exposure.incidentType.entityName",
            "initialDispatchCode": "exposure.initialDispatchCode",
            "workingFire": "exposure.workingFire",
            "CriticalIncident": "exposure.criticalIncident",
            "CriticalIncidentTeamMobilized": "exposure.criticalIncidentTeamMobilized",
            "reportToIRWIN": "exposure.reportToIRWIN",
            "Alarms": "exposure.alarms",
            "Station": "exposure.station",
            "StationName": "exposure.stationName",
            "Shift": "exposure.shift",
            "District": "exposure.district",
            "DistrictName": "exposure.districtName",
            "ResourceFormUsed": "exposure.resourceFormUsed",
            # Deaths/Injuries
            "fireServiceDeaths": "exposure.fireServiceDeaths",
            "otherDeaths": "exposure.otherDeaths",
            "fireServiceInjuries": "exposure.fireServiceInjuries",
            "otherInjuries": "exposure.otherInjuries",
            "HazardousMaterialReleased": "exposure.hazardousMaterialReleased",
            # Timing
            "fireDiscoveryDatetime": "exposure.fireDiscoveryDatetime",
            "PSAPDatetime": "exposure.pSAPDatetime",
            "AlarmDatetime": "exposure.alarmDatetime",
            "DispatchNotifiedDatetime": "exposure.dispatchNotifiedDatetime",
            "ArrivalDatetime": "exposure.arrivalDatetime",
            "WaterOnFireDatetime": "exposure.waterOnFireDatetime",
            "LossStopDatetime": "exposure.lossStopDatetime",
            "AtPatientDatetime": "exposure.atPatientDatetime",
            "IncidentControlledDateTime": "exposure.incidentControlledDateTime",
            "LastUnitClearedDatetime": "exposure.lastUnitClearedDatetime",
            "ActionsTaken": "exposure.actionsTaken",  # List of Actions  [{code:t,entityName:t,entityNameText:t },{}]
            "CriticalIncidentCircumstances": "exposure.criticalIncidentCircumstances",
            # Aid
            "AidGivenOrReceived": "exposure.aidDetails.aidGivenOrReceived.entityName",
            "AidedAgency": "exposure.aidDetails.aidedAgency",
            "AidedAgencyIncidentNumber": "exposure.aidDetails.aidedAgencyIncidentNumber",
            "AidingAgencies": "exposure.aidDetails.aidingAgencies",
            # Location
            "AddressOnWildland": "exposure.locationDetails.addressOnWildland",
            "LocationTypeCode": "exposure.locationDetails.locationType.entityName",
            "LocationType": "exposure.locationDetails.locationType.entityName",
            "PropertyUseCode": "exposure.locationDetails.propertyUse.code",
            "PropertyUse": "exposure.locationDetails.propertyUse.entityName",
            "MixedUse": "exposure.locationDetails.mixedUse",
            "CensusTract": "exposure.locationDetails.censusTract",
            "DetectorAlertedOccupants": "exposure.locationDetails.detectorAlertedOccupants",
            # Address
            "NumberOrMilepost": "exposure.locationDetails.addressDetails.numberOrMilepost",
            "StreetPrefixCode": "exposure.locationDetails.addressDetails.streetPrefix.code",
            "StreetPrefix": "exposure.locationDetails.addressDetails.streetPrefix.entityName",
            "StreetOrHighwayName": "exposure.locationDetails.addressDetails.streetOrHighwayName",
            "StreetTypeCode": "exposure.locationDetails.addressDetails.streetType.code",
            "StreetType": "exposure.locationDetails.addressDetails.streetType.entityName",
            "StreetSuffix": "exposure.locationDetails.addressDetails.streetSuffix",
            "PostOfficeBox": "exposure.locationDetails.addressDetails.postOfficeBox",
            "ApartmentNumber": "exposure.locationDetails.addressDetails.apartmentNumber",
            "City": "exposure.locationDetails.addressDetails.city",
            "State": "exposure.locationDetails.addressDetails.state.entityName",
            "Zip": "exposure.locationDetails.addressDetails.zip",
            "County": "exposure.locationDetails.addressDetails.county",
            # Location Cont
            "Directions": "exposure.locationDetails.directions",
            "Latitude": "exposure.locationDetails.latitude",
            "Longitude": "exposure.locationDetails.longitude",
            # Owner Details
            "personsAndEntities": "exposure.personsAndEntities",  # []
            "OwnerSequenceNumber": "exposure.ownerDetails.sequenceNumber",
            "OwnerNameDetails": "exposure.ownerDetails.nameDetails",
            "OwnerAddressSameAsIncident": "exposure.ownerDetails.addressSameAsIncident",
            "OwnerAddressDetails": "exposure.ownerDetails.addressDetails",
            "OwnerBusinessName": "exposure.ownerDetails.businessName",
            "OwnerPhone": "exposure.ownerDetails.phone",
            "OwnerAffiliation": "exposure.ownerDetails.affiliation",
            "OwnerInsuranceCompany": "exposure.ownerDetails.insuranceCompany",
            "OwnerTotalInsuranceAmount": "exposure.ownerDetails.totalInsuranceAmount",
            "OwnerInvolvedInIncident": "exposure.ownerInvolvedInIncident",
            # Loss
            "vehicles": "exposure.vehicles",
            "PropertyLoss": "exposure.propertyLoss",
            "PropertyValue": "exposure.propertyValue",
            "ContentsLoss": "exposure.contentsLoss",
            "ContentsValue": "exposure.contentsValue",
            "PropertyLossIsNone": "exposure.propertyLossIsNone",
            "PropertyValueIsNone": "exposure.propertyValueIsNone",
            "ContentsLossIsNone": "exposure.contentsLossIsNone",
            "ContentsValueIsNone": "exposure.contentsValueIsNone",
            # apparatusesAndPersonnel
            "apparatusesAndPersonnel": "exposure.apparatusesAndPersonnel",  # [{{}{}{}}]
            "SuppressionApparatusCount": "exposure.suppressionApparatusCount",
            "SuppressionPersonnelCount": "exposure.suppressionPersonnelCount",
            "EmsApparatusCount": "exposure.emsApparatusCount",
            "EmsPersonnelCount": "exposure.emsPersonnelCount",
            "OtherApparatusCount": "exposure.otherApparatusCount",
            "OtherPersonnelCount": "exposure.otherPersonnelCount",
            "ResourcesIncludeMutualAid": "exposure.resourcesIncludeMutualAid",
            "ReportWriterName": "exposure.reportWriterDetails.NameDetails",
            "ReportWriterAssignment": "exposure.reportWriterDetails.Assignment",
            "ReportWriterRank": "exposure.reportWriterDetails.Rank",
            "OfficerInCharge": "exposure.officerInChargeDetails.nameDetails",
            "OfficerInChargeAssignment": "exposure.officerInChargeDetails.Assignment",
            "OfficerInChargeRank": "exposure.officerInChargeDetails.Rank",
            "Narratives": "exposure.narratives",  # [{}]
            # More Details
            "fireDetails": "exposure.fireDetails",
            "civilianCasualties": "exposure.civilianCasualties",  # []
            "emsPatients": "exposure.emsPatients",  # []
            "hazmatDetails": "exposure.hazmatDetails",
            "wildlandDetails": "exposure.wildlandDetails",
            "arsonDetails": "exposure.arsonDetails",
            "cadNotes": "exposure.cadNotes",
            "Covid19Factor": "exposure.covid19Factor",
            "temporaryResidentInvolvement": "exposure.temporaryResidentInvolvement",
            "qualityControlFirstName": "exposure.qualityControlFirstName",
            "qualityControlLastName": "exposure.qualityControlLastName",
            "qualityControlCompletedDate": "exposure.qualityControlCompletedDate",
        },
    },
    # "Arson": {
    #     "entry_path": "exposure.arsonDetails",
    #     "field_paths": {
    #         "exposureId": "exposure.exposureId",
    #         "IncidentId": "incident.incidentId",
    #         "AgencyName": "exposure.arsonDetails.agencyName",
    #         "PhoneNumber": "exposure.arsonDetails.phoneNumber",
    #         "CaseNumber": "exposure.arsonDetails.caseNumber",
    #         "AgencyORI": "exposure.arsonDetails.agencyORI",
    #         "AgencyFID": "exposure.arsonDetails.agencyFID",
    #         "AgencyFDID": "exposure.arsonDetails.agencyFDID",
    #         "ArsonAgencyReferralNumberOrMilepost": "exposure.arsonDetails.referralNumberOrMilepost",
    #         "ArsonAgencyReferralStreetPrefix": "exposure.arsonDetails.streetPrefix",
    #         "ArsonAgencyReferralStreetOrHighwayName": "exposure.arsonDetails.streetOrHighwayName",
    #         "ArsonAgencyReferralStreetType": "exposure.arsonDetails.streetType",
    #         "ArsonAgencyReferralStreetSuffix": "exposure.arsonDetails.streetSuffix",
    #         "ArsonAgencyReferralPostOfficeBox": "exposure.arsonDetails.postOfficeBox",
    #         "ArsonAgencyReferralApt/Suite/Room": "exposure.arsonDetails.aptSuiteRoom",
    #         "ArsonAgencyReferralCity": "exposure.arsonDetails.city",
    #         "ArsonAgencyReferralState": "exposure.arsonDetails.state",
    #         "ArsonAgencyReferralZip": "exposure.arsonDetails.zip",
    #         "ArsonAgencyReferralCounty": "exposure.arsonDetails.county",
    #         "CaseStatus": "exposure.arsonDetails.caseStatus",
    #         "AvailabilityOfFirstMaterialIgnited": "exposure.arsonDetails.firstMaterialIgnited",
    #         "PropertyOwnership": "exposure.arsonDetails.propertyOwnership",
    #         "LaboratoriesUsed": "exposure.arsonDetails.laboratoriesUsed",
    #         "InitialObservations": "exposure.arsonDetails.initialObservations",
    #         "OtherInvestigativeInfos": "exposure.arsonDetails.otherInvestigativeInfo",
    #         "EntryMethod": "exposure.arsonDetails.entryMethod",
    #         "ExtentOfFireInvolvement": "exposure.arsonDetails.extentOfFireInvolvement",
    #         "IncendiaryContainer": "exposure.arsonDetails.incendiaryContainer",
    #         "IncendiaryIgnitionOrDelayDevice": "exposure.arsonDetails.ignitionOrDelayDevice",
    #         "IncendiaryFuel": "exposure.arsonDetails.incendiaryFuel",
    #         "SuspectedMotivations": "exposure.arsonDetails.suspectedMotivations",
    #         "GroupInvolvements": "exposure.arsonDetails.groupInvolvements",
    #         "DateOfBirth": "exposure.arsonDetails.dateOfBirth",
    #         "AgeEstimated": "exposure.arsonDetails.ageEstimated",
    #         "Age": "exposure.arsonDetails.age",
    #         "Sex": "exposure.arsonDetails.sex",
    #         "Race": "exposure.arsonDetails.race",
    #         "Ethnicity": "exposure.arsonDetails.ethnicity",
    #         "FamilyType": "exposure.arsonDetails.familyType",
    #         "Motivation": "exposure.arsonDetails.motivation",
    #         "RiskFactors": "exposure.arsonDetails.riskFactors",
    #         "Disposition": "exposure.arsonDetails.disposition",
    #         "Remarks": "exposure.arsonDetails.remarks",
    #     },
    # },
}


#       Aggregation Functions
# =======================================================================================
def getPath(response, path):
    """
    Navigate through the path in a nested dictionary and return the value found at the end,
    specially handling lists to gather multiple data points if necessary.
    """
    keys = path.split(".")
    value = response
    for key in keys:
        if testing:
            print(f"{key} > ", end="")
        if isinstance(value, dict):
            value = value.get(key)
        elif isinstance(value, list) and key.isdigit():
            value = value[int(key)]  # Access specific index if key is a digit
        else:
            # If encountering a list without a digit key, return the list as is
            print(f"!!! '{path}' not found")
            break
    if testing and value:
        print(f"\n\tFound Value: {value}")
    return value


def process_exposure(exposure, incident, group_config):
    """
    Process a single exposure, extracting data according to the data_group mapping.
    """
    current_data = {}
    entry_path = group_config["entry_path"]
    field_paths = group_config["field_paths"]

    # Check if the entry_path exists and is not None before proceeding
    entry_point = getPath(
        incident if entry_path.startswith("incident") else exposure,
        entry_path.replace("incident.", "").replace("exposure.", ""),
    )

    if entry_point is None:
        print(f"Entry Point ({entry_path}) not found, skipping Field")
        return None

    for key, path in field_paths.items():
        if path.startswith("incident."):
            adjusted_path = path[9:]  # Adjust the path to remove 'incident.' prefix.
            entry_point = incident
        else:
            adjusted_path = path.replace(
                "exposure.", ""
            )  # Adjust path for use with exposure.
            entry_point = (
                exposure if exposure else incident
            )  # Use incident if exposure is None.

        current_data[key] = getPath(entry_point, adjusted_path)
    if not current_data:
        return None
    return current_data


def get_data_by_group(response, group_config):
    """
    Accept ESO response data, along with a group configuration that includes an entry path and mapping paths to the data we want to pull.
    Returns a complete dataframe with columns contained in said data_group, excluding entries where process_exposure returns None.
    """
    aggregate_data = []

    for incident in response.get("incidents", []):
        exposures = (
            incident.get("exposures", [{}]) if incident.get("exposures") else [None]
        )
        exposure_data_list = [
            process_exposure(exposure, incident, group_config) for exposure in exposures
        ]

        # Filter out None values returned by process_exposure before adding to aggregate_data
        exposure_data_list = [data for data in exposure_data_list if data is not None]

        # Only add to aggregate data if there's something to add
        if exposure_data_list:
            aggregate_data.extend(exposure_data_list)

    # If there's no data to aggregate, return an empty DataFrame with the specified columns from any of the group configurations
    if not aggregate_data:
        return pd.DataFrame(
            columns=[key for key in group_config.get("field_paths", {})]
        )

    finalized_dataframe = pd.DataFrame(aggregate_data)
    return finalized_dataframe


def group_data(response):
    """
    Adjusted function to collect arson-related data, including handling lists within the path.
    """
    group_dfs = {}
    for name in groupings.keys():
        print(f"# Gathering [{name}] data")

        group_dfs[name] = get_data_by_group(response, groupings[name])
    return group_dfs


def main():
    sf.setup_logging("..\\logs\\ESO Pull.log")

    eso_query = construct_query()
    eso_data = get_eso(eso_query)

    group_dfs = group_data(eso_data)

    if group_dfs:
        show(**group_dfs)


if __name__ == "__main__":
    main()
