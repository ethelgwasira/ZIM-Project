## Import basic python functions
import os
import pandas as pd
import numpy as np
## Import dtk and EMOD basics functionalities
from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.SetupParser import SetupParser
from analyzer_collection import InsetChartAnalyzer, AnnualAgebinPfPRAnalyzer
## For plotting
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates

mpl.rcParams['pdf.fonttype'] = 42

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'LOCAL'

user = os.getlogin()  # user initials
expt_name = 'ZBOOK_ZIM-project_Zimbabwe'
expt_id = '2022_07_02_03_00_59_746515' ## change expt_id
working_dir = os.path.join('simulation_outputs')

if __name__ == "__main__":
    SetupParser.init()

    # set desired InsetChart channels to analyze and plot
    channels_inset_chart = ['Statistical Population', 'New Clinical Cases', 'Adult Vectors', 'Infected']

    analyzers = [InsetChartAnalyzer(expt_name=expt_name,
                                    channels=channels_inset_chart,
                                    working_dir=working_dir),
                 AnnualAgebinPfPRAnalyzer(expt_name=expt_name,
                                          working_dir=working_dir,
                                          start_year=2022,
                                          end_year=2025)
                 ]

    am = AnalyzeManager(expt_id, analyzers=analyzers)
    am.analyze()

    # read in analyzed InsetChart data
    df = pd.read_csv(os.path.join(working_dir, expt_name, 'All_Age_InsetChart.csv'))
    df['date'] = pd.to_datetime(df['date'])

    # make InsetChart plot
    fig1 = plt.figure('InsetChart', figsize=(12,6))
    fig1.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    fig1.suptitle(f'Analyzer: InsetChartAnalyzer')
    for ch, channel in enumerate(channels_inset_chart) :
        ax = fig1.add_subplot(2,2,ch+1)
        ax.plot(df['date'], df[channel], '-', linewidth=0.8)
        ax.set_title(channel)
        ax.set_ylabel(channel)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig1.savefig(os.path.join(working_dir, expt_name, 'InsetChart.png'))

    # read in analyzed summary reporrt
    channels_summary_report = ['Pop', 'Cases', 'Severe cases', 'PfPR']
    df = pd.read_csv(os.path.join(working_dir, expt_name, 'Agebin_PfPR_ClinicalIncidence_annual.csv'))
    df = df.sort_values(by='agebin')
    # take mean over all years in report
    df = df.groupby(['agebin', 'Run_Number'])[channels_summary_report].agg(np.mean).reset_index()

    # make summary report plot
    fig2 = plt.figure('Summary Report', figsize=(6, 5))
    fig2.subplots_adjust(right=0.96, left=0.12, hspace=0.55, wspace=0.35, top=0.83, bottom=0.10)
    axes = [fig2.add_subplot(2, 2, x + 1) for x in range(4)]
    fig2.suptitle(f'Analyzer: AnnualAgebinPfPRAnalyzer')

    for ai, channel in enumerate(channels_summary_report):
        ax = axes[ai]
        ax.set_title(channel)
        ax.set_ylabel(channel)
        ax.set_ylim(0, max([1, 1.1*np.max(df[channel])]))
        ax.set_xlabel('age')

        ax.plot(df['agebin'], df[channel], '-', linewidth=0.8)

    fig2.savefig(os.path.join(working_dir, expt_name, 'Agebin_PfPR_ClinicalIncidence.png'))

    plt.show()
