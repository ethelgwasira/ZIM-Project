import os

import pandas as pd
import matplotlib as mpl

mpl.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from calibtool.LL_calculators import beta_binomial

user = os.getlogin()  # user initials
expt_name = f'{user}_ZIM-project_Pickup_Zimbabwe{50}'
output_dir = os.path.join('simulation_outputs')
input_dir = os.path.join('input')
data_dir = os.path.join('data')

#sim_pfpr_df = pd.read_csv(os.path.join(output_dir, expt_name, 'Agebin_PfPR_ClinicalIncidence_annual.csv'))
sim_pfpr_df = pd.read_csv(os.path.join(output_dir, expt_name, 'Agebin_PfPR_ClinicalIncidence_annual.csv'))
sim_pfpr_df = sim_pfpr_df[sim_pfpr_df.agebin == 5]
dhs_pfpr_df = pd.read_csv(os.path.join(data_dir, 'U5PfPR.csv'))
sweep_variables = ['x_Temporary_Larval_Habitat', 'Run_Number', 'Killing_Effect']


def score(sim_df, data_df, sweep_variables):
    comb_df = data_df.merge(sim_df, on=['year'], how='left')
    comb_df['se'] = (comb_df['PfPR'] - comb_df['U5PfPR'])**2

    df = comb_df.groupby(sweep_variables).mean()['se'].reset_index().sort_values(by=['se'])

    return df


def plot_output(sim_df, data_df, score_df, variable):
    sim_df['date'] = pd.to_datetime([f'{y}-01-01' for y in (sim_df.year)])#, sim_df.month)])
    data_df['date'] = pd.to_datetime([f'{y}-01-01' for y in (data_df.year)]) #f'{y}-{m}-01' for y in zip(data_df.year, data_df.month)])
    data_df['PfPR'] = data_df['DHS_pos'] / data_df['DHS_n']
    sns.set_style('whitegrid', {'axes.linewidth': 0.5})
    fig = plt.figure(figsize=(12, 5))
    axes = [fig.add_subplot(1, 2, x + 1) for x in range(2)]

    candidate_val = score_df[variable]

    for cand in candidate_val:
        plot_df = sim_df[sim_df[variable] == cand]
        a = 1 if cand == score_df[variable].max() else 0.15
        axes[0].plot(plot_df['date'], plot_df['PfPR'], color='#FF0000', alpha=a)

    axes[0].scatter(data_df['date'].values, data_df['PfPR'], data_df['DHS_n'], 'k')
    axes[0].set_ylabel('PfPR')
    axes[0].set_title('Observed vs Simulated (Dark red is the best fit)')

    score_df1 = score_df[score_df.ll == score_df.ll.max()]
    axes[1].plot(score_df[variable], score_df['ll'], '-o', color='#FF0000', markersize=5)
    axes[1].scatter(score_df1[variable], score_df1.ll, s=90, color='red')
    axes[1].set_ylabel('log-likelihood')
    axes[1].set_xlabel('x_Temporary_Larval_Habitat')
    axes[1].set_title('Mean log-likelihood. Larger value = better fit')

    fig.savefig(os.path.join(output_dir, expt_name, 'selection.png'))


if __name__ == "__main__":
    scores = score(sim_pfpr_df, dhs_pfpr_df, sweep_variables)
    print(scores.dropna())
    exit(0)
    sim_pfpr_agg = sim_pfpr_df.groupby(['year', 'x_Temporary_Larval_Habitat'])['PfPR'].mean().reset_index(name='PfPR') #'month'
    plot_output(sim_pfpr_agg, dhs_pfpr_df, scores, 'x_Temporary_Larval_Habitat')
