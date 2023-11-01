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

        total_records = result['totalSize']
        lead_data = [record for record in records]

        # Create a dictionary to track how 'Technology_Service__c' is related to 'Technology__c'
        technology_service_relationships = {}

        for record in lead_data:
            technology_service = record.get('Technology_Service__c')
            technology = record.get('Technology__c')

            if technology_service in technology_service_relationships:
                technology_service_relationships[technology_service].add(technology)
            else:
                technology_service_relationships[technology_service] = {technology}

        # Print the relationships in the console
        print("Technology Service Relationships:")
        for service, technologies in technology_service_relationships.items():
            print(f"{service}: {', '.join(technologies)}")

        return render_template('lead1.html', lead_data=lead_data, total_records=len(lead_data))
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
