"""
.. moduleauthor:: Theresa Boiger <theresa.boiger@gmx.at>
pipeline for dekadal NDVI time series generation
"""

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from PIL import Image
import io
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
from dateutil import relativedelta
import calendar

def main_pipeline(AOI, start_date, end_date, CLIENT_ID, CLIENT_SECRET):
    '''
    main pipeline for dekadal NDVI time series generation
    args:
        AOI (dict): AOI as dict containing 'type' and 'coordinates'
        start_date (str): date in the format 'YYYY-MM-DD'
        end_date (str): date in the format 'YYYY-MM-DD'
        CLIENT_ID (str): client ID from OAuth client
        CLIENT_SECRET (str): client secret from OAuth client

    returns:
        response_list (list): list of tifs for NDVI time series for 1st, 11th and 21st of month within given period
    '''

    start_date_list, end_date_list = define_dates(start_date, end_date)
    coordinates = AOI["coordinates"]

    oauth, token = set_up_token(CLIENT_ID, CLIENT_SECRET)    
    response_list = get_data(start_date_list, end_date_list, coordinates, oauth, token)

    return response_list


def define_dates(start_date, end_date):
    '''
    function to get the start and end dates for dekadal time series within a given time period
    dekadal time series includes time spans from 1st to 10th, 11th to 20th and 21st to end of month for each month
    args:
        start_date (str): date in the format 'YYYY-MM-DD'
        end_date (str): date in the format 'YYYY-MM-DD'

    returns:
        tuple of
        start_date_list (list): list of start dates (1st, 11th, 21st of given period)
        end_date_list (list): list of end dates (9 days after start date or end of month)
    '''

    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d').date()        # transforms string to datetime and checks if input format is correct
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    start_date_list = [start_date]       # initialize list with first start date
    start_date_x = start_date            # add other start dates with 10 day difference to list until end date is reached
    while start_date_x < end_date:
        start_date_y = start_date_x + dt.timedelta(days=10)
        start_date_list.append(start_date_y)
        start_date_x = start_date_y
    else:
        start_date_list.pop()


    for (i, start_date) in enumerate(start_date_list):         # transform given start dates into 1st, 11th and 21st of month
        if start_date.day not in [1, 11, 21]:
            if 2 <= start_date.day <= 10:
                start_date_n = start_date + relativedelta.relativedelta(days=10, day=1)
            if 12 <= start_date.day <= 20:
                start_date_n = start_date + relativedelta.relativedelta(days=20, day=1)
            if 22 <= start_date.day <= 31:
                start_date_n = start_date + relativedelta.relativedelta(months=1, day=1)
            start_date_list[i] =start_date_n

    for sd in start_date_list:          # handle any remaining start dates that are after the end date
        if sd > end_date:
            start_date_list.remove(sd)


    end_date_list = []
    for start_date in start_date_list:         # define end dates based on start dates
        if start_date.month ==2 and start_date.day == 21: # February is a special case: if the start date is 21st, end date is not 30th or 31st, but 28th or 29th
            remaining_days = calendar.monthrange(start_date.year, start_date.month)[1] - start_date.day
            end_date = start_date + dt.timedelta(days=remaining_days)
        else:
            end_date = start_date + dt.timedelta(days=9) # for all other months: end date is always 9 days after start date
        end_date_list.append(end_date)
        
        
    return start_date_list, end_date_list


def set_up_token(CLIENT_ID, CLIENT_SECRET):
    '''
    function to set up access to API
    args:
        CLIENT_ID (str)
        CLIENT_SECRET (str)

    returns:
        tuple of
        oauth: authorization session for client
        token: authentification token
    '''
    
    # set up credentials
    client = BackendApplicationClient(client_id=CLIENT_ID)
    oauth = OAuth2Session(client=client)

    # get an authentication token
    token = oauth.fetch_token(token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
                            client_secret=CLIENT_SECRET, include_client_id=True)

    return oauth, token

def get_data(start_date_list, end_date_list, coordinates, oauth, token):
    '''
    function to get data and calculate NDVI from bands
    NDVI = (B08 -B04) / (B04 + B08)
    args:
        start_date_list (list): start dates for each dekadal time period
        end_date_list (list): end dates for each dekadal time period
        coordinates (list): coordinates of AOI as polygon
        oauth
        token

    returns:
        response_list (list): tif for 10-daily NDVI within given time period
    '''

    response_list = []
    for start_date, end_date in zip(start_date_list, end_date_list):     # Cloud Masking did not work here
        evalscript = """
        //VERSION=3
        function setup() {
        return {
            input: [{bands: ["B04", "B08"], , units: "DN"}],
            output: { id:"default", bands: 1 }
        };
        }


        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B04 + sample.B08)
            return [ndvi];

        }
        """

        # request body/payload
        json_request = {
            'input': {
                'bounds': {
                    'properties': {
                        'crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": coordinates
                    }
                },
                'data': [
                    {
                        'type': 'S2L2A',
                        'dataFilter': {
                            'timeRange': {
                                'from': f'{start_date}T00:00:00Z',
                                'to': f'{end_date}T23:59:59Z'
                            },
                            'maxcc': '0.2',
                            #'mosaickingOrder': 'leastCC',
                        },
                    }
                ]
            },
            'output': {
                'width': 1798.178,       # tried to define the width and height automatically with the method "bbox_to_dimensions" but got wrong results (out of range, above 2500)
                'height': 1162.351,       # therefore set width and height based on Requests Builder
                'responses': [
                    {
                        'identifier': 'default',
                        'format': {
                            'type': 'image/tiff'
                            #'cogOutput': True
                        }
                    }
                ]
            },
            'evalscript': evalscript
        }

        
        
        # Set the request url and headers
        #url_request = 'https://services.sentinel-hub.com/api/v1/process'
        url_request = 'https://sh.dataspace.copernicus.eu/api/v1/process'
        headers_request = {
            "Authorization" : "Bearer %s" %token['access_token']
        }

        #Send the request
        response = oauth.request(
            "POST", url_request, headers=headers_request, json=json_request
        )
        response_list.append(response)

    return response_list

def plot_image(response_list):
    '''
    plots the images from dekadal NDVI time series
    args:
        response_list (list): all tifs for 10-daily NDVI within given time period
    '''

    for response in response_list:
        # read the image as numpy array
        image_arr = np.array(Image.open(io.BytesIO(response.content)))

        # plot the image for visualization
        plt.figure(figsize=(16,16))
        plt.axis('off')
        plt.tight_layout()
        plt.imshow(image_arr)
        plt.show()

if __name__ == '__main__':

    # input parameters
    AOI = {"type": "Polygon", "coordinates": [[[15.272166,46.967134],[15.616379,46.967134],[15.616379,47.11383],[15.272166,47.11383],[15.272166,46.967134]]]}
    start_date = '2025-08-01'
    end_date = '2025-08-31'

    #authentification
    CLIENT_ID = 'sh-872d1524-8b1f-4ca7-9633-de99aa3b6a43'
    CLIENT_SECRET = 'PkwhqLgBQ7cmmUbkWQ4h8LKALaiJZ1bb'

    response_list = main_pipeline(AOI, start_date, end_date, CLIENT_ID, CLIENT_SECRET)
    plot_image(response_list)