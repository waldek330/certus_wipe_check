from flask import Flask, request, render_template
import xmlrpc
from xmlrpc import client
from datetime import datetime
import datetime
import requests
import json

app = Flask(__name__, template_folder=r'C:\Users\waldemar.lusiak\Desktop\pas_de_certus_api\templates')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        asset_tag = request.form['asset_tag']
        
        if not validate_asset_tag(asset_tag):
            return render_template('no_asset.html')
        
        odoo_serial = veryfi_asset_serial(asset_tag)
        print(odoo_serial)

        if not odoo_serial:
            return render_template('no_asset.html')
        
        result = send_request(odoo_serial)
        print(result)

        if not result:
            return render_template('not_erased.html')
        
        if result and result[0].get('cewm.ce.report.erasure.status') == 'Erased' or result[0].get('cewm.ce.report.erasure.status') == 'Erased with warnings':
            return render_template('erased.html')
        else:
            return render_template('not_erased.html')
    return render_template('index.html')

def validate_asset_tag(asset_tag):
    return len(asset_tag) == 6 or len(asset_tag) == 10

def send_request(odoo_serial):
    url = "https://cloud.certus.software/webservices/rest-api/reports"
    headers = {
        "accept": "application/json",
        "Customer-Code": "",
        "Accept-Language": "en-US",
        "Authorization": "Basic TktTR3JvdXBTcHpvbzpDb25jb3JkMiE=",
        "Content-Type": "application/json"
    }
    current_year = str(datetime.datetime.now().year)
    start_date = current_year + "-01-01"
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    payload = {
        "reportMode": "ORIGINAL",
        "groupData": "DRIVE",
        "request": {
            "filter": {
                "criteria": [
                    {
                        "column": "cewm.ce.report.erasure.time.start",
                        "conditions": [
                            {
                                "type": "date",
                                "operator": "inRange",
                                "date": start_date,
                                "dateTo": end_date
                            }
                        ]
                    },
                    {
                        "column": "cewm.ce.report.hardware.system.serial.number",
                        "conditions": [
                            {
                                "type": "text",
                                "operator": "contains",
                                "value": odoo_serial
                            }
                        ]
                    }
                ],
                "conjunction": "AND"
            },
            "limit": 1,
            "offset": 0
        },
        "response": {
            "showColumns": [
                "cewm.ce.report.erasure.status",
                "cewm.ce.report.hardware.system.serial.number",
                "cewm.ce.report.erasure.time.start"
            ]
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    return data

def veryfi_asset_serial(odoo_asset):
    try:
        prod_db = ''
        prod_url = ''
        username = ''
        password = ''
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(prod_url))
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(prod_url))
        uid = common.authenticate(prod_db, username, password, {})

        list_record = models.execute_kw(prod_db, uid, password, 'stock.production.lot', 'search_read', [[['itadon_assetid', '=', odoo_asset]]], {'fields': ['itadon_assetid', 'name']})
        odoo_serial = list_record[0]['name']
    except Exception as e:
        print(e)
    
    return odoo_serial

if __name__ == '__main__':
    app.run()
