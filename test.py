import pandas as pd
import numpy as np
from vega_datasets import data
import altair as alt
import panel as pn
import datetime as dt
import holoviews as hv
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('.'))
jinja_template = env.get_template('template.html')

county_data = pd.read_csv('covid_confirmed_usafacts_new.csv')
state_data = county_data.groupby(['State','stateFIPS']).sum()
state_data = pd.DataFrame(state_data.to_records())
state_data_long = pd.melt(state_data.drop(['countyFIPS'],axis=1), id_vars=['State','stateFIPS'],var_name='Date',value_name='numberOfConfirmed')
source = alt.topo_feature(data.world_110m.url, 'countries')
counties = alt.topo_feature(data.us_10m.url, feature='counties')
states_data = alt.topo_feature(data.us_10m.url, feature='states')
alt.renderers.enable('mimetype')
pn.extension('vega')

state_list = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", 
                 "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                 "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                 "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                 "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
scale_list = ["linear","log"]
states = pn.widgets.Select(options=state_list, name='Select state',value="NY")

scales = pn.widgets.ToggleGroup(options=scale_list, name='Select scale',behavior='radio',value="linear")

date_slider_state = pn.widgets.DateSlider(name='Date', start=dt.datetime(2020, 3, 3), end=dt.datetime(2020, 4, 17), value=dt.datetime(2020, 4, 17))

date_slider_country = pn.widgets.DateSlider(name='Date', start=dt.datetime(2020, 3, 3), end=dt.datetime(2020, 4, 17), value=dt.datetime(2020, 4, 17))


altair_logo = 'https://altair-viz.github.io/_static/altair-logo-light.png'

covid_logo = 'https://wslmradio.com/wp-content/uploads/2020/03/banner.png'

# states map
@pn.depends(states.param.value, date_slider_state.param.value)
def get_state_map(states, date_slider_state):
  state_dict = {"AL":1, "AK":2, "AZ":4, "AR":5, "CA":6, "CO":8, "CT":9, "DE":10, "DC":11, "FL":12, "GA":13, 
                 "HI":15, "ID":16, "IL":17, "IN":18, "IA":19, "KS":20, "KY":21, "LA":22, "ME":23, "MD":24, 
                 "MA":25, "MI":26, "MN":27, "MS":28, "MO":29, "MT":30, "NE":31, "NV":32, "NH":33, "NJ":34, 
                 "NM":35, "NY":36, "NC":37, "ND":38, "OH":39, "OK":40, "OR":41, "PA":42, "RI":44, "SC":45, 
                 "SD":46, "TN":47, "TX":48, "UT":49, "VT":50, "VA":51, "WA":53, "WV":54, "WI":55, "WY":56}
  state = state_dict[states]
  date = date_slider_state.strftime('%-m/%-d/%y')
  a = alt.Chart(counties).mark_geoshape(
    stroke='black'
  ).transform_calculate(
    state_id = "(datum.id / 1000)|0"
  ).transform_filter(
    (alt.datum.state_id)==state
  ).transform_lookup(
    lookup='id',
    from_=alt.LookupData(county_data, 'countyFIPS', [date,'County Name'])
  ).encode(
    color = alt.Color(date +":Q",title='Cases',scale=alt.Scale(type='threshold',domain=[20,100,500,1000,5000],scheme='orangered',zero=True)),
    tooltip=[alt.Tooltip('County Name:N', title='County'),alt.Tooltip(date+":Q", title='Number of cases')]
  ).properties(
    width=600, 
    height=450
  ).project(
    type='albersUsa'
  )
  return a.configure_view(
    stroke=None
  )

@pn.depends(date_slider_country.param.value)
def get_country_bar(date_slider_country):
  date = date_slider_country.strftime('%-m/%-d/%y')
  return alt.Chart(state_data).mark_bar().encode(
      x=alt.X('State',sort='-y'),
      y=alt.Y(date+':Q',title='Number of Confirmed')
  )

