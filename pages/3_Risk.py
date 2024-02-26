import streamlit as st
import matplotlib.pyplot as plt

from streamlit_app import sidebar, OBSERVATION_COLUMNS, ASSET_COLUMNS

import random
print(f'Risk {random.randint(0,99)}')

# the top X assets with the asset name and the deforestation in the 
# 3-year time window --> list of the assets associated with the most deforestation

with st.expander('Assets associated with the most deforestation...'):

    class Period:
        AROUND3="Around 3 Years"
        AROUND5="Around 5 Years"
        PREVIOUS3="Previous 3 Years"
        NEXT3="Next 3 Years"

    PERIODS = [Period.AROUND3, Period.AROUND5, Period.PREVIOUS3, Period.NEXT3]
    period = st.radio(
        "Select a period...",
        PERIODS,
        index=PERIODS.index(Period.AROUND3),
        horizontal=True)

    match period:
        case Period.AROUND3:
            sort_column = 'around_3'
            period_columns = [sort_column]
        case Period.AROUND5:
            sort_column = 'around_5'
            period_columns = [sort_column]
        case Period.PREVIOUS3:
            sort_column = 'past_3'
            period_columns = [sort_column]
        case Period.NEXT3:
            sort_column = 'forward_3'
            period_columns = [sort_column]

    assets_for_chosen_period = st.session_state.observation_data[ASSET_COLUMNS + period_columns]

    block = st.slider("Select a block...", 
        0, len(assets_for_chosen_period), (0, 50), step=10)

    assets_for_chosen_period.sort_values(by=sort_column, ascending=False, inplace=True)
    topX = assets_for_chosen_period.iloc[block[0]:block[1],:]

    col1, col2=st.columns([0.7, 0.3])
    with col1:
        st.write(topX)
    with col2:

        columns=['country', 'sector_main']
        columns.sort()
        column = st.radio(
            "Select a column...",
            columns,
            index=0)

        value_counts = topX[column].value_counts()

        fig1, ax1 = plt.subplots()
        values=[value for value in value_counts[value_counts.index]]
        labels=value_counts.index.to_list()
        ax1.pie(values, 
                labels=labels, 
                autopct='%1.1f%%',
                shadow=True, 
                startangle=180
                )
        #plt.legend(labels, loc="center")
        ax1.axis('equal')
        st.pyplot(fig1)

sidebar()