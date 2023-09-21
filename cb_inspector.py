from cbc_sdk.helpers import build_cli_parser, get_cb_cloud_object
from cbc_sdk.platform import *
from cbc_sdk import CBCloudAPI
from cbc_sdk.enterprise_edr import *
import os
from datetime import datetime
import json
import sys
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import re

os.makedirs('Investigations', exist_ok=True)
os.makedirs('Detections', exist_ok=True)
os.makedirs('Watchlist Hits', exist_ok=True)
os.makedirs('Outdated Sensors', exist_ok=True)

class Color:
    RESET = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    @staticmethod
    def get_color(color_code):
        return color_code + '{}'.format(Color.RESET)

def display_banner(version):
    return ((f'''{Color.CYAN}
  /$$$$$$  /$$$$$$$        /$$$$$$                                                     /$$                        
 /$$__  $$| $$__  $$      |_  $$_/                                                    | $$                        
| $$  \__/| $$  \ $$        | $$   /$$$$$$$   /$$$$$$$  /$$$$$$   /$$$$$$   /$$$$$$$ /$$$$$$    /$$$$$$   /$$$$$$ 
| $$      | $$$$$$$         | $$  | $$__  $$ /$$_____/ /$$__  $$ /$$__  $$ /$$_____/|_  $$_/   /$$__  $$ /$$__  $$
| $$      | $$__  $$        | $$  | $$  \ $$|  $$$$$$ | $$  \ $$| $$$$$$$$| $$        | $$    | $$  \ $$| $$  \__/
| $$    $$| $$  \ $$        | $$  | $$  | $$ \____  $$| $$  | $$| $$_____/| $$        | $$ /$$| $$  | $$| $$      
|  $$$$$$/| $$$$$$$/       /$$$$$$| $$  | $$ /$$$$$$$/| $$$$$$$/|  $$$$$$$|  $$$$$$$  |  $$$$/|  $$$$$$/| $$      
 \______/ |_______/       |______/|__/  |__/|_______/ | $$____/  \_______/ \_______/   \___/   \______/ |__/      
                                                      | $$                                                        
                                                      | $$                                                        
                                                      |__/
    ''') + (
        f'''{Color.MAGENTA} version: {version}\n''') + (
        f'''{Color.MAGENTA}     by: fishnotphish\n{Color.RESET}''')
    )

def help_manual():
    return f'''{Color.CYAN}\n
    --------------------------------------------------------------------------------------------------------
    Inspector Options
    --------------------------------------------------------------------------------------------------------
    quit                                --> Quit Script
    investigate                         --> Run Query to Return Specific Events Based on Criteria
    detection creation                  --> Workflow to Create New Watchlists/Reports
                                            {Color.MAGENTA}Returns Hits on Custom Investigate Query
                                            If No Hits, Then Create Watchlist/Report{Color.CYAN}
    watchlist hits                      --> Check All Hits Against Specific Watchlist/Report 
    check sensors                       --> Check If Sensors Are Out of Date
    help                                --> Display Help Menu
    \n{Color.RESET}'''

def global_tenant_list(path):
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except FileExistsError:
        print("File not found.")
    except json.JSONDecodeError:
        print("Error decoding file.")

