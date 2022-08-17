import os

import numpy as np
import pandas as pd
from dtk.interventions.irs import add_IRS
from dtk.interventions.itn import add_ITN
from dtk.interventions.outbreakindividual import recurring_outbreak
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
burnin_id = "930f9ca0-e11c-ed11-a9fb-b88303911bc1"  # UPDATE with burn-in experiment id
pull_year = 10  # year of burn-in to pick-up from
pickup_years = 4  # years of pick-up to run
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
    #'Enable_Default_Reporting': 1
})

"""Serialization"""
cb.update_params({
    'Serialization_Time_Steps': [365 * pickup_years],
    'Serialization_Type': 'TIMESTEP',
    'Serialized_Population_Writing_Type': 'TIMESTEP',
    #'Serialized_Population_Reading_Type': 'NONE',
    'Serialization_Mask_Node_Write': 0,
    'Serialization_Precision': 'REDUCED'
})


set_species(cb, [ "funestus", "gambiae"])           #"arabiensis",
set_larval_habitat(cb, {
                        "funestus": {'WATER_VEGETATION': 4e8*32.51,  'CONSTANT': 1e7*15.67},
                        "gambiae": {'TEMPORARY_RAINFALL': 8.3e8, 'CONSTANT': 1e7}
                        })      # "arabiensis": {'TEMPORARY_RAINFALL': 7.5e9, 'CONSTANT': 1e7},

recurring_outbreak(cb, start_day=180, repetitions=pickup_years)

# health seeeking, immediate start
def case_management(cb, cm_cov_U5=0.6, cm_cov_adults=0.45):
    add_health_seeking(cb, start_day=0,
                       targets=[{'trigger': 'NewClinicalCase', 'coverage': cm_cov_U5,
                                 'agemin': 0, 'agemax': 5, 'seek': 1, 'rate': 0.3},
                                {'trigger': 'NewClinicalCase', 'coverage': cm_cov_adults,
                                 'agemin': 5, 'agemax': 100, 'seek': 1, 'rate': 0.3}],
                       drug=['Artemether', 'Lumefantrine'],
                       duration=1460)
    add_health_seeking(cb, start_day=0,
                       targets=[{'trigger': 'NewSevereCase', 'coverage': 0.85,
                                 'agemin': 0, 'agemax': 100, 'seek': 1, 'rate': 0.5}],
                       drug=['Artemether', 'Lumefantrine'],
                       duration=1460,
                       broadcast_event_name='Received_Severe_Treatment')
    return {'cm_cov_U5': cm_cov_U5,
            'cm_cov_adults': cm_cov_adults}
event_list = []
event_list = event_list + ['Received_Treatment', 'Received_Severe_Treatment']

# ITN, start after 1 year
def itn_intervention(cb, coverage_level = 0.52, day=1096):
    add_ITN(cb,
            start=day,  # starts on first day of second year
            coverage_by_ages=[
                {"coverage": coverage_level, "min": 0, "max": 5},  # Highest coverage for 0-10 years old
                {"coverage": coverage_level * 0.75, "min": 5, "max": 100},
                # 25% lower than for children for 10-50 years old
                #{"coverage": coverage_level * 0.6, "min": 50, "max": 125}
                # 40% lower than for children for everyone else
            ],
            repetitions=1,  # ITN will be distributed 0 times
            tsteps_btwn_repetitions=365 * 3 + 1096  # three years between ITN distributions
            )
    return {'itn_start': day,
            'itn_coverage': coverage_level}

def irs_intervention(cb, KE):
    irs_days=[325, 690, 1055, 1420]           #, 1785, 2150, 2515, 2880, 3245, 3610, 3975, 4340, 4705, 5070
    #irs_days = [325, 691, 1057, 1423, 1789, 2155, 2521, 2887, 3253, 3619]
    irs_covs = [ 0.93, 0.8, 0.85, 0.92]  # 0, 0, 0, 0, 0.36, 0.43, 0.8, 0.85, 0.92, 0.832
    KEs=[0.15, 0.15, 0.15, 0.15]              # 0.30, 0.29, 0.28, 0.27, 0.26,0.25,0.24,0.18,0.15,
    for i, j,k in zip(irs_days, irs_covs,KEs):
        add_IRS(cb, start= i,
                coverage_by_ages=[
                    {"coverage": j, "min": 0, "max": 100}
                ],
                killing_config={
                    "class": "WaningEffectBoxExponential",
                    "Box_Duration": 60,  #
                    "Decay_Time_Constant": 120,  #
                    "Initial_Effect": k},
                )

    return {'Killing_Effect': KE}


event_list = event_list + ['Received_IRS']
#Enable Reporters
cb.update_params({
    "Report_Event_Recorder": 1,
    "Report_Event_Recorder_Individual_Properties": [],
    "Report_Event_Recorder_Ignore_Events_In_List": 0,
    "Report_Event_Recorder_Events": event_list,
    'Custom_Individual_Events': event_list
})

# Report_Event_Counter
add_event_counter_report(cb, event_trigger_list=event_list, start=0, duration=pickup_years*365)

for i in range(pickup_years):
    add_summary_report(cb, start=1+365*i, interval=30,
                       duration_days=365,
                       age_bins=[0.25, 5, 100],
                       # age_bins=[0.25, 5, 120],
                       description=f'Monthly_U5_{2011+i}')

# run_sim_args is what the `dtk run` command will look for
user = os.getlogin()  # user initials
expt_name = f'{user}_Zimbabwe_Mutasa_PickupB{4}'

builder = ModBuilder.from_list(
    [[ModFn(DTKConfigBuilder.set_param, 'x_Temporary_Larval_Habitat', m),
      ModFn(DTKConfigBuilder.set_param,
            'Serialized_Population_Path',
            os.path.join(ser_df[ser_df.x_Temporary_Larval_Habitat == m].outpath.iloc[0], 'output')),
      ModFn(DTKConfigBuilder.set_param, 'x_Temporary_Larval_Habitat', m),
      ModFn(case_management),
      ModFn(itn_intervention),
      ModFn(irs_intervention, KE=ke)]  #,
     # Run pick-up from each unique burn-in scenario
     for m in np.logspace(-2, np.log10(30), 50)
     for n in range(numseeds)
     for ke in [0.15]
     for itn_cov in [0.52]
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
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())
