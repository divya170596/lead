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

# Define a function to calculate lead score based on 'Status', 'Exists', and 'Country'
def calculate_lead_score(status, exists, country):
    lead_score_mapping = {
        ('Unqualified', 'Yes', 'USA'): 10,
        ('Open', 'Yes', 'USA'): 20,
        ('Contacted', 'Yes', 'USA'): 30,
        ('Qualified', 'Yes', 'USA'): 40,
        ('Unqualified', 'No', 'USA'): 90,
        ('Open', 'No', 'USA'): 100,
        ('Contacted', 'No', 'USA'): 110,
        ('Qualified', 'No', 'USA'): 120,
        ('Unqualified', 'Yes', 'IN'): 50,
        ('Open', 'Yes', 'IN'): 60,
        ('Contacted', 'Yes', 'IN'): 70,
        ('Qualified', 'Yes', 'IN'): 80,
        ('Unqualified', 'No', 'IN'): 130,
        ('Open', 'No', 'IN'): 140,
        ('Contacted', 'No', 'IN'): 150,
        ('Qualified', 'No', 'IN'): 160
    }
    
    return lead_score_mapping.get((status, exists, country))

# Define a route to fetch Lead data from Salesforce and display it in a table format
@app.route('/', methods=['GET'])
def lead_table():
    # Query Salesforce to fetch data from the 'Lead' object
    query = 'SELECT FirstName, LastName, Title, Email, Phone, Country__c, Company, Industry, Status, AnnualRevenue, NumberOfEmployees, Technology__c, Technology_Service__c FROM Lead'
    lead_data = []
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

            # Calculate the lead score based on 'Status', 'Exists', and 'Country'
            status = record.get('Status')
            country = record.get('Country__c')
            lead_score = calculate_lead_score(status, exists, country)
            record['LeadScore'] = lead_score

            lead_data.append(record)



        # Collect unique values from each column
        unique_title = set()
        unique_country = set()
        unique_industry = set()
        unique_status = set()
        unique_Revenue_Range = set()
        unique_technology = set()
        unique_technology_service = set()

        for record in records:
            unique_title.add(record.get('Title'))
            unique_country.add(record.get('Country__c'))
            unique_industry.add(record.get('Industry'))
            unique_status.add(record.get('Status'))
            unique_Revenue_Range.add(record.get('RevenueRange'))
            unique_technology.add(record.get('Technology__c'))
            unique_technology_service.add(record.get('Technology_Service__c'))

         # Print unique values in the console
        print("Unique Titles:", unique_title)
        print("Unique Countries:", unique_country)
        print("Unique Industries:", unique_industry)
        print("Unique Statuses:", unique_status)
        print("Unique Revenue Range:", unique_Revenue_Range)
        print("Unique Technologies:", unique_technology)
        print("Unique Technology Services:", unique_technology_service)

        max_lead_score = max(record['LeadScore'] for record in lead_data)
        min_lead_score = min(record['LeadScore'] for record in lead_data)

        for record in lead_data:
            lead_score = record.get('LeadScore')
            normalized_lead_score = round(100 * (lead_score - min_lead_score) / (max_lead_score - min_lead_score))
            record['LeadScoreFinal'] = normalized_lead_score

        # Categorize leads into Hot, Warm, and Cold
            for record in lead_data:
                lead_score_final = record.get('LeadScoreFinal')
                if lead_score_final > 70:
                    record['LeadCategory'] = 'Hot Lead'
                elif 40 <= lead_score_final <= 69:
                    record['LeadCategory'] = 'Warm Lead'
                else:
                    record['LeadCategory'] = 'Cold Lead'

        


        total_records = len(lead_data)

        return render_template('lead1.html', lead_data=lead_data, total_records=total_records, 
                               unique_title=unique_title, unique_country=unique_country,
                               unique_industry=unique_industry, unique_status=unique_status,
                               unique_annual_revenue=unique_Revenue_Range, unique_technology=unique_technology,
                               unique_technology_service=unique_technology_service)
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
