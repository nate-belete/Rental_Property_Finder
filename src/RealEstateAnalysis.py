import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

class RealEstateAnalysis:
    def __init__(self, rental_filepath, sales_filepath):
        self.df_rental, self.df_sales = self.load_csv_data(rental_filepath, sales_filepath)
        self.merged_df, self.df_rental_long, self.df_sales_long = self.prepare_data(self.df_rental, self.df_sales)

    @staticmethod
    def load_csv_data(rental_filepath, sales_filepath):
        df_rental = pd.read_csv(rental_filepath)
        df_sales = pd.read_csv(sales_filepath)
        return df_rental, df_sales

    @staticmethod
    def melt_dataframe(df, id_vars, value_vars, var_name, value_name):
        return pd.melt(df, id_vars=id_vars, value_vars=value_vars,
                       var_name=var_name, value_name=value_name)

    def prepare_data(self, df_rental, df_sales):
        date_columns = [col for col in df_sales.columns if '/' in col]
        df_sales_long = self.melt_dataframe(
            df_sales,
            id_vars=[
                'RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName',
                'State', 'Metro', 'StateCodeFIPS', 'MunicipalCodeFIPS'
            ],
            value_vars=date_columns,
            var_name='Date',
            value_name='Value'
        )
        df_sales_long['Date'] = pd.to_datetime(df_sales_long['Date'], errors='coerce')

        bedroom_columns = [col for col in df_rental.columns if col.startswith('Bedroom_')]
        df_rental_long = self.melt_dataframe(
            df_rental,
            id_vars=[
                'State Postal Code', '2 Digit State FIPS Code', 'HUD Specific Area Code',
                'County Name', 'MSA', 'HUD_Area_Name', 'FIPS_Code', 'Population in 2020'
            ],
            value_vars=bedroom_columns,
            var_name='Bedroom_Type',
            value_name='Rent'
        )
        df_rental_long['Bedroom_Count'] = df_rental_long['Bedroom_Type'].str.extract('(\d+)', expand=False).astype(int)
        
        df_sales_long['MunicipalCodeFIPS'] = df_sales_long['MunicipalCodeFIPS'].astype(str).str.zfill(3)
        df_sales_long['FIPS_Code'] = df_sales_long['StateCodeFIPS'].astype(str) + df_sales_long['MunicipalCodeFIPS'] + '99999'
        df_rental_long['FIPS_Code'] = df_rental_long['FIPS_Code'].astype(str)

        merged_df = df_rental_long.merge(df_sales_long, on='FIPS_Code', how='left')
        merged_df.dropna(inplace=True)

        return merged_df, df_rental_long, df_sales_long

    def plot_time_series_value_by_region(self, metro_area: str = ''):
        df = self.df_sales_long.copy()  # Use copy to avoid SettingWithCopyWarning
        df['Date'] = pd.to_datetime(df['Date'])
        df.sort_values('Date', inplace=True)
        
        if metro_area:
            df = df[df['Metro'] == metro_area]
            if df.empty:
                print(f"No data found for Metro area: {metro_area}")
                return None, []

        def dollars(x, pos):
            return f'${x:,.0f}'

        dollar_formatter = FuncFormatter(dollars)
        sns.set_style('whitegrid')
        fig, ax = plt.subplots(figsize=(16, 6))

        sns.lineplot(data=df, x='Date', y='Value', hue='RegionName', ax=ax)
        ax.set_title(f"Time Series of Real Estate Value Index by Region {'in Metro area: ' + metro_area if metro_area else ''}")
        ax.set_xlabel('Date')
        ax.set_ylabel('Real Estate Value Index')
        ax.yaxis.set_major_formatter(dollar_formatter)
        plt.xticks(rotation=45)
        ax.legend(title='RegionName', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        return fig

    def plot_rental_summary(self, FIPS_Code_list, figsize: tuple = (12, 5), dpi: int = 96):

        df = self.df_rental_long.copy()  # Use copy to avoid SettingWithCopyWarning

        if FIPS_Code_list:
            df = df[df['FIPS_Code'].isin(FIPS_Code_list)]
            if df.empty:
                print(f"No data found for the area")
                return None, []

        summary = df.groupby(['Bedroom_Type', 'County Name'], as_index=False)['Rent'].mean()
        sns.set_style('whitegrid')
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        sns.barplot(data=summary, x='Bedroom_Type', y='Rent', hue='County Name', ax=ax)
        ax.set_ylabel('Average Rent')
        ax.set_xlabel('Bedroom Type')
        ax.set_title('Average Rent by County Across Bedroom Types')
        plt.xticks(rotation=45)
        ax.legend(title='County Name', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        return fig


    def plot_county_population(self, FIPS_Code_list, figsize: tuple = (12, 5)):
        """
        Plot population for each county as a horizontal bar chart using a seaborn barplot.

        :param figsize: A tuple to set figure size. The default is (12, 5).
        :return: Matplotlib figure object
        """
        df = self.df_rental_long.copy()  # Use copy to avoid SettingWithCopyWarning

        if FIPS_Code_list:
            df = df[df['FIPS_Code'].isin(FIPS_Code_list)]
            if df.empty:
                print(f"No data found for the area")
                return None, []

        # Extract unique combinations of 'County Name' and 'Population in 2020', and round the population values
        county_population = df[['County Name', 'Population in 2020']].drop_duplicates()
        county_population['Population in 2020'] = county_population['Population in 2020'].round(0)

        # Sort the DataFrame by 'Population in 2020' to display bars in a meaningful order
        county_population_sorted = county_population.sort_values('Population in 2020', ascending=False)

        # Set the aesthetic style of the plots
        sns.set(style="whitegrid")

        # Initialize matplotlib figure and axes
        fig, ax = plt.subplots(figsize=figsize)

        # Use seaborn to create a horizontal bar plot on the provided axes object
        sns.barplot(
            x='Population in 2020', 
            y='County Name', 
            data=county_population_sorted, 
            palette='coolwarm',  # Color palette for visual appeal
            ax=ax
        )

        # Format the x-axis values to represent populations without decimal places (rounded integers)
        formatter = FuncFormatter(lambda x, _: f'{x:,.0f}')
        ax.xaxis.set_major_formatter(formatter)

        # Label the axes and the plot
        ax.set_xlabel('Population in 2020')
        ax.set_ylabel('County Name')
        ax.set_title('Population by County in 2020')

        # Adjust the layout to make sure everything fits into the figure area
        plt.tight_layout()

        # Return the figure object
        return fig


    def foreclosure_rental_listings(self, period, min_price, population, min_roi):
        """
        Filters properties based on specified criteria and calculates relevant metrics,
        then adds URLs for foreclosure and rental listings.

        :param period: Date string for the period of interest (YYYY-MM-DD)
        :param min_price: Minimum property value to consider
        :param population: Minimum population count to consider
        :param min_roi: Minimum rental return on investment (ROI) to consider
        :return: DataFrame with filtered data, calculated ROI, and generated URLs
        """
        # Prepare and filter data
        self.merged_df['Value'] = self.merged_df['Value'].round(0)
        self.merged_df['Rental_ROI'] = self.merged_df['Rent'] * 12 / self.merged_df['Value']
        filtered_df = (self.merged_df[
            (self.merged_df['Date'] == period) &
            (self.merged_df['Value'] >= min_price) &
            (self.merged_df['Population in 2020'] >= population) &
            (self.merged_df['Rental_ROI'] >= min_roi)]
        ).copy()

        # Aggregate data by key columns using groupby, calculate mean values
        key_columns = ['Metro', 'County Name', 
                    'State Postal Code', 'FIPS_Code',
                       'Population in 2020', 'Rent', 'Value', 'Rental_ROI']
        grouped_df = filtered_df[key_columns].groupby(key_columns[:4]).mean().reset_index()

        # Sort properties by ROI in descending order
        grouped_df.sort_values('Rental_ROI', ascending=False, inplace=True)

        # Generate clickable URL strings with HTML anchor tags
        grouped_df['Foreclosures_urls'] = grouped_df.apply(
            lambda row: f'<a target="_blank" href="https://mls.foreclosure.com/listing/search.html?q={row["County Name"].replace(" ", "%20")}%20county,%20{row["State Postal Code"]}">Foreclosures</a>', 
            axis=1
        )
        grouped_df['Rental_urls'] = grouped_df.apply(
            lambda row: f'<a target="_blank" href="https://www.apartments.com/houses/{row["County Name"].replace(" ", "-").lower()}-{row["State Postal Code"].lower()}/">Rentals</a>', 
            axis=1
        )

        # Reset index for clean output
        grouped_df.reset_index(drop=True, inplace=True)

        # Format 'Population in 2020' with commas
        grouped_df['Population in 2020'] = grouped_df['Population in 2020'].round(0).apply(lambda x: f"{x:,.0f}")
        # Format 'Average Rent' with commas and a dollar sign
        grouped_df['Average Rent'] = grouped_df['Rent'].round(0).apply(lambda x: f"${x:,.0f}")
        # Format 'Average Property Value' with commas and a dollar sign
        grouped_df['Average Property Value'] = grouped_df['Value'].round(0).apply(lambda x: f"${x:,.0f}")
        # Format 'Expected Annual ROI' as a percentage
        grouped_df['Expected Annual ROI'] = (grouped_df['Rental_ROI'] * 100).apply(lambda x: f"{x:.1f}%")


        return grouped_df[['Metro', 'County Name', 'Population in 2020', 'Average Rent',
                             'Average Property Value', 'Expected Annual ROI', 
                             'Foreclosures_urls', 'Rental_urls']]


    def generate_listing_urls(self, county_name, state_postal_code):
        """
        Generates clickable HTML links for foreclosure and rental listing URLs 
        based on the county name and state postal code.

        :param county_name: The name of the county
        :param state_postal_code: The postal code abbreviation of the state (e.g., 'CA' for California)
        :return: A dictionary containing the HTML anchor tags for the foreclosure 
                 and rental listing URLs
        """
        # Generate the clickable HTML link for the foreclosure listing
        foreclosure_url = f'<a target="_blank" href="https://mls.foreclosure.com/listing/search.html?q={county_name.replace(" ", "%20")}%20county,%20{state_postal_code}">Foreclosures</a>'
        
        # Generate the clickable HTML link for the rental listing
        rental_url = f'<a target="_blank" href="https://www.apartments.com/{county_name.replace(" ", "-").lower()}-{state_postal_code.lower()}/">Rentals</a>'

        # Return both URLs as HTML anchor tags in a dictionary format
        return {
            'foreclosure_url': foreclosure_url,
            'rental_url': rental_url
        }

# Other existing methods would remain unchanged