import numpy as np
import matplotlib.pyplot as plt
import iris
import iris.quickplot as qplt
import cartopy.feature as cfeature
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import shapely.geometry
import cartopy.crs as ccrs
import cartopy.feature as cf
from matplotlib.dates import ConciseDateConverter
import cftime
import matplotlib.units as munits
munits.registry[cftime.DatetimeGregorian] = ConciseDateConverter()
import datetime
from datetime import timedelta
from iris.coord_categorisation import add_categorised_coord
from iris.coord_categorisation import _pt_date
from iris.coord_categorisation import add_day_of_year
import pandas as pd
import xarray as xr
import iris.coords as icoords
import iris.cube as icube
# steps:

# create GB country mask
# load in the natural earth data we will use to make the mask
# make country average T2m
# make HDD and CDD
# apply demand model (weather-dependent)

# functions:

def country_mask(data_dir, test_str, COND,COUNTRY):

    dataset = iris.load(data_dir + test_str,COND)
    LONS,LATS = iris.analysis.cartography.get_xy_grids(dataset[0])
    print(np.shape(LONS))
    x,y = LONS.flatten(), LATS.flatten()
    points = np.vstack((x,y)).T

    MASK_MATRIX_TEMP = np.zeros((len(x),1))
    country_shapely=[]
    for country in shpreader.Reader(countries_shp).records():
        if country.attributes["NAME"][0:14] == COUNTRY:
            print('Found Country ' + COUNTRY)
            country_shapely.append(country.geometry)

    print('making mask')
    for i in range(0,len(x)):
        my_point = shapely.geometry.Point(x[i],y[i])
        if country_shapely[0].contains(my_point) == True:
            MASK_MATRIX_TEMP[i,0] = 1.0     

    MASK_MATRIX_RESHAPE = np.reshape(MASK_MATRIX_TEMP,(np.shape(LONS)))
    print(np.shape(MASK_MATRIX_RESHAPE))

    #fig = plt.figure(figsize=(5,5))
    #ax = fig.add_subplot(1,1,1,projection=ccrs.PlateCarree())
    #plt.pcolormesh(LONS,LATS,MASK_MATRIX_RESHAPE,cmap='YlGn',transform=ccrs.PlateCarree())
    #plt.title('Land Mask',fontsize=16)
    #ax.set_aspect('auto',adjustable=None)
    #ax.coastlines(resolution='50m')
    #ax.add_feature(cf.BORDERS)


    return MASK_MATRIX_RESHAPE

####
# calculate HDD and CDD timeseries.
#####
def HDD_function(temperature_timeseries):
#inputs:
#temperature_timeseries = 1D temperatures timeseries in degrees celcius

#Outputs:
#HDD_timeseries = same dimensions as temperature_timeseries.
    #print(temperature_timeseries)
    HDD_timeseries = temperature_timeseries.copy()
    HDD_timeseries.rename("HDD")

    interesting_points = temperature_timeseries.data <= 15.5
    HDD_timeseries.data[interesting_points] = 15.5 - temperature_timeseries.data[interesting_points]
    HDD_timeseries.data[~interesting_points] = 0.0
    
    return HDD_timeseries

def CDD_function(temperature_timeseries):
#inputs:
#temperature_timeseries = 1D temperatures timeseries in degrees celcius

#Outputs:
#CDD_timeseries = same dimensions as temperature_timeseries.
    CDD_timeseries = temperature_timeseries.copy()
    CDD_timeseries.rename("CDD")

    interesting_points = temperature_timeseries.data >= 22.0
    CDD_timeseries.data[interesting_points] =  temperature_timeseries.data[interesting_points] - 22.0
    CDD_timeseries.data[~interesting_points] = 0.0

    return CDD_timeseries



def get_regression_coefficients(COUNTRY_nospace,path_to_reg_coeff_file):
  
    coeffs = pd.read_csv(path_to_reg_coeff_file)
    title_string = COUNTRY_nospace + '_regression_coeffs_no_pop_weights.txt'
    coeffs_country = coeffs[title_string]
    return coeffs_country


