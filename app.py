import streamlit as st
from datetime import datetime
from src.RealEstateAnalysis import RealEstateAnalysis

# Define the file paths to the rental and sales data CSVs
rental_filepath = "Data/HUD_Rental_Rate.csv"
sales_filepath = "Data/Zillow_SFH_Sales.csv"

# Create an instance of RealEstateAnalysis
real_estate_analysis = RealEstateAnalysis(rental_filepath, sales_filepath)

# Set up the Streamlit app layout
st.title('Rental Property Finder')

# Configure the sidebar for input parameters
st.sidebar.header('Your Rental Property Search Criteria')
min_price = st.sidebar.number_input('Minimum Property Value', min_value=0, value=50000, step=10000)
population = st.sidebar.number_input('Minimum Population', min_value=0, value=500000, step=50000)
min_roi = st.sidebar.number_input('Minimum Target ROI', min_value=0.0, max_value=1.0, value=0.10, step=0.01)
#period = st.sidebar.date_input('Period of Interest', datetime(2023, 11, 30))
period = datetime(2023, 11, 30)

# Get the list of State from the data and use it for the select box
state_options = real_estate_analysis.df_sales_long['State'].dropna().unique().tolist()
state_area = st.sidebar.selectbox('Select a State', state_options)

# Get the list of metro areas from the data and use it for the select box
metro_area_options_df = real_estate_analysis.df_sales_long[real_estate_analysis.df_sales_long['State'] == state_area].copy()
metro_area_options = metro_area_options_df['Metro'].dropna().unique().tolist()
metro_area = st.sidebar.selectbox('Select a Metro Area', metro_area_options)

# Get list of FIPS_Code_list for metro area and county options
FIPS_Code_options_df = metro_area_options_df[metro_area_options_df['Metro'] == metro_area].copy()
FIPS_Code_list = FIPS_Code_options_df['FIPS_Code'].dropna().unique().tolist()

county_options_df = real_estate_analysis.df_rental_long
county_options = county_options_df[county_options_df['FIPS_Code'].isin(FIPS_Code_list)]['County Name'].dropna().unique().tolist()

# Tabs on the main page
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Historical Values", 
                                        "Rental Summary", 
                                        "County Populations", 
                                        "Foreclosure & RentalListings", 
                                        "High ROI Rental Markerts"])

# Historical property values by region
with tab1:
    st.header(f'Historical Property Values for {metro_area}')
    fig = real_estate_analysis.plot_time_series_value_by_region(metro_area)
    if fig:
        st.pyplot(fig)
    else:
        st.error('Error generating plot. Please check the selected Metro area.')

# Rental summary
with tab2:
    st.header('Rental Summary')
    rental_summary_fig = real_estate_analysis.plot_rental_summary(FIPS_Code_list, dpi=300)
    st.pyplot(rental_summary_fig)

# County populations
with tab3:
    st.header('County Populations')
    population_fig = real_estate_analysis.plot_county_population(FIPS_Code_list)
    st.pyplot(population_fig)

# Generate and display listing URLs
with tab4:
    county_input = st.selectbox('Select a County Area', county_options)
    if st.button('Generate URLs'):
        if county_input and state_area:
            listing_urls = real_estate_analysis.generate_listing_urls(county_input, state_area)
            foreclosure_url = listing_urls['foreclosure_url']
            rental_url = listing_urls['rental_url']
            st.markdown(f"Foreclosure Listings: {foreclosure_url}", unsafe_allow_html=True)
            st.markdown(f"Rental Listings: {rental_url}", unsafe_allow_html=True)
        else:
            st.warning('Please select a county name.')

# Foreclosure listings
with tab5:
    st.header('Foreclosure Properties')
    foreclosure_properties = real_estate_analysis.foreclosure_rental_listings(
        period.strftime('%Y-%m-%d'), 
        min_price, 
        population, 
        min_roi
    )
    st.markdown(foreclosure_properties.to_html(escape=False, index=False), unsafe_allow_html=True)


# Footer or any additional information
st.markdown("## Data Analysis Completed")
st.markdown("**Thank You for using the Rental Property Finder!**")