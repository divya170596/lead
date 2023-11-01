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

        # Collect unique 'Status' values
        unique_status = set()
        for record in records:
            unique_status.add(record.get('Status'))

        # Print unique 'Status' values in the console
        print("Unique Statuses:", unique_status)

        # Find the index of a specific 'Status' value
        target_status = "CurrentRow.Item(4).ToString"
        target_status_indices = []
        for index, record in enumerate(records):
            status_value = record.get('Status')
            if status_value == target_status:
                target_status_indices.append(index)

        # Print the indices of records where the target status is present
        if target_status_indices:
            print(f"'{target_status}' is present in the 'Status' column in the following records:")
            for index in target_status_indices:
                print(f"Record at index {index}: {records[index]}")
        else:
            print(f"'{target_status}' is not present in the 'Status' column.")

        total_records = result['totalSize']
        lead_data = [record for record in records]
        
        return render_template('lead1.html', lead_data=lead_data, total_records=total_records)
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