def calc_demands(YEAR,MONTH,coeffs_country,GB_daily_HDD_ERA5,GB_daily_CDD_ERA5):

    if YEAR in [1940,1944,1948,1952,1956,1960,1964,1968,1972,1976,1980,1984,1988,1992,1996,2000,2004,2008,2012,2016,2020,2024,2028] and MONTH in ['02']:
        len_of_reanalysis_period = 29
    elif MONTH == '02':
        len_of_reanalysis_period = 28
    elif MONTH in ['09','04','06','11']:
        len_of_reanalysis_period = 30
    else:
        len_of_reanalysis_period = 31

    # find what day of the week we're starting on
    start_date = datetime.datetime(YEAR, 1, 1)
    starting_weekday = start_date.weekday()

    
    pred_WD1 = np.zeros([len_of_reanalysis_period]) #monday
    pred_WD2 = np.zeros([len_of_reanalysis_period]) #tuesday
    pred_WD3 = np.zeros([len_of_reanalysis_period]) #wednesday
    pred_WD4 = np.zeros([len_of_reanalysis_period]) #thursday
    pred_WD5 = np.zeros([len_of_reanalysis_period]) #friday
    pred_WK1 = np.zeros([len_of_reanalysis_period]) #saturday
    pred_WK2 = np.zeros([len_of_reanalysis_period]) #sunday

    if starting_weekday == 1:
        pred_WD2[::7] =1 # tuesday
        pred_WD3[1:len_of_reanalysis_period:7] =1
        pred_WD4[2:len_of_reanalysis_period:7] =1
        pred_WD5[3:len_of_reanalysis_period:7] =1
        pred_WK1[4:len_of_reanalysis_period:7] =1
        pred_WK2[5:len_of_reanalysis_period:7] =1
        pred_WD1[6:len_of_reanalysis_period:7] =1
    
    if starting_weekday == 0:
        pred_WD1[::7] =1 # monday
        pred_WD2[1:len_of_reanalysis_period:7] =1
        pred_WD3[2:len_of_reanalysis_period:7] =1
        pred_WD4[3:len_of_reanalysis_period:7] =1
        pred_WD5[4:len_of_reanalysis_period:7] =1
        pred_WK1[5:len_of_reanalysis_period:7] =1
        pred_WK2[6:len_of_reanalysis_period:7] =1
    
    if starting_weekday == 2:
        pred_WD3[::7] =1 # wednesday
        pred_WD4[1:len_of_reanalysis_period:7] =1
        pred_WD5[2:len_of_reanalysis_period:7] =1
        pred_WK1[3:len_of_reanalysis_period:7] =1
        pred_WK2[4:len_of_reanalysis_period:7] =1
        pred_WD1[5:len_of_reanalysis_period:7] =1
        pred_WD2[6:len_of_reanalysis_period:7] =1
    
    if starting_weekday == 3:
        pred_WD4[::7] =1 # thursday
        pred_WD5[1:len_of_reanalysis_period:7] =1
        pred_WK1[2:len_of_reanalysis_period:7] =1
        pred_WK2[3:len_of_reanalysis_period:7] =1
        pred_WD1[4:len_of_reanalysis_period:7] =1
        pred_WD2[5:len_of_reanalysis_period:7] =1
        pred_WD3[6:len_of_reanalysis_period:7] =1
    
    if starting_weekday == 4:
        pred_WD5[::7] =1 # friday
        pred_WK1[1:len_of_reanalysis_period:7] =1
        pred_WK2[2:len_of_reanalysis_period:7] =1
        pred_WD1[3:len_of_reanalysis_period:7] =1
        pred_WD2[4:len_of_reanalysis_period:7] =1
        pred_WD3[5:len_of_reanalysis_period:7] =1
        pred_WD4[6:len_of_reanalysis_period:7] =1
        
    if starting_weekday == 5:
        pred_WK1[::7] =1 # saturday
        pred_WK2[1:len_of_reanalysis_period:7] =1
        pred_WD1[2:len_of_reanalysis_period:7] =1
        pred_WD2[3:len_of_reanalysis_period:7] =1
        pred_WD3[4:len_of_reanalysis_period:7] =1
        pred_WD4[5:len_of_reanalysis_period:7] =1
        pred_WD5[6:len_of_reanalysis_period:7] =1
     
    if starting_weekday == 6:
        pred_WK2[::7] =1 # sunday
        pred_WD1[1:len_of_reanalysis_period:7] =1
        pred_WD2[2:len_of_reanalysis_period:7] =1
        pred_WD3[3:len_of_reanalysis_period:7] =1
        pred_WD4[4:len_of_reanalysis_period:7] =1
        pred_WD5[5:len_of_reanalysis_period:7] =1
        pred_WK1[6:len_of_reanalysis_period:7] =1


    # fix demand levels at 2021
    weather_dep_demand = coeffs_country[0]*2021 + coeffs_country[8]*GB_daily_HDD_ERA5 + coeffs_country[9]*GB_daily_CDD_ERA5
    full_demand = coeffs_country[0]*2021 + coeffs_country[8]*GB_daily_HDD_ERA5 + coeffs_country[9]*GB_daily_CDD_ERA5 + coeffs_country[1]*pred_WD1 + coeffs_country[2]*pred_WD2 + coeffs_country[3]*pred_WD3 + coeffs_country[4]*pred_WD4 + coeffs_country[5]*pred_WD5 + coeffs_country[6]*pred_WK1 + coeffs_country[7]*pred_WK2


    return weather_dep_demand, full_demand
    

