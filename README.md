# CB Inspector: A Versatile tool for Carbon Black
Carbon Black Enterprise EDR, which stands for Endpoint Detection and Response, is a cybersecurity solution designed to protect enterprise networks and endpoints (like laptops, desktops, and servers) from cyber threats. It was developed by the company Carbon Black, which was later acquired by VMware. 

Carbon Black does not natively offer a parent tenant setup where queries can be run seamlessly across all child tenants. This kind of setup would allow a centralized system or entity to monitor, query, and control various child entities or sub-organizations, facilitating smoother cross-organization data analysis and threat response.

CB Inspector can function as a de-facto parent tenant, essentially bridging the gap in Carbon Black's offering, facilitating better data integration, threat detection, and operational efficiency in multi-tenant environments.

# Requirements
- Carbon Black Enterprise EDR
- Python pip

# Usage
1. Clone this repository:
```
❯ git clone https://github.com/fish-not-phish/cb-inspector.git
```
2. Create a json file with your expected tenant information. Example below:
```
[
    "tenant1",
    "tenant2",
    // more tenants...
]
```
3. Create a `credentials.cbc` file with all the tenant credentials. Each credentials label should correspond with their name you wrote in the previous json file. The label is what is located inside the brackets `[tenant1]`.
```
[tenant1]
url=https://defense-prod05.conferdeploy.net
token=ABCDEFGHIJKLMNO123456789/ABCD123456
org_key=ABCD123456
ssl_verify=true

[tenant2]
url=https://defense-prod05.conferdeploy.net
token=ABCDEFGHIJKLMNO123456789/ABCD123456
org_key=ABCD123456
ssl_verify=true

more tenants...
```
For more information on how to properly set up your `credentials.cbc` file, please view the [Carbon Black SDK Documentation](https://carbon-black-cloud-python-sdk.readthedocs.io/en/latest/authentication/).

Ensure the parent folder and `credentials.cbc` both have the correct permissions set.

4. Install the Carbon Black through pip:
```
❯ pip install carbon-black-cloud-sdk
```
5. Run the script:
```
❯ python3 cb_inspector.py
```
# Features
There are 3 main features of this script. Investigate, Detection Creation and Watchlist Hits.

Three folders will be created within your current working directory:
- Investigations
- Detections
- Watchlist Hits

### Detections
```
❯ detection creation
```
Detections is responsible for threat detection creations. This is a great way to query for specific activity, and if there are no events to match the query, to then create a watchlist/report using the previously input query. If there are events, those events will be returned via the terminal output and a file will be created within your current working directory to store the results. 

If there are no events that match the query, then the script will prompt you to give a watchlist name to use. If a watchlist with that name already exists, a report will be created within that watchlist. Otherwise, a new watchlist will be created using the name entered, and then a report will be created within the new watchlist. The result of the activity will be output in the terminal, as well as a file written to your current working directory for reporting purposes.

This would be useful for creating mass detections over all tenant environments and ensuring there are no false positives or potentially true positive results before implementing a new report into all environments.

- Query watchlist hits for one tenant
- Query watchlist hits for all tenants

Running a Detection query will automatically create two subfolders within `Detections` called `Created` and `Collisions`. A file will be written with the output results called `created_<report_name>_<current_datetime>.txt` if a watchlist/report was created. If a report was not created, a file will be written with the output of the collisions called `collisions_all_<current_datetime>.txt`.

The output will include the following for each event found:
- Tenant Name
- Report Title 
- Report ID
- Alert Count

### Investigate
```
❯ investigate
```
Investigate will allow you to run a query as if you were inside the Carbon Black Cloud console. You will still need to escape special characters, including spaces as you would in the console.

Example query:
```
process_product_name:the\ product\ name filemod_name:.zip 
```

Or, here is an example with a NOT.

```
process_product_name:the\ product\ name NOT filemod_name:.zip 
```

- Investigate across one tenant
    - Investigate on one device
        - Run a query and have results returned to your terminal
    - Investigate across the entire tenant environment
        - Run a query and have results returned to your terminal
- Investigate across all tenants
    - Run a query and have results returned to your terminal
    - Investigates all devices across all tenants

Running an investigate query will automatically create a subfolder within `Investigations` called `Results`. A file will be written with the output results called `results_<tenant>_<current_datetime>.txt`.

The output will include the following for each collision found:
- Tenant Name
- Device Name 
- Device ID
- Process Name
- Condition

The output will include if a watchlist/report is created:
- Tenant Name
- Watchlist Name
- Watchlist Description
- Report Name
- Report Description
- Condition

### Watchlist Hits
```
❯ watchlist hits
```
Watchlist hits will allow you to give a watchlist name and view all the recent alerts associated to the reports within the watchlist. This can be a great way to review watchlists at a mass scale. If a report has more than 30 alerts, you will get a special (red) notification in the terminal.

- Query watchlist hits for one tenant
- Query watchlist hits for all tenants

Running an investigate query will automatically create a subfolder within `Watchlist Hits` called `Hits`. A file will be written with the output results called `hits_<tenant>_<current_datetime>.txt`.

The output will include the following for each event found:
- Tenant Name
- Report Title 
- Report ID
- Alert Count
