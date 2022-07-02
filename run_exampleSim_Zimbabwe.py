## Import basic python functions
import os
## Import dtk and EMOD basics functionalities
from dtk.interventions.irs import add_IRS
from dtk.interventions.itn import add_ITN
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.species import set_species, set_larval_habitat
from malaria.interventions.health_seeking import add_health_seeking
from malaria.interventions.malaria_drug_campaigns import add_drug_campaign
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

## Import custom reporters
from malaria.reports.MalariaReport import add_summary_report, add_event_counter_report

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'LOCAL'
#SetupParser.default_block = 'HPC'
years = 4
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM', Simulation_Duration=years * 365)

"""MODIFIED SETTING SPECIFIC FILES"""
cb.update_params({
    'Demographics_Filenames': [os.path.join('Mozambique', 'Mozambique_2.5arcmin_demographics.json')],
    "Air_Temperature_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_air_temperature_daily.bin'),
    "Land_Temperature_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_air_temperature_daily.bin'),
    "Rainfall_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_rainfall_daily.bin'),
    "Relative_Humidity_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_relative_humidity_daily.bin'),
    "Age_Initialization_Distribution_Type": 'DISTRIBUTION_COMPLEX'
})

"""Optional update other parameters (explorative)"""
cb.update_params({
    'x_Base_Population': 1,
    'x_Birth': 1,
    'x_Temporary_Larval_Habitat': 1
})

set_species(cb, ["arabiensis", "funestus", "gambiae"])
set_larval_habitat(cb, {"arabiensis": {'TEMPORARY_RAINFALL': 7.5e9, 'CONSTANT': 1e7},
                        "funestus": {'WATER_VEGETATION': 4e8},
                        "gambiae": {'TEMPORARY_RAINFALL': 8.3e8, 'CONSTANT': 1e7}
                        })
#Outputs
"""CUSTOM REPORTS"""
add_summary_report(cb, start=1, interval=365,
                   age_bins=[0.25, 2, 5, 10, 15, 20, 100, 120],
                   description='Annual_Agebin')
#Interventions
#Clinical cases
add_health_seeking(cb, start_day=366,
                    targets=[{'trigger': 'NewClinicalCase', 'coverage': 0.7,
                              'agemin': 0, 'agemax': 5, 'seek': 1, 'rate': 0.3},
                             {'trigger': 'NewClinicalCase', 'coverage': 0.5,
                              'agemin': 5, 'agemax': 100, 'seek': 1, 'rate': 0.3}],
                    drug=['Artemether', 'Lumefantrine'])
#Severe cases
add_health_seeking(cb, start_day=366,
                    targets=[{'trigger': 'NewSevereCase', 'coverage': 0.49,
                     'seek': 1, 'rate': 0.5}],
            drug=['Artemether', 'Lumefantrine'],
            broadcast_event_name='Received_Severe_Treatment')
#ITN
add_ITN(cb,
         start=366,  # starts on first day of second year
         coverage_by_ages=[
             {"coverage": 1, "min": 0, "max": 10},  # Highest coverage for 0-10 years old
             {"coverage": 0.75, "min": 10, "max": 50}, # 25% lower than for children for 10-50 years old
             {"coverage":  0.6, "min": 50, "max": 125} # 40% lower than for children for everyone else
         ],
         repetitions=5,  # ITN will be distributed 5 times
         tsteps_btwn_repetitions=365 * 3  # three years between ITN distributions
         )
#IRS
add_IRS(cb, start=366,
        coverage_by_ages=[{"coverage": 0.8, "min": 0, "max": 100}],
        killing_config={
            "class": "WaningEffectBoxExponential",
            "Box_Duration": 180,  # based on PMI data from Burkina
            "Decay_Time_Constant": 90,  # Sumishield from Benin
            "Initial_Effect": 0.7},
        )
#SMC
#add_drug_campaign(cb, campaign_type='SMC', drug_code='SPA',
#                   coverage=0.8,
#                   start_days=[366],
#                   repetitions=4,
#                   tsteps_btwn_repetitions=30,
#                   target_group={'agemin': 0.25, 'agemax': 5},
#                   receiving_drugs_event_name='Received_SMC')


# run_sim_args is what the `dtk run` command will look for
user = os.getlogin()  # user initials

run_sim_args = {
    'exp_name': f'{user}_ZIM-project_Zimbabwe',
    'config_builder': cb,
}
#To keep track of the campaign events in the simulations
#event_list = ['Received_Treatment', 'Received_ITN', 'Received_SMC']
event_list = ['Received_Treatment', 'Received_ITN']
add_event_counter_report(cb, event_trigger_list=event_list, start=0, duration=10000)

cb.update_params({
   "Report_Event_Recorder": 0,
   "Report_Event_Recorder_Individual_Properties": [],
   "Report_Event_Recorder_Ignore_Events_In_List": 0,
   "Report_Event_Recorder_Events": event_list,
   'Custom_Individual_Events': event_list
})


# If you prefer running with `python example_sim.py`, you will need the following block
if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())