def main():
    global_list = None
    print(display_banner("v1.0"))
    create_global_list = input("Would you like to use a global tenant list or enter a list for every operation performed?\n1. Global List\n2. Enter a list for every operation\n Enter a number: ")
    if create_global_list == "1":
        path = input("Please enter your tenant list file path: ")
        global_list = global_tenant_list(path)
        print(global_list)
    elif create_global_list == "2":
        print("Proceeding without creating a global list...")
    else:
        print(f"{Color.RED}Invalid number entered. Quitting...{Color.RESET}")
        sys.exit()
    print(help_manual())
    print("What would you like to do?\n")

    while True:
        action = input("Enter an action: ")
        if action.lower() == "detection creation":
            scope = input("Is this investigate query for:\n1. One tenant\n2. All tenants\nEnter scope: ")
            if scope == "1":
                tenant_code = input("Enter the tenant code: ")
                tenant_code = tenant_code.upper()
                cb = CBCloudAPI(profile=tenant_code)
                condition = input("Please enter the query condition(s): ")
                time_window = input('Please enter the time window (e.g., "4w"): ')

                query = cb.select(Process)
                query.set_time_range(window=f'-{time_window}')
                query.where(condition)

                hits_dict = {}
                result_dict = {}

                if query:
                    hits_dict[tenant_code] = hits_dict.get(tenant_code, [])
                    for event in query:
                        device_id = event.device_id
                        process_name = event.process_name
                        print("--------------------------------------------------")
                        print(f"Device ID: {device_id}")
                        print(f"Process Name: {process_name}")

                        hit_dict = {
                            "Device ID": device_id,
                            "Process Name": process_name
                        }

                        hits_dict[tenant_code].append(hit_dict)

                if hits_dict:
                    os.makedirs(os.path.join('Detections', 'Collisions'), exist_ok=True)
                    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    with open(os.path.join('Detections', 'Collisions', f'collisions_{tenant_code}_{current_datetime}.txt'), 'w') as file:
                        file.write(f'{current_datetime} Collision Report For {tenant_code}:\n')
                        file.write("------------------------------------------------------------------\n")
                        for tenant, hits in hits_dict.items():
                            for hit in hits:
                                file.write(f"Device ID: {hit['Device ID']}\n")
                                file.write(f"Process Name: {hit['Process Name']}\n")
                                file.write("------------------------------------------------------------------\n")
                else:
                    print(f"{Color.GREEN}No matches for {tenant_code}.{Color.RESET}")
                    watchlist_name = input("What is the watchlist name you would like to create?\nPlease enter a name: ")
                    existing_watchlists = cb.select(Watchlist)
                    report_created = False
                    ioc_name = ""
                    result_dict = {}
                    for wl in existing_watchlists:
                        if wl.name.lower() == watchlist_name.lower():
                            result_dict[tenant_code] = result_dict.get(tenant_code, [])
                            
                            report_name = input("Please enter a name for your new report: ")
                            report_desc = input("Please enter a description for your new report: ")

                            builder = Report.create(cb, str(report_name), str(report_desc), 5)
                            report_ioc_name = report_name.replace(" ", "-").lower()
                            ioc_name = report_ioc_name
                            builder.add_ioc(IOC_V2.create_query(cb, str(report_ioc_name), str(condition)))
                            report = builder.build()
                            report.save_watchlist()

                            wl.add_reports([report])
                            wl.save()
                            report_created = True

                            report_dict = {
                                "Report Name" : report_name,
                                "Report Description": report_desc,
                                "Condition": condition,
                            }

                            result_dict[tenant_code].append(report_dict)

                            print(f"{Color.GREEN}Report has been created!{Color.RESET}")
                    if result_dict:
                        os.makedirs(os.path.join('Detections', 'Created'), exist_ok=True)
                        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                        with open(os.path.join('Detections', 'Created', f'created{ioc_name}_{current_datetime}.txt'), 'w') as file:
                            file.write(f'{current_datetime} Report Created For {tenant_code}:\n')
                            file.write("------------------------------------------------------------------\n")
                            for tenant, reports in result_dict.items():
                                for report in reports:
                                    file.write(f"Report Name: {report['Report Name']}\n")
                                    file.write(f"Report Description: {report['Report Description']}\n")
                                    file.write(f"Condition: {report['Condition']}\n")
                                    file.write("------------------------------------------------------------------\n")
                        break
                    if not report_created:
                        result_dict = {}
                        wl_desc = input("Please enter a description for your new Watchlist: ")
                        report_name = input("Please enter a name for your new report: ")
                        report_desc = input("Please enter a description for your new report: ")
                        result_dict[tenant_code] = result_dict.get(tenant_code, [])
                        
                        print(f"{Color.YELLOW}Creating new Watchlist & Report...")
                        print(f"Using conditions: {condition}{Color.RESET}")
                        builder = Report.create(cb, str(report_name), str(report_desc), 5)
                        report_ioc_name = report_name.replace(" ", "-").lower()
                        builder.add_ioc(IOC_V2.create_query(cb, str(report_ioc_name), str(condition)))
                        report = builder.build()
                        report.save_watchlist()

                        wl_builder = Watchlist.create(cb, str(watchlist_name))
                        wl_builder.set_description(str(wl_desc)).add_reports([report])
                        watchlist = wl_builder.build()
                        watchlist.save()

                        wl_dict = {
                            "Watchlist Name": watchlist_name,
                            "Watchlist Description": wl_desc,
                            "Report Name": report_name,
                            "Report Description": report_desc,
                            "Condition": condition,
                        }

                        result_dict[tenant_code].append(wl_dict)

                        print(f"{Color.GREEN}Watchlist and report have been created!{Color.RESET}")
                    if result_dict:
                        os.makedirs(os.path.join('Detections', 'Created'), exist_ok=True)
                        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                        with open(os.path.join('Detections', 'Created', f'created{ioc_name}_{current_datetime}.txt'), 'w') as file:
                            file.write(f'{current_datetime} Watchlist and Report Created For {tenant_code}:\n')
                            file.write("------------------------------------------------------------------\n")
                            for tenant, wls in result_dict.items():
                                for wl in wls:
                                    file.write(f"Watchlist Name: {wl['Watchlist Name']}\n")
                                    file.write(f"Watchlist Description: {wl['Watchlist Description']}\n")
                                    file.write(f"Report Name: {wl['Report Name']}\n")
                                    file.write(f"Report Description: {wl['Report Description']}\n")
                                    file.write(f"Condition: {wl['Condition']}\n")
                                    file.write("------------------------------------------------------------------\n")
            elif scope == "2":
                if global_list is None:
                    file_path = input('Please input the file that your tenant list is stored: ')
                    
                    try:
                        with open(file_path, 'r') as file:
                            tenant_list = json.load(file)
                    except FileExistsError:
                        print("File not found.")
                    except json.JSONDecodeError:
                        print("Error decoding file.")
                else:
                    tenant_list = global_list
                condition = input("Please enter the query condition(s): ")
                time_window = input('Please enter the time window (e.g., "4w"): ')
                hits_dict = {}
                ioc_name = ""

                for tenant in tenant_list:
                    cb = CBCloudAPI(profile=tenant)
                    condition = input("Please enter the query condition(s): ")
                    time_window = input('Please enter the time window (e.g., "4w"): ')

                    query = cb.select(Process)
                    query.set_time_range(window=f'-{time_window}')
                    query.where(condition)

                    if query:
                        hits_dict[tenant] = hits_dict.get(tenant, [])
                        for event in query:
                            device_id = event.device_id
                            device_name = event.device_name
                            process_name = event.process_name
                            print("--------------------------------------------------")
                            print(f"{Color.RED}Matching event for {device_name}!{Color.RESET}")
                            print(f"Device name: {device_name}")
                            print(f"Device ID: {device_id}")
                            print(f"Process Name: {process_name}")
                            print(f"Condition: {condition}")

                            hit_dict = {
                                "Device Name": device_name,
                                "Device ID": device_id,
                                "Process Name": process_name
                            }

                            hits_dict[tenant].append(hit_dict)
                    if hits_dict:
                        os.makedirs(os.path.join('Detections', 'Collisions'), exist_ok=True)
                        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                        with open(os.path.join('Detections', 'Collisions', f'collisions_all_{current_datetime}.txt'), 'w') as file:
                            for tenant, hits in hits_dict.items():
                                file.write(f"{current_datetime} Report Created For {tenant}:\n")
                                file.write("------------------------------------------------------------------\n")
                                for hit in hits:
                                    file.write(f"Device Name: {hit['Device Name']}\n")
                                    file.write(f"Device ID: {hit['Device ID']}\n")
                                    file.write(f"Process Name: {hit['Process Name']}\n")
                                    file.write(f"Condition: {condition}\n")
                                    file.write("------------------------------------------------------------------\n")
                    else:
                        print(f"{Color.GREEN}No matches for {tenant_code}.{Color.RESET}")
                        watchlist_name = input("What is the watchlist name you would like to create?\nPlease enter a name: ")
                        existing_watchlists = cb.select(Watchlist)
                        report_created = False
                        result_dict = {}
                        for wl in existing_watchlists:
                            if wl.name.lower() == watchlist_name.lower():
                                result_dict[tenant] = result_dict.get(tenant, [])
                                report_name = input("Please enter a name for your new report: ")
                                report_desc = input("Please enter a description for your new report: ")

                                builder = Report.create(cb, str(report_name), str(report_desc), 5)
                                report_ioc_name = report_name.replace(" ", "-").lower()
                                ioc_name = report_ioc_name
                                builder.add_ioc(IOC_V2.create_query(cb, str(report_ioc_name), str(condition)))
                                report = builder.build()
                                report.save_watchlist()

                                wl.add_reports([report])
                                wl.save()
                                report_created = True

                                report_dict = {
                                    "Report Name": report_name,
                                    "Report Description": report_desc,
                                    "Condition": condition,
                                }

                                result_dict[tenant].append(report_dict)

                                print(f"{Color.GREEN}Report has been created!{Color.RESET}")
                        if result_dict:
                            os.makedirs(os.path.join('Detections', 'Created'), exist_ok=True)
                            current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                            with open(os.path.join('Detections', 'Created', f'created_{ioc_name}_{current_datetime}.txt'), 'w') as file:
                                for tenant, reports in result_dict.items():
                                    file.write(f"{current_datetime} Report Created For {tenant}:\n")
                                    file.write("------------------------------------------------------------------\n")
                                    for report in reports:
                                        file.write(f"Report Name: {report['Report Name']}\n")
                                        file.write(f"Report Description: {report['Report Description']}\n")
                                        file.write(f"Condition: {report['Condition']}\n")
                                        file.write("------------------------------------------------------------------\n")

                            break
                        if not report_created:
                            result_dict = {}
                            wl_desc = input("Please enter a description for your new Watchlist: ")
                            report_name = input("Please enter a name for your new report: ")
                            report_desc = input("Please enter a description for your new report: ")
                            result_dict[tenant_code] = result_dict.get(tenant_code, [])
                            
                            print(f"{Color.YELLOW}Creating new Watchlist & Report...")
                            print(f"Using conditions: {condition}{Color.RESET}")
                            builder = Report.create(cb, str(report_name), str(report_desc), 5)
                            report_ioc_name = report_name.replace(" ", "-").lower()
                            ioc_name = report_ioc_name
                            builder.add_ioc(IOC_V2.create_query(cb, str(report_ioc_name), str(condition)))
                            report = builder.build()
                            report.save_watchlist()

                            wl_builder = Watchlist.create(cb, str(watchlist_name))
                            wl_builder.set_description(str(wl_desc)).add_reports([report])
                            watchlist = wl_builder.build()
                            watchlist.save()

                            wl_dict = {
                                "Watchlist Name": watchlist_name,
                                "Watchlist Description": wl_desc,
                                "Report Name": report_name,
                                "Report Description": report_desc,
                                "Condition": condition,
                            }

                            result_dict[tenant_code].append(wl_dict)
                            print(f"{Color.GREEN}Watchlist and report have been created!{Color.RESET}")

                        if result_dict:
                            os.makedirs(os.path.join('Detections', 'Created'), exist_ok=True)
                            current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                            with open(os.path.join('Detections', 'Created', f'created_{ioc_name}_{current_datetime}.txt'), 'w') as file:
                                file.write(f'{current_datetime} Watchlist and Report Created For {tenant_code}:\n')
                                file.write("------------------------------------------------------------------\n")
                                for tenant, wls in result_dict.items():
                                    for wl in wls:
                                        file.write(f"Watchlist Name: {wl['Watchlist Name']}\n")
                                        file.write(f"Watchlist Description: {wl['Watchlist Description']}\n")
                                        file.write(f"Report Name: {wl['Report Name']}\n")
                                        file.write(f"Report Description: {wl['Report Description']}\n")
                                        file.write(f"Condition: {wl['Condition']}\n")
                                        file.write("------------------------------------------------------------------\n")
        elif action.lower() == "investigate":
            scope = input("Is this investigate query for:\n1. One tenant\n2. All tenants\nEnter scope: ")
            if scope == "1":
                tenant_code = input("Enter the tenant code: ")
                tenant_code = tenant_code.upper()
                cb = CBCloudAPI(profile=tenant_code)
                device_scope = input("Is this investigate query for:\n1. One Device\n2. All Devices\nEnter scope: ")
                if device_scope == "1":
                    device_name = input("Enter the device name (case sensitive): ")
                    device_name = device_name.replace("\\", "\\")
                    device_name = f"device_name:{device_name} "
                    condition = input("Please enter the query condition(s): ")
                    time_window = input('Please enter the time window (e.g., "4w"): ')

                    query = cb.select(Process)
                    query.set_time_range(window=f'-{time_window}')
                    condition = device_name + condition
                    query.where(condition)

                    result_dict = {}

                    if query:
                        result_dict[tenant_code] = result_dict.get(tenant_code, [])
                        for event in query:
                            device_id = event.device_id
                            device_name = event.device_name
                            process_name = event.process_name

                            event_dict = {
                                "Device Name": device_name,
                                "Device ID": device_id,
                                "Process Name": process_name,
                                "Condition": condition,
                            }

                            result_dict[tenant_code].append(event_dict)
                            
                            print("--------------------------------------------------")
                            print(f"{Color.RED}Matching event for {device_name}!{Color.RESET}")
                            print(f"Device name: {device_name}")
                            print(f"Device ID: {device_id}")
                            print(f"Process Name: {process_name}")

                    if result_dict:
                        os.makedirs(os.path.join('Investigations', 'Results'), exist_ok=True)
                        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                        with open(os.path.join('Investigations', 'Results', f'results_{tenant_code}_{current_datetime}.txt'), 'w') as file:
                            file.write(f"tenant: {tenant_code}\n")
                            file.write("------------------------------------------------------------------\n")
                            for tenant, events in result_dict.items():
                                for event in events:
                                    file.write(f"Device Name: {event['Device Name']}\n")
                                    file.write(f"Device ID: {event['Device ID']}\n")
                                    file.write(f"Process Name: {event['Process Name']}\n")
                                    file.write(f"Condition: {event['Condition']}\n")
                                    file.write("------------------------------------------------------------------\n")

                    else:
                        print(f"{Color.GREEN}No matches for {device_name}.{Color.RESET}")
                elif device_scope == "2":
                    condition = input("Please enter the query condition(s): ")
                    time_window = input('Please enter the time window (e.g., "4w"): ')
                    query = cb.select(Process)
                    query.set_time_range(window=f'-{time_window}')
                    query.where(condition)
                    result_dict = {}
                    if query:
                        result_dict[tenant_code] = result_dict.get(tenant_code, [])
                        for event in query:
                            device_id = event.device_id
                            device_name = event.device_name
                            process_name = event.process_name
                            print("--------------------------------------------------")
                            print(f"{Color.RED}Matching event for {tenant_code}!{Color.RESET}")
                            print(f"Device name: {device_name}")
                            print(f"Device ID: {device_id}")
                            print(f"Process Name: {process_name}")

                            event_dict = {
                                "Device Name": device_name,
                                "Device ID": device_id,
                                "Process Name": process_name,
                                "Condition": condition,
                            }

                            result_dict[tenant_code].append(event_dict)

                        if result_dict:
                            os.makedirs(os.path.join('Investigations', 'Results'), exist_ok=True)
                            current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                            with open(os.path.join('Investigations', 'Results', f'results_{tenant_code}_{current_datetime}.txt'), 'w') as file:
                                file.write(f"tenant: {tenant_code}\n")
                                file.write("------------------------------------------------------------------\n")
                                for tenant, events in result_dict.items():
                                    for event in events:
                                        file.write(f"Device Name: {event['Device Name']}\n")
                                        file.write(f"Device ID: {event['Device ID']}\n")
                                        file.write(f"Process Name: {event['Process Name']}\n")
                                        file.write(f"Condition: {event['Condition']}\n")
                                        file.write("------------------------------------------------------------------\n")
                    else:
                        print(f"{Color.GREEN}No matches for {tenant_code}.{Color.RESET}")
                else:
                    print(f"{Color.RED}Invalid number entered.{Color.RESET}")
            elif scope == "2":
                if global_list is None:
                    file_path = input('Please input the file that your tenant list is stored: ')
                    
                    try:
                        with open(file_path, 'r') as file:
                            tenant_list = json.load(file)
                    except FileExistsError:
                        print("File not found.")
                    except json.JSONDecodeError:
                        print("Error decoding file.")
                else:
                    tenant_list = global_list
                condition = input("Please enter the query condition(s): ")
                time_window = input('Please enter the time window (e.g., "4w"): ')

                result_dict = {}

                for tenant in tenant_list:
                    cb = CBCloudAPI(profile=tenant)
                    query = cb.select(Process)
                    query.set_time_range(window=f'-{time_window}')
                    query.where(condition)
                    if query:
                        result_dict[tenant] = result_dict.get(tenant, [])
                        for event in query:
                            device_id = event.device_id
                            device_name = event.device_name
                            process_name = event.process_name

                            event_dict = {
                                "Device Name": device_name,
                                "Device ID": device_id,
                                "Process Name": process_name,
                                "Condition": condition,
                            }

                            result_dict[tenant].append(event_dict)

                            print("--------------------------------------------------")
                            print(f"{Color.RED}Matching event for {tenant}!{Color.RESET}")
                            print(f"Device name: {device_name}")
                            print(f"Device ID: {device_id}")
                            print(f"Process Name: {process_name}")
                    else:
                        print(f"{Color.GREEN}No matches for {tenant}.{Color.RESET}")
                if result_dict:
                    os.makedirs(os.path.join('Investigations', 'Results'), exist_ok=True)
                    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    with open(os.path.join('Investigations', 'Results', f'results_all_{current_datetime}.txt'), 'w') as file:
                        file.write(f"Investigation query for: {condition}\n")
                        file.write(f"Date/Time: {current_datetime}\n")
                        file.write("------------------------------------------------------------------\n") 
                        for tenant, events in result_dict.items():
                            for event in events:
                                file.write(f"tenant: {tenant}\n")
                                file.write(f"Device Name: {event['Device Name']}\n")
                                file.write(f"Device ID: {event['Device ID']}\n")
                                file.write(f"Process Name: {event['Process Name']}\n")
                                file.write(f"Condition: {event['Condition']}\n")
                                file.write("------------------------------------------------------------------\n")        
            else:
                print(f"{Color.RED}Invalid number entered.{Color.RESET}")
        elif action.lower() == "watchlist hits":
            result_dict = {}
            scope = input("Is this investigate query for:\n1. One tenant\n2. All tenants\nEnter scope: ")
            if scope == "1":
                tenant_code = input("Enter the tenant code: ")
                tenant_code = tenant_code.upper()
                cb = CBCloudAPI(profile=tenant_code)
                wl_name =  input("Enter the watchlist Name: ")
                wl_query = cb.select(Watchlist).all()
                if wl_query:
                    for wl in wl_query:
                        if wl.name == wl_name:
                            wl_id = wl.id
                            query = cb.select(Watchlist, wl_id)
                            if query:
                                result_dict[tenant_code] = []
                                for report_id in query.report_ids:
                                    report = cb.select(Report, str(report_id))
                                    alert_query = cb.select(BaseAlert).where(f'report_id:{report_id}')
                                    alert_count = len(list(alert_query))

                                    if alert_count > 0:
                                        print(f'{Color.RED}Report: {report.title} has {alert_count} hits!{Color.RESET}')
                                        print(f'Report ID: {report_id}')

                                        result_info = {
                                            "Report Title": report.title,
                                            "Report ID": report_id,
                                            "Alert Count": alert_count
                                        }

                                        result_dict[tenant_code].append(result_info)

                                        if alert_count > 30:
                                            print(f'{Color.RED}This report needs to be reviewed.{Color.RESET}')
                                        print("-----------------------------------------------------------")
                            if result_dict:
                                os.makedirs(os.path.join('Watchlist Hits', 'Hits'), exist_ok=True)
                                current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                                with open(os.path.join('Watchlist Hits', 'Hits', f'hits_{tenant_code}_{current_datetime}.txt'), 'w') as file:
                                    file.write(f"Current watchlist ({wl_name}) hits.\n")
                                    file.write(f"Date/Time: {current_datetime}\n")
                                    file.write("------------------------------------------------------------------\n") 
                                    for tenant, reports in result_dict.items():
                                        file.write(f"tenant: {tenant}\n")
                                        for report in reports:
                                            file.write(f"Report Title: {report['Report Title']}\n")
                                            file.write(f"Report ID: {report['Report ID']}\n")
                                            file.write(f"Alert Count: {report['Alert Count']}\n")
                                            file.write("------------------------------------------------------------------\n") 
            elif scope == "2":
                if global_list is None:
                    file_path = input('Please input the file that your tenant list is stored: ')
                    
                    try:
                        with open(file_path, 'r') as file:
                            tenant_list = json.load(file)
                    except FileExistsError:
                        print("File not found.")
                    except json.JSONDecodeError:
                        print("Error decoding file.")
                else:
                    tenant_list = global_list

                for tenant in tenant_list:
                    cb = CBCloudAPI(profile=tenant)
                    wl_name =  input("Enter the watchlist Name: ")
                    wl_query = cb.select(Watchlist).all()
                    if wl_query:
                        for wl in wl_query:
                            if wl.name == wl_name:
                                wl_id = wl.id
                                query = cb.select(Watchlist, wl_id)
                                if query:
                                    result_dict[tenant] = result_dict.get(tenant, [])
                                    for report_id in query.report_ids:
                                        report = cb.select(Report, str(report_id))
                                        alert_query = cb.select(BaseAlert).where(f'report_id:{report_id}')
                                        alert_count = len(list(alert_query))
                                        if alert_count > 0:
                                            print(f'{Color.RED}Report {report.title} has {alert_count} hits!{Color.RESET}')
                                            print(f'Report ID: {report_id}')

                                            report_dict = {
                                                "Report Title": report.title,
                                                "Report ID": report_id,
                                                "Alert Count": alert_count
                                            }

                                            result_dict[tenant].append(report_dict)

                                            if alert_count > 30:
                                                print(f'{Color.RED}This report needs to be reviewed.{Color.RESET}')
                                            print("-----------------------------------------------------------")
                            if result_dict:
                                os.makedirs(os.path.join('Watchlist Hits', 'Hits'), exist_ok=True)
                                current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                                with open(os.path.join('Watchlist Hits', 'Hits', f'hits_all_{current_datetime}.txt'), 'w') as file:
                                    file.write(f"Watchlist query for: {wl_name}\n")
                                    file.write(f"Date/Time: {current_datetime}\n")
                                    file.write("------------------------------------------------------------------\n") 
                                    for tenant, reports in result_dict.items():
                                        for report in reports:
                                            file.write(f"tenant: {tenant}\n")
                                            file.write(f"Report Title: {report['Report Title']}\n")
                                            file.write(f"Report ID: {report['Report ID']}\n")
                                            file.write(f"Alert Count: {report['Alert Count']}\n")
                                            file.write("------------------------------------------------------------------\n") 
            else:
                print(f"{Color.RED}Invalid number entered.{Color.RESET}")
        elif action.lower() == "check sensors":
            groups = {}
            result_dict = {}
            print("Pulling most recent sensor versions. Please wait...")
            url = "https://docs.vmware.com/en/VMware-Carbon-Black-Cloud/index.html"
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--log-level=3')
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            driver = webdriver.Chrome(options=options)
            try:
                driver.get(url)
                sleep(10)
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                elements = soup.find_all(class_="noLabel")
                no_label_contents = [
                    element.get_text(separator=' ', strip=True)
                    for element in elements
                    if "Release Notes" in element.get_text()
                    and "DEPRECATED" not in element.get_text()
                    and "Container" not in element.get_text()
                ]
                groups = {
                    "VMware Carbon Black Cloud Windows Sensor": [],
                    "VMware Carbon Black Cloud Linux Sensor": [],
                    "VMware Carbon Black Cloud macOS Sensor": []
                }
                for content in no_label_contents:
                    version_number = re.search(r'(\d+\.\d+\.\d+\.\d+)', content)
                    if version_number:
                        version_number = version_number[0]
                        for key in groups.keys():
                            if key in content:
                                groups[key].append(version_number)
                                break
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                driver.quit()
            scope = input("Is this investigate query for:\n1. One tenant\n2. All tenants\nEnter scope: ")
            if scope == "1":
                tenant_code = input("Enter the tenant code: ")
                tenant_code = tenant_code.upper()
                cb = CBCloudAPI(profile=tenant_code)
                w_w_c = 0
                w_w_n_u = 0
                w_s_c = 0
                w_s_n_u = 0
                m_c = 0
                m_n_u = 0
                query = cb.select(Device).all()
                result_dict[tenant_code] = []
                for device in query:
                    os_version_lower = device.os_version.lower()
                    os_lower = device.os.lower()
                    sensor_version = device.sensor_version
                    if "windows server" in os_version_lower or "server 2012 r2" in os_version_lower:
                        w_s_c += 1
                        group = groups["VMware Carbon Black Cloud Windows Sensor"]
                        if sensor_version not in group[:3]:
                            print(f"{device.os_version} with Device Name: {device.name} is out of date.")
                            print(f"Current sensor version: {sensor_version}")
                            print(f"----------------------------------------")
                            w_s_n_u += 1
                            result_info = {
                                "Device OS Version": device.os_version,
                                "Device Name": device.name,
                                "Sensor Version": sensor_version
                            }

                            result_dict[tenant_code].append(result_info)
                    # elif "linux" in os_lower:
                    #     group = groups["VMware Carbon Black Cloud Linux Sensor"]
                    #     if sensor_version not in group[:3]:
                    #         print(f"{os_type} with Device Name: {device.name} is out of date.")
                    #         print(f"Current sensor version: {sensor_version}")
                    #         print(f"----------------------------------------")
                    elif "mac" in os_version_lower:
                        m_c += 1
                        group = groups["VMware Carbon Black Cloud macOS Sensor"]
                        if sensor_version not in group[:3]:
                            print(f"{device.os_version} with Device Name: {device.name} is out of date.")
                            print(f"Current sensor version: {sensor_version}")
                            print(f"----------------------------------------")
                            m_n_u += 1
                            result_info = {
                                "Device OS Version": device.os_version,
                                "Device Name": device.name,
                                "Sensor Version": sensor_version
                            }

                            result_dict[tenant_code].append(result_info)
                    elif "windows 10" in os_version_lower or "windows 11" in os_version_lower or "windows 7" in os_version_lower:
                        w_w_c += 1
                        group = groups["VMware Carbon Black Cloud Windows Sensor"]
                        if sensor_version not in group[:3]:
                            print(f"{device.os_version} with Device Name: {device.name} is out of date.")
                            print(f"Current sensor version: {sensor_version}")
                            print(f"----------------------------------------")
                            w_w_n_u += 1
                            result_info = {
                                "Device OS Version": device.os_version,
                                "Device Name": device.name,
                                "Sensor Version": sensor_version
                            }

                            result_dict[tenant_code].append(result_info)
                print(f"Windows Workstations Out of Date: {w_w_n_u}/{w_w_c}")
                print(f"Mac Machines Out of Date: {m_n_u}/{m_c}")
                print(f"Windows Servers Out of Date: {w_s_n_u}/{w_s_c}")
                print(f"All Devices Out of Date: {w_w_n_u + m_n_u + w_s_n_u}/{w_w_c + m_c + w_s_c}")
                if result_dict:
                    os.makedirs(os.path.join('Outdated Sensors', 'Results'), exist_ok=True)
                    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    with open(os.path.join('Outdated Sensors', 'Results', f'results_{tenant_code}_{current_datetime}.txt'), 'w') as file:
                        file.write(f"Tenant: {tenant_code}\n")
                        file.write(f"Windows Workstations Out of Date: {w_w_n_u}/{w_w_c}\n")
                        file.write(f"Mac Machines Out of Date: {m_n_u}/{m_c}\n")
                        file.write(f"Windows Servers Out of Date: {w_s_n_u}/{w_s_c}\n")
                        file.write(f"All Devices Out of Date: {w_w_n_u + m_n_u + w_s_n_u}/{w_w_c + m_c + w_s_c}")
                        file.write(f"Date/Time: {current_datetime}\n")
                        file.write("------------------------------------------------------------------\n") 
                        for tenant, devices in result_dict.items():
                            for device in devices:
                                file.write(f"Device OS Version: {device['Device OS Version']}\n")
                                file.write(f"Device Name: {device['Device Name']}\n")
                                file.write(f"Sensor Version: {device['Sensor Version']}\n")
                                file.write("------------------------------------------------------------------\n") 
            elif scope == "2":
                if global_list is None:
                    file_path = input('Please input the file that your tenant list is stored: ')
                    
                    try:
                        with open(file_path, 'r') as file:
                            tenant_list = json.load(file)
                    except FileExistsError:
                        print("File not found.")
                    except json.JSONDecodeError:
                        print("Error decoding file.")
                else:
                    tenant_list = global_list

                for tenant in tenant_list:
                    cb = CBCloudAPI(profile=tenant)
                    w_w_c = 0
                    w_w_n_u = 0
                    w_s_c = 0
                    w_s_n_u = 0
                    m_c = 0
                    m_n_u = 0
                    query = cb.select(Device).all()
                    result_dict[tenant] = result_dict.get(tenant, [])
                    for device in query:
                        os_version_lower = device.os_version.lower()
                        os_lower = device.os.lower()
                        sensor_version = device.sensor_version
                        if "windows server" in os_version_lower or "server 2012 r2" in os_version_lower:
                            w_s_c += 1
                            group = groups["VMware Carbon Black Cloud Windows Sensor"]
                            if sensor_version not in group[:3]:
                                w_s_n_u += 1

                                result_info = {
                                    "Device OS Version": device.os_version,
                                    "Device Name": device.name,
                                    "Sensor Version": sensor_version
                                }

                                result_dict[tenant].append(result_info)
                        # elif "linux" in os_lower:
                        #     group = groups["VMware Carbon Black Cloud Linux Sensor"]
                        #     if sensor_version not in group[:3]:
                        #         print(f"{os_type} with Device Name: {device.name} is out of date.")
                        #         print(f"Current sensor version: {sensor_version}")
                        #         print(f"----------------------------------------")
                        elif "mac" in os_version_lower:
                            m_c += 1
                            group = groups["VMware Carbon Black Cloud macOS Sensor"]
                            if sensor_version not in group[:3]:
                                m_n_u += 1

                                result_info = {
                                    "Device OS Version": device.os_version,
                                    "Device Name": device.name,
                                    "Sensor Version": sensor_version
                                }

                                result_dict[tenant].append(result_info)
                        elif "windows 10" in os_version_lower or "windows 11" in os_version_lower or "windows 7" in os_version_lower:
                            w_w_c += 1
                            group = groups["VMware Carbon Black Cloud Windows Sensor"]
                            if sensor_version not in group[:3]:
                                w_w_n_u += 1
                                
                                result_info = {
                                    "Device OS Version": device.os_version,
                                    "Device Name": device.name,
                                    "Sensor Version": sensor_version
                                }

                                result_dict[tenant].append(result_info)
                    print(f"Tenant: {tenant}")
                    print(f"Windows Workstations Out of Date: {w_w_n_u}/{w_w_c}")
                    print(f"Mac Machines Out of Date: {m_n_u}/{m_c}")
                    print(f"Windows Servers Out of Date: {w_s_n_u}/{w_s_c}")
                    print(f"All Devices Out of Date: {w_w_n_u + m_n_u + w_s_n_u}/{w_w_c + m_c + w_s_c}")
                    print("------------------------------------------------------------------") 
                if result_dict:
                    os.makedirs(os.path.join('Outdated Sensors', 'Results'), exist_ok=True)
                    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    with open(os.path.join('Outdated Sensors', 'Results', f'results_all_{current_datetime}.txt'), 'w') as file:
                        file.write(f"Date/Time: {current_datetime}\n")
                        file.write("------------------------------------------------------------------\n") 
                        for tenant, devices in result_dict.items():
                            for device in devices:
                                file.write(f"tenant: {tenant}\n")
                                file.write(f"Device OS Version: {device['Device OS Version']}\n")
                                file.write(f"Device Name: {device['Device Name']}\n")
                                file.write(f"Sensor Version: {device['Sensor Version']}\n")
                                file.write("------------------------------------------------------------------\n")
        elif action.lower() == "quit":
            break
        elif action.lower() == "help":
            print(help_manual())
        else:
            print(f"{Color.RED}Invalid option. Please try again.\n{Color.RESET}")
if __name__ == "__main__":
    main()