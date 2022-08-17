import os

import numpy as np
import pandas as pd
from dtk.interventions.irs import add_IRS
from dtk.interventions.itn import add_ITN
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.species import set_species, set_larval_habitat
from malaria.interventions.health_seeking import add_health_seeking
from malaria.reports.MalariaReport import add_event_counter_report, add_summary_report
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.SetupParser import SetupParser
from simtools.ModBuilder import ModBuilder, ModFn

# This block will be used unless overridden on the command-line
from simtools.Utilities.Experiments import retrieve_experiment

SetupParser.default_block = 'HPC'
burnin_id = "feb39fba-e719-ed11-a9fb-b88303911bc1"  # UPDATE with burn-in experiment id
pull_year = 50  # year of burn-in to pick-up from
pickup_years = 14  # years of pick-up to run
numseeds = 1

SetupParser.init()
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
expt = retrieve_experiment(burnin_id)  # Identifies the desired burn-in experiment
# Loop through unique "tags" to distinguish between burn-in scenarios (ex. varied historical coverage levels)
ser_df = pd.DataFrame([x.tags for x in expt.simulations])
ser_df["outpath"] = pd.Series([sim.get_path() for sim in expt.simulations])
#print(ser_df.columns)
#exit(0)
#Input
cb.update_params({
    'Demographics_Filenames': [os.path.join('Mozambique', 'Mozambique_2.5arcmin_demographics.json')],
    "Air_Temperature_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_air_temperature_daily.bin'),
    "Land_Temperature_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_air_temperature_daily.bin'),
    "Rainfall_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_rainfall_daily.bin'),
    "Relative_Humidity_Filename": os.path.join('Mozambique', 'Mozambique_30arcsec_relative_humidity_daily.bin'),
    "Age_Initialization_Distribution_Type": 'DISTRIBUTION_COMPLEX',
    "Birth_Rate_Dependence": "FIXED_BIRTH_RATE",
    'Simulation_Duration': pickup_years * 365,
    'Serialized_Population_Reading_Type': 'READ',
    'Serialized_Population_Filenames': ['state-%05d.dtk' % (pull_year * 365)],#state07300.dtk
    'Enable_Random_Generator_From_Serialized_Population': 0,
    'Serialization_Mask_Node_Read': 0,
    'Enable_Default_Reporting': 1
})

set_species(cb, [ "funestus", "gambiae"])           #"arabiensis",
set_larval_habitat(cb, {
                        "funestus": {'WATER_VEGETATION': 4e8*32.51,  'CONSTANT': 1e7*15.67},
                        "gambiae": {'TEMPORARY_RAINFALL': 8.3e8, 'CONSTANT': 1e7}
                        })      # "arabiensis": {'TEMPORARY_RAINFALL': 7.5e9, 'CONSTANT': 1e7},

# IRS, start after 1 year - single campaign
# def irs_intervention(cb, coverage_level, day=366):
#     add_IRS(cb, start=day,
#             coverage_by_ages=[{"coverage": coverage_level, "min": 0, "max": 100}],
#             killing_config={
#                 "class": "WaningEffectBoxExponential",
#                 "Box_Duration": 180,  # based on PMI data from Burkina
#                 "Decay_Time_Constant": 90,  # Sumishield from Benin
#                 "Initial_Effect": 0.7}
#             )
#
#     return {'irs_start': day,
#            'irs_coverage': coverage_level}

#def irs_intervention(cb, coverage_level, day=366):
    # add_IRS(cb,
    #         start=325,
    #         coverage_by_ages=[{"coverage": coverage_level, "min": 0, "max": 92}],
    #         killing_config={
    #             "class": "WaningEffectBoxExponential",
    #             "Box_Duration": 60,  # based on PMI data from Burkina
    #             "Decay_Time_Constant": 90,  # Sumishield from Benin
    #             "Initial_Effect": 0.6},
    #         )

# health seeeking, immediate start
def case_management(cb, cm_cov_U5=0.7, cm_cov_adults=0.5):
    add_health_seeking(cb, start_day=0,
                       targets=[{'trigger': 'NewClinicalCase', 'coverage': cm_cov_U5,
                                 'agemin': 0, 'agemax': 5, 'seek': 1, 'rate': 0.3},
                                {'trigger': 'NewClinicalCase', 'coverage': cm_cov_adults,
                                 'agemin': 5, 'agemax': 100, 'seek': 1, 'rate': 0.3}],
                       drug=['Artemether', 'Lumefantrine'],
                       duration=3985)
    add_health_seeking(cb, start_day=0,
                       targets=[{'trigger': 'NewSevereCase', 'coverage': 0.85,
                                 'agemin': 0, 'agemax': 100, 'seek': 1, 'rate': 0.5}],
                       drug=['Artemether', 'Lumefantrine'],
                       duration=3985,
                       broadcast_event_name='Received_Severe_Treatment')
    return {'cm_cov_U5': cm_cov_U5,
            'cm_cov_adults': cm_cov_adults}
event_list = []
event_list = event_list + ['Received_Treatment', 'Received_Severe_Treatment']

def irs_intervention(cb, coverage_level, day=325):
    add_IRS(cb, start= day,
            coverage_by_ages=[{"coverage": coverage_level, "min": 0, "max": 100}],
            killing_config={
                "class": "WaningEffectBoxExponential",
                "Box_Duration": 60,  # based on PMI data from Burkina
                "Decay_Time_Constant": 90,  # Sumishield from Benin
                "Initial_Effect": 0.6},
            )

    return {'irs_start': day,
            'irs_coverage': coverage_level}

event_list = event_list + ['Received_IRS']
#Enable Reporters
cb.update_params({
    "Report_Event_Recorder": 1,
    "Report_Event_Recorder_Individual_Properties": [],
    "Report_Event_Recorder_Ignore_Events_In_List": 1,
    "Report_Event_Recorder_Events": event_list,
    'Custom_Individual_Events': event_list
})

# Report_Event_Counter
add_event_counter_report(cb, event_trigger_list=event_list, start=0, duration=pickup_years*365)

#for i in range(pickup_years):
   # add_summary_report(cb, start=1 + 365 * i, interval=365,
add_summary_report(cb, start=0, interval=365,
                       duration_days=pull_year*365,
                       age_bins=[5, 100],                  #0.25,
                       #description=f'Monthly_U5_{2010+i}')
                       description=f'Annual_Agebin')#_{2010 + i}')

# run_sim_args is what the `dtk run` command will look for
user = os.getlogin()  # user initials
expt_name = f'{user}_ZIM-project_Pickup_Zimbabwe{pull_year}_int'

builder = ModBuilder.from_list(
    [[ModFn(DTKConfigBuilder.set_param, 'x_Temporary_Larval_Habitat', m),
      ModFn(DTKConfigBuilder.set_param,
            'Serialized_Population_Path',
            os.path.join(ser_df[ser_df.x_Temporary_Larval_Habitat == m].outpath.iloc[0], 'output')),
      ModFn(DTKConfigBuilder.set_param, 'x_Temporary_Larval_Habitat', m),
      ModFn(case_management),
      ModFn(irs_intervention, coverage_level=irs_cov)]
     # Run pick-up from each unique burn-in scenario
     for m in np.logspace(-2, np.log10(30), 50)
     for n in range(numseeds)
     for irs_cov in [0.7]
     ])

run_sim_args = {
    'exp_name' : expt_name,
    'config_builder': cb,
    'exp_builder': builder
}

# If you prefer running with `python example_sim.py`, you will need the following block
if __name__ == "__main__":
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    # exp_manager.wait_for_finished(verbose=True)
    # assert (exp_manager.succeeded())
