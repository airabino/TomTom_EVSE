import requests as r

interval_minutes = int(input("Enter the scheduled time interval in minutes: "))
charger_id = ["YjKMl-AndGNr4WPDzC1I1w"]
#charger_id could be a list of charger_ids or a single string with 1 charger id
r.schedule_task(interval_minutes, charger_id)
