import cdsapi


for YEAR in range(2025,2026):
    for MONTH in [1,2,3,4]: # [5,6,7,8,9,10,11,12]: 
        m = str(MONTH).zfill(2) # make sure it is 01, 02 etc
        if m in ['04','06','09','11']:
            days = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30']
        elif m in ['01','03','05','07','08','10','12']:
            days = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31']
        else:
            if YEAR in [1940,1944,1948,1952,1956,1960,1964,1968,1972,1976,1980,1984,1988,1992,1996,2000,2004,2008,2012,2016,2020,2024]:
                days = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29']
            else:
                days = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28']

        dataset = "reanalysis-era5-single-levels"
        request = { 
        "product_type": ["reanalysis"],
        "variable": ['10m_u_component_of_wind', '10m_v_component_of_wind', '2m_temperature','mean_sea_level_pressure',],
        "year": [str(YEAR)],
        'month':[m],
        'day': days,
        'time':['00:00','01:00','02:00','03:00','04:00','05:00','06:00','07:00','08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00','20:00','21:00','22:00','23:00'],
            'data_format': "netcdf",
            "download_format": "unarchived",
    "area": [72,-15,34,35],}# N/W/S/E
        target = '/gws/pw/j07/ceraf/hbloomfield01/Data/ERA5/ERA5_EU_1hr_sfc_weather_' + str(YEAR) + '_' + str(m) + '.nc'
        client = cdsapi.Client()
        client.retrieve(dataset, request,target)#.download()

# , 'surface_solar_radiation','total_precipitation',], had to do accumilated as a seperate field or they come out zipped!