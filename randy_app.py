import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import requests, os
from gwpy.timeseries import TimeSeries
from gwosc.locate import get_urls
from gwosc import datasets

from copy import deepcopy

# -- Default detector list
detectorlist = ['H1','L1', 'V1']

# Title the app
st.title('Gravitational Wave Quickview App')

st.markdown("""
 * Use the controls at left to select data
 * Learn more at https://gw-openscience.org
""")

@st.cache   #-- Magic command to cache data
def load_gw(t0, detector):
    strain = TimeSeries.fetch_open_data(detector, t0-16, t0+16, cache=False)
    return strain

st.sidebar.markdown("## Select Data Time and Detector")

# -- Get list of events
# find_datasets(catalog='GWTC-1-confident',type='events')
eventlist = datasets.find_datasets(type='events')
eventlist = [name.split('-')[0] for name in eventlist if name[0:2] == 'GW']
eventset = set([name for name in eventlist])
eventlist = list(eventset)
eventlist.sort()

#-- Set time by GPS or event
select_event = st.sidebar.selectbox('How do you want to find data?',
                                    ['By event name', 'By GPS'])

if select_event == 'By GPS':
    # -- Set a GPS time:        
    str_t0 = st.sidebar.text_input('GPS Time', '1126259462.4')    # -- GW150914
    t0 = float(str_t0)

    st.sidebar.markdown("""
    Example times in the H1 detector:
    * 1126259462.4    (GW150914) 
    * 1187008882.4    (GW170817) 
    * 933200215       (hardware injection)
    * 1132401286.33   (Koi Fish Glitch) 
    """)

else:
    chosen_event = st.sidebar.selectbox('Select Event', eventlist)
    t0 = datasets.event_gps(chosen_event)
    detectorlist = list(datasets.event_detectors(chosen_event))
    
    
#-- Choose detector as H1, L1, or V1
detector = st.sidebar.selectbox('Detector', detectorlist)

st.sidebar.markdown('## Q-Transform Controls')
dtboth = st.sidebar.slider('Time Range (seconds)', 0.1, 8.0, 1.0)  # min, max, default
dt = dtboth / 2.0
vmax = st.sidebar.slider('Colorbar Max Energy', 10, 500, 25)  # min, max, default

qcenter = st.sidebar.slider('Q-value', 5, 120, 5)  # min, max, default
qrange = (int(qcenter*0.8), int(qcenter*1.2))




# Create a text element and let the reader know the data is loading.
strain_load_state = st.text('Loading data...this may take a minute')
try:
    strain = load_gw(t0, detector)
except:
    st.text('Data load failed.  Try a different time and detector pair.')
    st.text('Problems can be reported to gwosc@igwn.org')
    raise st.ScriptRunner.StopException
    
strain_load_state.text('Loading data...done!')

cropstart = t0-0.2
cropend   = t0+0.1


#-- Make a time series plot
st.subheader('Raw data')

@st.cache()
def tsplot(t0, strain, cropstart, cropend):

    center = int(t0)
    strain_ = deepcopy(strain).crop(croptstart, cropend) #Q: deepcopy used here, because I assume that mutation across graphs isn't the intent. Is that correct?
    tsplot_plt = strain_.plot()
    return(tsplot_plt)

st.pyplot(tsplot(t0, strain, cropstart, cropend), clear_figure=True)




# -- Try whitened and band-passed plot
# -- Whiten and bandpass data
st.subheader('Whitened and Bandpassed Data')

@st.cache()
def whitenplot(t0, strain):
    white_data = deepcopy(strain).whiten()  #Q: deepcopy used here, because I assume that mutation across graphs isn't the intent. Is that correct?
    bp_data = white_data.bandpass(30, 400)
    return bp_data.crop(cropstart, cropend)

whitenplot_plt = deepcopy(whitenplot(t0, strain)).plot()
st.pyplot(whitenplot_plt, clear_figure=True)




# -- Q-transform plot

st.subheader('Q-transform')

# -- Appears that this can't be cached, as deepcopy not possible due to TransformNode message, no frozen() method defined
def qtransform(t0, dt, qrange, vmax, strain):
    hq = deepcopy(strain).q_transform(outseg=(t0-dt, t0+dt), qrange=qrange) #Q: deepcopy used here, because I assume that mutation across graphs isn't the intent. Is that correct?
    fig4 = hq.plot()
    ax = fig4.gca()
    fig4.colorbar(label="Normalised energy", vmax=vmax, vmin=0)
    ax.grid(False)
    ax.set_yscale('log')
    ax.set_ylim(bottom=15)
    return fig4

qtransform_plt = qtransform(t0, dt, qrange, vmax, strain)
st.pyplot(qtransform_plt, clear_figure=True)



st.subheader("About this app")
st.markdown("""
This app displays data from LIGO, Virgo, and GEO downloaded from
the Gravitational Wave Open Science Center at https://gw-openscience.org .
""")
