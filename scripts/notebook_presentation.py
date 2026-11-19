"""Bounded aggregate tables for the main Cox notebooks."""
import pandas as pd


def estimates_table(result,key):
    frame=pd.DataFrame.from_dict(result['models'][key]['estimates'],orient='index')
    frame.index.name='Covariate'
    return frame.rename(columns={'hr':'HR','lower_95':'95% CI lower','upper_95':'95% CI upper','p':'p'}).style.format(
        {'HR':'{:.3f}','95% CI lower':'{:.3f}','95% CI upper':'{:.3f}','p':'{:.4g}'})


def raas_models_table(result,keys):
    rows=[]
    for key in keys:
        m=result['models'][key];e=m['estimates']['raas_pre_icu']
        rows.append({'Model':key,'Admissions':m['n'],'Deaths':m['deaths'],'HR':e['hr'],
                     '95% CI lower':e['lower_95'],'95% CI upper':e['upper_95'],'p':e['p']})
    return pd.DataFrame(rows).style.format({'HR':'{:.3f}','95% CI lower':'{:.3f}','95% CI upper':'{:.3f}','p':'{:.4g}'})


def ph_table(result,keys):
    return pd.DataFrame([{'Model':key,'Covariate':term,'Rank PH p':value}
                         for key in keys for term,value in result['models'][key]['ph_rank_p'].items()]).style.format({'Rank PH p':'{:.4g}'})
