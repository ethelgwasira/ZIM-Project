## Import basic python functions
import os
## Import dtk and EMOD basics functionalities
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.species import set_species, set_larval_habitat
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.ModBuilder import ModBuilder, ModFn
## Import custom reporters
from malaria.reports.MalariaReport import add_summary_report
from malaria.reports.MalariaReport import add_event_counter_report
## Import campaign functions
from dtk.interventions.itn import add_ITN
from dtk.interventions.itn_age_season import add_ITN_age_season
from dtk.interventions.irs import add_IRS
from dtk.interventions.novel_vector_control import add_larvicides
from malaria.interventions.health_seeking import add_health_seeking
from malaria.interventions.malaria_drug_campaigns import add_drug_campaign
from malaria.interventions.malaria_vaccine import add_vaccine

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'LOCAL'
years = 3
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM', Simulation_Duration=years * 365)

cb.update_params({
    'Demographics_Filenames': [os.path.join('Mozambique', 'Mozambique_2.5arcmin_demographics.json')],
    "Air_Temperature_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_air_temperature_daily.bin'),
    "Land_Temperature_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_air_temperature_daily.bin'),
    "Rainfall_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_rainfall_daily.bin'),
    "Relative_Humidity_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_relative_humidity_daily.bin'),
    "Age_Initialization_Distribution_Type": 'DISTRIBUTION_COMPLEX'
})

set_species(cb, ["arabiensis", "funestus", "gambiae"])
set_larval_habitat(cb, {"arabiensis": {'TEMPORARY_RAINFALL': 7.5e9, 'CONSTANT': 1e7},
                        "funestus": {'WATER_VEGETATION': 4e8},
                        "gambiae": {'TEMPORARY_RAINFALL': 8.3e8, 'CONSTANT': 1e7}
                        })

"""ADDITIONAL CAMPAIGNS"""
event_list = []  ## Collect events to track in reports
# health seeeking, immediate start
# Clinical cases
add_health_seeking(cb, start_day=0,
                   targets=[{'trigger': 'NewClinicalCase', 'coverage': 0.7,
                             'agemin': 0, 'agemax': 5, 'seek': 1, 'rate': 0.3},
                            {'trigger': 'NewClinicalCase', 'coverage': 0.5,
                             'agemin': 5, 'agemax': 100, 'seek': 1, 'rate': 0.3}],
                   drug=['Artemether', 'Lumefantrine'])
# Severe cases
add_health_seeking(cb, start_day=0,
                   targets=[{'trigger': 'NewSevereCase', 'coverage': 0.49,
                             'seek': 1, 'rate': 0.5}],
                   drug=['Artemether', 'Lumefantrine'],
                   broadcast_event_name='Received_Severe_Treatment')
event_list = event_list + ['Received_Treatment', 'Received_Severe_Treatment']

## malaria vaccine (RTS,S), as mass campaign at 80% at a single day (hypothetical example only!)
#add_vaccine(cb,
#            vaccine_type='RTSS',
#            start_days=[366],
#            coverage=0.1)
#event_list = event_list + ['Received_Vaccine']

## seasonal malaria chemoprevention, start after 1 year
#add_drug_campaign(cb, campaign_type='SMC', drug_code='SPA',
#                  coverage=0.8,
#                  start_days=[366],
#                  repetitions=4,
#                  tsteps_btwn_repetitions=30,
#                  target_group={'agemin': 0.25, 'agemax': 5},
#                  receiving_drugs_event_name='Received_SMC')
#event_list = event_list + ['Received_SMC']

# ITN, start after 1 year
"""Select either add_ITN or add_ITN_age_season"""
add_ITN(cb,
        start=366,  # starts on first day of second year
        coverage_by_ages=[
            {"coverage": 1, "min": 0, "max": 10},  # 100% for 0-10 years old
            {"coverage": 0.75, "min": 10, "max": 50},  # 75% for 10-50 years old
            {"coverage": 0.6, "min": 50, "max": 125}  # 60% for everyone else
        ],
        repetitions=5,  # ITN will be distributed 5 times
        tsteps_btwn_repetitions=365 * 3  # assume annual ITN distributions instead of 1 year in example
        )
event_list = event_list + ['Received_ITN']

# add_ITN_age_season(cb, start=366,
#                    demographic_coverage=0.8,
#                    killing_config={
#                        "Initial_Effect": 0.520249973,  # LLIN Burkina
#                        "Decay_Time_Constant": 1460,
#                        "class": "WaningEffectExponential"},
#                    blocking_config={
#                        "Initial_Effect": 0.53,
#                        "Decay_Time_Constant": 730,
#                        "class": "WaningEffectExponential"},
#                    discard_times={"Expiration_Period_Distribution": "DUAL_EXPONENTIAL_DISTRIBUTION",
#                                   "Expiration_Period_Proportion_1": 0.9,
#                                   "Expiration_Period_Mean_1": 365 * 1.7,  # Burkina 1.7
#                                   "Expiration_Period_Mean_2": 3650},
#                    age_dependence={'Times': [0, 100],
#                                    'Values': [0.9, 0.9]},
#                    duration=-1, birth_triggered=False
#                    )
# event_list = event_list + ['Bednet_Got_New_One', 'Bednet_Using', 'Bednet_Discarded']

# IRS, start after 1 year - single campaign
add_IRS(cb,
        start=366,  # IRS occurs on first day of second year
        coverage_by_ages=[
            {"coverage": 1, "min": 0, "max": 10},  # 100% for 0-10 years old
            {"coverage": 0.75, "min": 11, "max": 50},  # 75% for 11-50 years old
            {"coverage": 0.6, "min": 51, "max": 125}  # 60% for everyone else
        ],
        killing_config={
            "class": "WaningEffectBoxExponential",
            "Box_Duration": 60,
            "Decay_Time_Constant": 120,
            "Initial_Effect": 0.6
        }
        )
event_list = event_list + ['Received_IRS']

## Larviciding, start after 1 year - single campaign
#add_larvicides(cb, start_day=366,
#               habitat_target='CONSTANT',
#               killing_initial=0.4,
#               killing_decay=150)

"""CUSTOM REPORTS"""
# add_filtered_report(cb, start=0, end=years * 365)
## Summary report per agebin
add_summary_report(cb, start=1, interval=365,
                   age_bins=[0.25, 2, 5, 10, 15, 20, 100, 120],
                   description='Annual_Agebin')

## Enable reporters
cb.update_params({
    "Report_Event_Recorder": 1,
    "Report_Event_Recorder_Individual_Properties": [],
    "Report_Event_Recorder_Ignore_Events_In_List": 0,
    "Report_Event_Recorder_Events": event_list,
    'Custom_Individual_Events': event_list
})

## Event_counter_report
add_event_counter_report(cb, event_trigger_list=event_list, start=0, duration=10000)

# run_sim_args is what the `dtk run` command will look for
user = os.getlogin()  # user initials

numseeds = 1
builder = ModBuilder.from_list([[ModFn(DTKConfigBuilder.set_param, 'Run_Number', x),
                                 ModFn(DTKConfigBuilder.set_param, 'Scenario', 'Basic')  # optional
                                 ]
                                for x in range(numseeds)])

run_sim_args = {
    'exp_name': f'{user}_ZIM-project_Zimbabwew3a',
    'config_builder': cb,
    'exp_builder': builder
}

# If you prefer running with `python example_sim.py`, you will need the following block
if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())