print('loading ERA5 one year at a time to create demand and other useful variables')

# directories and information common to each year and country:
# load in the natural earth data
countries_shp = shpreader.natural_earth(resolution='10m',category='cultural',name='admin_0_countries')


# directories and information common to each month of the dataset:
data_dir = '/gws/pw/j07/ceraf/hbloomfield01/Data/ERA5/'
test_str = 'ERA5_EU_1hr_sfc_weather_1940_01.nc' # 2019_03.nc
coeffs_path = '/home/users/hbloomfield01/CCC/process_ERA5/ERA5_Regression_coeffs_demand_model.csv'

countries = ['United Kingdom']#,"Austria","Belgium","Bulgaria","Croatia","Czechia", "Denmark","Finland","France","Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania","Luxembourg","Montenegro","Netherlands","Norway","Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden","Switzerland"]#["Finland","France","Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania","Luxembourg","Montenegro","Netherlands","Norway","Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden","Switzerland"]

# [ "Austria","Belgium","Bulgaria","Croatia","Czechia", "Denmark","United Kingdom"

# put in iris fix:


for COUNTRY in countries:

    if COUNTRY == 'Czechia':
        COUNTRY_nospace = 'Czech_Republic'
    else:
        COUNTRY_nospace = COUNTRY.replace(" ", "_")
  
    # make country mask
    COND = iris.Constraint('2 metre temperature')

    MASK_MATRIX_RESHAPE = country_mask(data_dir, test_str, COND,COUNTRY)

    # get regression coefficients
    coeffs_country = get_regression_coefficients(COUNTRY_nospace,coeffs_path)  
    
    for YEAR in range(2025,2026):
        print(YEAR)
        for MONTH in ['01','02','03','04','05','06','07','08','09','10','11','12']:
            print(MONTH)

            if YEAR in [1940,1944,1948,1952,1956,1960,1964,1968,1972,1976,1980,1984,1988,1992,1996,2000,2004,2008,2012,2016,2020,2024,2028] and MONTH in ['02']:
                ndays = 29
            elif MONTH == '02':
                ndays = 28
            elif MONTH in ['09','04','06','11']:
                ndays = 30
            else:
                ndays = 31
 
            data_str = 'ERA5_EU_1hr_sfc_weather_' + str(YEAR) + '_' + MONTH + '.nc'# 2019_03.nc
    
            print('loading cubes')
            ds = xr.open_mfdataset(data_dir + data_str, combine='by_coords')
            var = ds['t2m']
            var = var.assign_coords(day_of_year=var['valid_time'].dt.dayofyear)
            daily_mean_field = var.groupby('day_of_year').mean(dim='valid_time')
            print(daily_mean_field)
            mask_array_for_weights = np.concatenate([[MASK_MATRIX_RESHAPE]] * np.shape(daily_mean_field)[0], axis=0)
            # Create 3D weight array from 2D mask
            n_days = daily_mean_field.sizes['day_of_year']
            weights = np.broadcast_to(MASK_MATRIX_RESHAPE, (n_days,) + MASK_MATRIX_RESHAPE.shape)
            weights_da = xr.DataArray(weights, coords=[daily_mean_field['day_of_year'], daily_mean_field['latitude'], daily_mean_field['longitude']], dims=["day_of_year", "latitude", "longitude"])

