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
    query = 'SELECT FirstName, LastName, Title, Email, Phone, Country__c, Company, Industry, Status, AnnualRevenue, Technology__c, Technology_Service__c FROM Lead'
    
    try:
        result = sf.query_all(query)
        records = result['records']

        # Collect unique values from each column
        unique_title = set()
        unique_country = set()
        unique_industry = set()
        unique_status = set()
        unique_annual_revenue = set()
        unique_technology = set()
        unique_technology_service = set()

        for record in records:
            unique_title.add(record.get('Title'))
            unique_country.add(record.get('Country__c'))
            unique_industry.add(record.get('Industry'))
            unique_status.add(record.get('Status'))
            unique_annual_revenue.add(record.get('AnnualRevenue'))
            unique_technology.add(record.get('Technology__c'))
            unique_technology_service.add(record.get('Technology_Service__c'))

        # Print unique values in the console
        print("Unique Titles:", unique_title)
        print("Unique Countries:", unique_country)
        print("Unique Industries:", unique_industry)
        print("Unique Statuses:", unique_status)
        print("Unique Annual Revenues:", unique_annual_revenue)
        print("Unique Technologies:", unique_technology)
        print("Unique Technology Services:", unique_technology_service)

        total_records = result['totalSize']
        lead_data = [record for record in records]
        
        return render_template('lead1.html', lead_data=lead_data, total_records=total_records)
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