@pn.depends(date_slider_country.param.value)
def get_country_table(date_slider_country):
  date = date_slider_country.strftime('%-m/%-d/%y')
  state_table = state_data[['State',date]].sort_values(by=date, ascending=False).reset_index(drop=True)[:10]
  state_table.index = state_table.index + 1
  td_props = [
    ('font-size', '18px')
  ]
  styles = [
    dict(selector="th", props=td_props),
    dict(selector="td", props=td_props)
  ]

  # state_table = state_table.style.set_table_styles(styles)

  return state_table

@pn.depends(states.param.value, scales.param.value, date_slider_state.param.value)
def get_state_line(states, scales, date_slider_state):
  date = date_slider_state.strftime('%-m/%-d/%y')
  state_data_long['rule'] = date
  state_data_long['num'] = int(state_data.loc[state_data['State'] == states,date])

  # print(date)
  base = alt.Chart(
    state_data_long
  ).transform_filter(
      (alt.datum.State == states)
  ).transform_filter(
      alt.datum.numberOfConfirmed > 0
  )

  line = base.mark_line().encode(
    alt.X('Date:T',title="Date"),
    alt.Y('numberOfConfirmed:Q', scale=alt.Scale(type=scales), title="Number of Confirmed Cases")
  )

  dots = base.mark_point(
    filled=True,
    size = 100,
    color = 'black'
  ).encode(
      x = 'rule:T',
      y = 'num:Q',
      tooltip=[alt.Tooltip('num:Q', title='Number of Cases'),alt.Tooltip("rule:T", title='Date')]
  )

  rule = base.mark_rule(
    size=4, 
    color="lightgray"
  ).encode(
    x = 'rule:T'
  )

  return (rule+line+dots).properties(
    height=350,
    width=350
  ).configure_axis(
    titleFontSize=16
  )

# US map
@pn.depends(date_slider_country.param.value)
def get_country_map(date_slider_country):
  date = date_slider_country.strftime('%-m/%-d/%y')
  return alt.Chart(states_data).mark_geoshape(
    stroke='black'
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(state_data, 'stateFIPS', [date,'State'])
    ).encode(
        color = alt.Color(date+":Q",title='Cases',scale=alt.Scale(type='threshold',domain=[200,1000,5000,10000,50000],scheme='orangered')),
        tooltip=[alt.Tooltip('State:N', title='State'),alt.Tooltip(date+':Q', title='Number of cases')]
    ).properties(
        width=600, 
        height=450
    ).project(
        type='albersUsa'
    ).configure_view(stroke=None)

# Customize webpage

tmpl = pn.Template(jinja_template)

tmpl.add_variable('app_title', '<h1>COVID-19 in U.S. States</h1>')


# pn.Row(
#     pn.Column('# Covid-19 in US states', pn.panel(altair_logo, height=150), states, date_slider),
#     get_map
# ).servable()

state_map = pn.Row(
    pn.Column('# Covid-19 for each state in the U.S.', pn.panel(covid_logo, height=150), states, date_slider_state),
    pn.Column(get_state_map, width=700),
    pn.Column(get_state_line,pn.Spacer(height=60),scales),

    # pn.Tabs(
    #   ('Map', get_state_map),
    #   ('Line Chart', pn.Column(get_state_line, scales))
    # )
)

# state_line = pn.Column(
#     get_state_line,
#     scales
# )




us_map = pn.Row(
    pn.Column('# Covid-19 in the U.S.',pn.panel(covid_logo, height=150), date_slider_country),
    pn.Column(get_country_map,width=700),
    pn.Column(get_country_table)
    # pn.Tabs(
    #   ('Map', get_country_map),
    #   ('Bar Chart', get_country_bar),
    #   ('10 states with the most COVID-19 cases', get_country_table)
    # )
)

# A.save('index.html', embed=True, max_states=2000, max_opts=2000)

# tmpl.add_panel('A', pn.Column('# Covid-19 in US states', pn.panel(altair_logo, height=150), states, date_slider))
# tmpl.add_panel('B', get_map)
tmpl.add_panel('A', us_map)
tmpl.add_panel('B', state_map)
# tmpl.add_panel('C', state_line)

# tmpl.save('index.html', embed=True)
tmpl.servable()
# Run "panel serve --show test.py" to start a local server and view it in your browser