# Calculate weighted spatial mean for each day
            daily_timeseries_xarray = (daily_mean_field * weights_da).sum(dim=["latitude", "longitude"]) / weights_da.sum(dim=["latitude", "longitude"])

            # Convert units if needed
            # You might need to manually adjust this depending on the input units
            if hasattr(var, 'attrs') and var.attrs.get('units') == 'K':
                 daily_timeseries_xarray =  daily_timeseries_xarray - 273.15
                 daily_timeseries_xarray.attrs['units'] = 'Celsius'    

            # Assume weighted_daily_timeseries is a 1D xarray.DataArray with dim 'day_of_year'
            data =  daily_timeseries_xarray.values
            coord_vals =  daily_timeseries_xarray['day_of_year'].values

            # Create Iris coordinate
            day_of_year_coord = icoords.DimCoord(coord_vals, standard_name='time', units='1')

            # Create cube
            daily_timeseries = icube.Cube(data,
            dim_coords_and_dims=[(day_of_year_coord, 0)],
            standard_name='air_temperature',  # or other appropriate name
            units='Celsius')  # or other appropriate units

            print(daily_timeseries)


     
            print('calculating HDD')
            GB_daily_HDD_ERA5 = HDD_function(daily_timeseries)
            print(np.shape(GB_daily_HDD_ERA5))

            print('calculating CDD')
            GB_daily_CDD_ERA5 = CDD_function(daily_timeseries)
            print('calculating demand')
            GB_daily_weather_dependent_demand_ERA5, GB_daily_full_demand_ERA5 = calc_demands(YEAR,MONTH,coeffs_country,GB_daily_HDD_ERA5,GB_daily_CDD_ERA5)
            GB_daily_weather_dependent_demand_ERA5.units = 'GW'
            GB_daily_weather_dependent_demand_ERA5.rename('Weather-dependent Demand')
            GB_daily_full_demand_ERA5.units = 'GW'
            GB_daily_full_demand_ERA5.rename('Full Demand')
    
            iris.save(GB_daily_HDD_ERA5,'/gws/pw/j07/ceraf/hbloomfield01/Data/ERA5/ERA5_demand_and_national_aggs/ERA5_' + str(COUNTRY_nospace) + '_'+ str(YEAR) + '_' + MONTH + '_HDD_timeseries.nc')
            iris.save(GB_daily_CDD_ERA5,'/gws/pw/j07/ceraf/hbloomfield01/Data/ERA5/ERA5_demand_and_national_aggs/ERA5_' + str(COUNTRY_nospace) + '_'+ str(YEAR) + '_' + MONTH + '_CDD_timeseries.nc')
            iris.save(daily_timeseries,'/gws/pw/j07/ceraf/hbloomfield01/Data/ERA5/ERA5_demand_and_national_aggs/ERA5_' + str(COUNTRY_nospace) + '_'+ str(YEAR) + '_' + MONTH + '_T2m_timeseries.nc')
            iris.save(GB_daily_weather_dependent_demand_ERA5,'/gws/pw/j07/ceraf/hbloomfield01/Data/ERA5/ERA5_demand_and_national_aggs/ERA5_' + str(COUNTRY_nospace) + '_'+ str(YEAR) + '_'+ MONTH + '_wd_demand_timeseries.nc')
            iris.save(GB_daily_full_demand_ERA5,'/gws/pw/j07/ceraf/hbloomfield01/Data/ERA5/ERA5_demand_and_national_aggs/ERA5_' + str(COUNTRY_nospace) + '_'+ str(YEAR) + '_' + MONTH + '_full_demand_timeseries.nc')

