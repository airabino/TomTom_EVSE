import os
import json
import time
import requests
import schedule
import numpy as np

from utilities import ProgressBar

default_key='ercfF032eCm1qy8QKpS37UIEeGoWkb8Z'
tomtom_charger_code=7309

def TomTom_Location_Search(
	lon,lat,radius=5000,limit=100,key=default_key,categorySet=tomtom_charger_code):
	
	kwargs=locals()
	kwargs.pop('key')

	request_string=(
		'https://api.tomtom.com/search/2/nearbySearch/.json?'+
		f'key={key}'
		)

	for key,val in kwargs.items():
		if val is not None:

			request_string+=f'&{key}={val}'

	result=requests.get(request_string)

	result_dict=json.loads(result._content.decode('utf-8'))

	return result_dict

def TomTom_EVSE_Information(charger_ids,key=default_key,disp=True):

	if not hasattr(charger_ids,'__iter__'):
		charger_ids=[charger_ids]

	results={charger_id:None for charger_id in charger_ids}

	for idx in ProgressBar(range(len(charger_ids)),disp=disp):

		charger_id=charger_ids[idx]

		request_string=(
			'https://api.tomtom.com/search/2/chargingAvailability.json?'+
			f'key={key}'+
			f'&chargingAvailability={charger_id}'
			)

		try:

			result=requests.get(request_string)

			results[charger_id]=json.loads(result._content.decode('utf-8'))

		except:

			pass

	return results


def TomTom_EVSE_Information_scheduler(charger_ids):
	result = TomTom_EVSE_Information(charger_ids=charger_ids, key=default_key, disp=True)
	print("result afters interval", result)
	

def schedule_task(interval_minutes, charger_ids):

    interval_seconds = interval_minutes * 60

    schedule.every(interval_seconds).seconds.do(TomTom_EVSE_Information_scheduler, charger_ids)
    
    while True:
        schedule.run_pending()
        time.sleep(1)