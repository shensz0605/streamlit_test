import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

#from pyecharts import options as opts
#from pyecharts.charts import Page,Grid,Geo,Bar,Line,Scatter,Tab,Timeline
#from pyecharts.globals import ChartType, SymbolType

#from pyecharts.components import Table
#from pyecharts.options import ComponentTitleOpts

st.title('实收日报')

########################
#I.load data
########################
df=pd.read_csv('./adm_loan_model.amx_daily_case_sum.csv')

########################
#II.数据处理
########################
dt_max0=df['dt'].max()
dt_max=(pd.to_datetime(dt_max0)-pd.DateOffset(days=1)).strftime('%Y-%m-%d')

mth_max=dt_max[0:7].replace('-','')

day_max0=int(dt_max0[7:10].replace('-',''))
day_max=int(dt_max[7:10].replace('-',''))

df=df[df['dt']<=dt_max].reset_index(drop=True)

##名字处理
df['disposer_name']=df['disposer_name'].apply(lambda x:x.replace('AMD_','').replace('A-','').replace('-WW','').replace('-ww','').replace('_WW','').\
                                              replace('_XH','').replace('-XH','').replace('有限公司','').replace('企业管理咨询','').replace('信用管理','').replace('C-',''))

df.loc[df['disposer_name']=='柳暗花明集团','disposer_name']='惠今'
df.loc[df['disposer_name']=='汉法通-杭州汉资-出售','disposer_name']='汉法通-出售'
df.loc[df['disposer_name']=='汉法通-杭州汉资-合肥方飞','disposer_name']='汉法通-委托'

##法诉标签
df['法诉']=0
df['调解']=0

df.loc[df['disposer_name'].str.contains('法院|汉法通|法溯|法诉|玄武|邯郸|乌市米东|乌市|黑龙江|弋阳|桂林_佤仟|桓仁鑫德|信博维诺攸米|焦作-河南浩兴|湖北远安')==True,'法诉']=1
df.loc[df['disposer_name'].str.contains('调解|诉调|掌讯通|言诺')==True,'调解']=1


##汇总
df['mth']=df['dt'].apply(lambda x:x[0:7].replace('-',''))
df['day']=df['dt'].apply(lambda x:int(x[8:10]))
mth_list=list(df['mth'].unique())

exl_asset=['FENGHUANG','DIANRONG_AUTO','QBYD','正钇资产包','平安普惠','空闲机构','停催']
asset_list=[i for i in list(df['asset_name'].unique()) if i not in exl_asset]

df_sum_level_1=df[(df['法诉']!=1) & (df['asset_name'].isin(asset_list))].groupby(['asset_name','mth','dt','day']).agg({'n_case':'sum','assign_amt_principal':'sum','repaid_amt':'sum'}).reset_index(drop=False)
df_sum_level_1['repaid_amt_cum']=df_sum_level_1.groupby(['asset_name','mth'])['repaid_amt'].cumsum()
df_sum_level_1['repaid_pct_cum']=100*df_sum_level_1['repaid_amt_cum']/df_sum_level_1['assign_amt_principal']
df_sum_level_1['dt_2']=df_sum_level_1['dt'].apply(lambda x:pd.to_datetime(x).date())

df_sum_level_2=df[df['法诉']!=1].groupby(['asset_name','mth','disposer_name','dt','day']).agg({'n_case':'sum','assign_amt_principal':'sum','repaid_amt':'sum'}).reset_index(drop=False)
df_sum_level_2['repaid_amt_cum']=df_sum_level_2.groupby(['asset_name','mth','disposer_name'])['repaid_amt'].cumsum()
df_sum_level_2['repaid_pct_cum']=100*df_sum_level_2['repaid_amt_cum']/df_sum_level_2['assign_amt_principal']
df_sum_level_2['dt_2']=df_sum_level_2['dt'].apply(lambda x:pd.to_datetime(x).date())
df_sum_level_2['n_case_max']=df_sum_level_2.groupby(['mth','disposer_name'])['n_case'].transform('max')

df_sum_level_1b=df_sum_level_1.pivot_table(index=['asset_name','day'],columns='mth',values=['n_case','assign_amt_principal','repaid_amt_cum','repaid_pct_cum']).reset_index('day',drop=False)
df_sum_level_2b=df_sum_level_2.pivot_table(index=['asset_name','disposer_name','day'],columns='mth',values=['n_case','assign_amt_principal','repaid_amt','repaid_amt_cum','repaid_pct_cum']).reset_index(['day'],drop=False)

########################
#III.输出
########################

st.markdown("""
#### 总体回收
""")

##当月累计回收
sum_1=df_sum_level_1b.loc[(df_sum_level_1b['day']==day_max),][['day','repaid_amt_cum','repaid_pct_cum']]

st.dataframe(sum_1)

##sidebar
asset_selected=st.sidebar.selectbox('选择资产', asset_list)

##制定资产回款情况
st.subheader(asset_selected)

###累计回款率
tmp1=df_sum_level_1[df_sum_level_1['asset_name']==asset_selected]
fig1 = px.line(tmp1, x = 'day', y = 'repaid_pct_cum',color="mth")

st.plotly_chart(fig1)

###daily 回款 by agency 
tmp2=df_sum_level_2[df_sum_level_2['asset_name']==asset_selected].sort_values(['mth','n_case_max','day'],ascending=[True,False,True])
list_disposer=[i for i in tmp2[(tmp2['day']==1) & (tmp2['n_case']>=200)].sort_values('n_case',ascending=False)['disposer_name'].unique() if i not in ['停催','空闲机构']]

fig2 = px.bar(tmp2[tmp2['disposer_name'].isin(list_disposer)], x = 'dt', y = 'repaid_amt',color="disposer_name")

st.plotly_chart(fig2)

###当月累计回款by 机构
tmp2_b=df_sum_level_2[(df_sum_level_2['asset_name']==asset_selected) & (df_sum_level_2['mth']==mth_max)].sort_values(['n_case_max','day'],ascending=[False,True])
list_disposer_b=[i for i in tmp2_b[(tmp2_b['day']==1) & (tmp2_b['n_case']>=200)].sort_values('n_case',ascending=False)['disposer_name'].unique() if i not in ['停催','空闲机构']]

fig2_b = px.line(tmp2_b[tmp2_b['disposer_name'].isin(list_disposer_b)], x = 'dt', y = 'repaid_pct_cum',color="disposer_name")

st.plotly_chart(fig2_b)

###多月累计回款- 制定机构
agency_selected=st.sidebar.selectbox('选择机构', list_disposer)

tmp3=tmp2[tmp2['disposer_name']==agency_selected].sort_values(['mth','day'])

#st.dataframe(tmp3)
fig3 = px.line(tmp3, x = 'day', y = 'repaid_pct_cum',color="mth")
st.subheader(agency_selected+"_累计回款率")
st.plotly_chart(fig3)