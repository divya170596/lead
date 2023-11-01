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
    query = 'SELECT Id,FirstName,LastName,Country__c,AnnualRevenue,Company,Email,Industry,Status,Phone,NumberOfEmployees,Title,Technology_Service__c,Technology__c FROM Lead'
    
    try:
        result = sf.query_all(query)
        total_records = result['totalSize']  # Get the total number of records
        records = result['records']
        lead_data = [record for record in records]
        
        return render_template('lead.html', lead_data=lead_data, total_records=total_records)
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
