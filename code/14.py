from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from simple_salesforce import Salesforce
import pickle
import pandas as pd
# Import the OneHotEncoder
from sklearn.preprocessing import OneHotEncoder

print("1")

app = Flask(__name__)
CORS(app)
print("2")

# Initialize the Salesforce client
sf = Salesforce(
    username='ashwini.kahalkar0@itradiant.com.uat',
    password='Sfdc@1234567',
    security_token='2IjGPqcStQmu97r7RTdS8NgV',
    domain='test'
)
print("3")

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
print("4")

# Define a function to calculate lead score based on 'Status', 'Exists', and 'Country'
def calculate_lead_score(status, exists, country,annual_revenue):
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

    revenue_score_factor = {
        # You can adjust this value as needed
        '0 - 500k': 30,  # You can adjust these values as needed
        '500k - 2M': 60,
        '2M - 4M': 90,
        '4M - 6M': 120,
        '6M - 8M': 150,  # You can adjust these values as needed
    }

    lead_score = lead_score_mapping.get((status, exists, country), 0)

    # Calculate the revenue score based on the 'AnnualRevenue' range
    revenue_range = group_annual_revenue(annual_revenue)
    revenue_score = revenue_score_factor.get(revenue_range, 0)

    # Combine the lead score and revenue score
    total_score = lead_score + revenue_score

    return total_score

print("5")
    
    #return lead_score_mapping.get((status, exists, country))

# Define a route to fetch Lead data from Salesforce and display it in a table format
@app.route('/', methods=['GET'])
def lead_table():
    # Query Salesforce to fetch data from the 'Lead' object
    query = 'SELECT FirstName, LastName, Title, Email, Phone, Country__c, Company, Industry, Status, AnnualRevenue, NumberOfEmployees, Technology__c, Technology_Service__c FROM Lead'
    lead_data = []
    print("6")
    try:
        result = sf.query_all(query)
        records = result['records']

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
            annual_revenue=record.get('AnnualRevenue')
            lead_score = calculate_lead_score(status, exists, country,annual_revenue)
            record['LeadScore'] = lead_score

        # Calculate the lead score normalization
        lead_scores = [record.get('LeadScore') for record in records if record.get('LeadScore') is not None]

        if lead_scores:
            max_lead_score = max(lead_scores)
            min_lead_score = min(lead_scores)

            for record in records:
                lead_score = record.get('LeadScore')
                if lead_score is not None:
                    normalized_lead_score = int(100 * (lead_score - min_lead_score) / (max_lead_score - min_lead_score))
                    record['LeadScoreFinal'] = normalized_lead_score
                else:
                    record['LeadScoreFinal'] = None
        else:
            for record in records:
                record['LeadScoreFinal'] = None

        # Categorize leads
        for record in records:
            lead_score_final = record.get('LeadScoreFinal')
            if lead_score_final is not None:
                if lead_score_final > 70:
                    record['LeadCategory'] = 'Hot Lead'
                elif 40 <= lead_score_final <= 69:
                    record['LeadCategory'] = 'Warm Lead'
                else:
                    record['LeadCategory'] = 'Cold Lead'
            else:
                record['LeadCategory'] = 'Uncategorized'

        # Initialize a counter for Hot Leads
        hot_lead_count = 0

        for record in records:
            lead_category = record.get('LeadCategory')
            if lead_category == 'Hot Lead':
                hot_lead_count += 1
        
        # Print the total count of Hot Leads in the console
        print(f'Total Hot Leads: {hot_lead_count}')

                # Save the Salesforce data (records) to a DataFrame
        df = pd.DataFrame(records)

        # Save the DataFrame to a CSV file (Adjust the path as needed)
        df.to_csv('salesforce_data.csv', index=False)

        # Define features for recommendation based on user input
        selected_features = ['Title', 'Country__c', 'Industry', 'RevenueRange','Technology__c', 'Technology_Service__c']
        df_selected = df[selected_features]

        # Apply one-hot encoding to categorical variables
        encoder = OneHotEncoder()
        df_encoded = encoder.fit_transform(df_selected)

        # Save the encoder to a pickle file (adjust the path as needed)
        with open('encoder1.pkl', 'wb') as encoder_file:
            pickle.dump(encoder, encoder_file)

        total_records = len(records)

        return render_template('lead1.html', lead_data=records, total_records=total_records)
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
    