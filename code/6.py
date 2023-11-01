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

        return render_template('lead1.html', lead_data=lead_data)
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
