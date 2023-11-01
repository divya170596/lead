from flask import Flask, render_template, request, jsonify
#from flask_cors import CORS
from simple_salesforce import Salesforce
import pickle
import pandas as pd
# Import the OneHotEncoder
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics.pairwise import cosine_similarity
import os
import sys
sys.path.append(r'C:\Users\Divya.mehra\OneDrive - ITRadiant Solution Pvt Ltd\Desktop\LeadScore')


app = Flask(__name__)
#CORS(app)


# Initialize the Salesforce client
sf = Salesforce(
    username='ashwini.kahalkar0@itradiant.com.uat',
    password='Sfdc@1234567',
    security_token='2IjGPqcStQmu97r7RTdS8NgV',
    domain='test'
)


encoder = None

# Check if the encoder pickle file exists, and if it does, load it
encoder_pickle_path = 'model\encoder.pkl'
if os.path.exists(encoder_pickle_path):
    with open(encoder_pickle_path, 'rb') as encoder_file:
        encoder = pickle.load(encoder_file)




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

query = 'SELECT FirstName, LastName, Title, Email, Phone, Country__c, Company, Industry, Status, AnnualRevenue, NumberOfEmployees, Technology__c, Technology_Service__c FROM Lead'
lead_data = []
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
        df.to_csv('data/salesforce_data1.csv', index=False)

        # Define features for recommendation based on user input
        selected_features = ['Title', 'Country__c', 'Industry', 'RevenueRange','Technology__c', 'Technology_Service__c']
        df_selected = df[selected_features]

        # Apply one-hot encoding to categorical variables
        encoder = OneHotEncoder()
        df_encoded = encoder.fit_transform(df_selected)

        # Save the encoder to a pickle file (adjust the path as needed)
        with open('model/encoder.pkl', 'wb') as encoder_file:
            pickle.dump(encoder, encoder_file)
        
        total_records = len(records)

    
except Exception as e:
        print(e)


@app.route('/', methods=['GET'])
def lead_form():
    return render_template('index.html')

# Define a route to fetch Lead data from Salesforce and display it in a table format
@app.route('/', methods=['GET','POST'])
def lead_table():
    global encoder
    records = []
    if request.method == 'POST':
        # Process the user input
        user_input = {
            'Title': request.form['Title'],
            'Country__c': request.form['Country'],
            'Industry': request.form['Industry'],
            'RevenueRange': request.form['RevenueRange'],
            'Technology__c': request.form['Technology__c'],
            'Technology_Service__c': request.form['TechnologyServices']
        }

        # Load the dataset
        data_path = 'data\salesforce_data1.csv'
        df = pd.read_csv(data_path) 

        # Populate the 'records' list with lead records
        records = df.to_dict(orient='records')

        # Define features for recommendation based on user input
        selected_features = ['Title', 'Country__c', 'Industry', 'RevenueRange','Technology__c', 'Technology_Service__c']
        df_selected = df[selected_features]

        # Apply one-hot encoding to categorical variables
        encoder = OneHotEncoder()
        df_encoded = encoder.fit_transform(df_selected)
        

        user_input_df = pd.DataFrame([user_input])
        user_input_encoded = encoder.transform(user_input_df[selected_features])
        

        similarity_scores = cosine_similarity(user_input_encoded, df_encoded)

        # Get indices of recommended leads for 'Hot Lead' category
        hot_lead_indices = [i for i, record in enumerate(records) if record['LeadCategory'] == 'Hot Lead']
        num_recommendations = 10

        # Sort indices based on similarity scores and select the top 10 hot leads
        recommended_hot_lead_indices = sorted(hot_lead_indices, key=lambda i: -similarity_scores[0][i])[:num_recommendations]
        # Sort recommended_hot_leads based on 'LeadScoreFinal' in descending order
        # Extract recommended hot leads
        recommended_hot_leads = [records[i] for i in recommended_hot_lead_indices]
        # Sort recommended hot leads based on 'LeadScoreFinal' in descending order
        recommended_hot_leads.sort(key=lambda x: x['LeadScoreFinal'], reverse=True)


        # Define columns for output
        output_columns = ['FirstName', 'LastName', 'Title', 'Email', 'Phone', 'Country__c', 'Company', 'Industry', 'AnnualRevenue', 'NumberOfEmployees', 'Technology__c', 'Technology_Service__c', 'RevenueRange', 'LeadScoreFinal', 'LeadCategory']

        recommended_hot_leads = [{column: record[column] for column in output_columns} for record in recommended_hot_leads]


        # Render the lead_results.html template with user input and recommended leads
        return render_template('lead_results.html', user_input=user_input, recommended_hot_leads=recommended_hot_leads)

if __name__ == '__main__':
    app.run(port=8080)
    