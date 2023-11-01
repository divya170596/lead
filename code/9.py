from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from simple_salesforce import Salesforce

app = Flask(__name__)
CORS(app)

# Initialize the Salesforce client
sf = Salesforce(
    username='ashwini.kahalkar0@itradiant.com.uat',
    password='Sfdc@1234567',
    security_token='2IjGPqcStQmu97r7RTdS8NgV',
    domain='test'
)

# Define a function to group 'AnnualRevenue' values into ranges
def group_annual_revenue(revenue):
    if revenue is None:
        return 'Unknown'
    
    ranges = [
        (0, 500000),
        (500001, 2000000),
        (2000001, 4000000),
        (4000001, 6000000),
        (6000001, 8000000)
    ]

    for start, end in ranges:
        if start <= revenue <= end:
            lower_str = ""
            upper_str = ""

            if start < 1000:
                lower_str = str(start)
            elif start < 1000000:
                lower_str = f"{start // 1000}k"
            else:
                lower_str = f"{start // 1000000}M"

            if end < 1000:
                upper_str = str(end)
            elif end < 1000000:
                upper_str = f"{end // 1000}k"
            else:
                upper_str = f"{end // 1000000}M"

            return f"{lower_str} - {upper_str}"

    return 'Unknown'

# Define a route to fetch Lead data from Salesforce and display it in a table format
@app.route('/', methods=['GET'])
def lead_table():
    # Query Salesforce to fetch data from the 'Lead' object
    query = 'SELECT FirstName, LastName, Title, Email, Phone, Country__c, Company, Industry, Status, AnnualRevenue, NumberOfEmployees, Technology__c, Technology_Service__c FROM Lead'
    
    try:
        result = sf.query_all(query)
        records = result['records']

        lead_data = []

        for record in records:
            annual_revenue = record.get('AnnualRevenue')
            exist = 'No'

            if annual_revenue is not None:
                record['RevenueRange'] = group_annual_revenue(annual_revenue)

            technology = record.get('Technology__c')
            technology_service = record.get('Technology_Service__c')

            exists = 'No'

            if technology is not None and technology_service is not None:
                services_to_check = {
                    'AI': ['AI Chatbots and Virtual Assistants'],
                    'RPA': ['Process Analysis and Optimization', 'RPA Consulting and Strategy'],
                    'SAP': ['SAP Customization and Development', 'SAP Implementation and Consulting'],
                    'CRM': ['CRM Software Implementation', 'CRM Integration and Customization']
                }

                for service_category, service_list in services_to_check.items():
                    for service in service_list:
                        if service in technology or service in technology_service:
                            exists = 'Yes'
                            break

            record['Exists'] = exists
            lead_data.append(record)

        total_records = len(lead_data)

        return render_template('lead1.html', lead_data=lead_data, total_records=total_records)
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
