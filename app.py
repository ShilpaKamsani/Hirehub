from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import boto3
import config
s3 = boto3.client('s3')
response = s3.list_buckets()
app = Flask(__name__)
sns_client = boto3.client('sns', region_name='us-east-1')
topic_arn = 'arn:aws:sns:us-east-1:269269334576:hirehubtopic'
#response = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)

# connect to the MySQL database

mydb = mysql.connector.connect(
    host=config.RDS_HOSTNAME,
    user=config.RDS_USERNAME,
    password=config.RDS_PASSWORD,
    database=config.RDS_DB_NAME
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
        #cursor = mysql.connection.cursor()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM job_postings WHERE job_title LIKE %s", (f"%{search_query}%",))
        results = cursor.fetchall()
        cursor.close()
        return render_template("search_results.html", search_query=search_query, results=results, num_results=len(results))
    else:
        # Render the search template
        return render_template("search.html")
        

@app.route('/submit', methods=['GET','POST'])
def submit():
    if request.method == 'POST':
        id = request.form['id']
        job_title = request.form['job_title']
        job_description = request.form['job_description']
        company_name = request.form['company_name']
        location = request.form['location']
        salary = request.form['salary']
        expiration_date = request.form['expiration_date']


    # insert data into the MySQL database
        mycursor = mydb.cursor()
        sql = "INSERT INTO job_postings (id, job_title, job_description, company_name, location, salary, expiration_date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = (id, job_title, job_description, company_name, location, salary, expiration_date)
        mycursor.execute(sql, val)
        mydb.commit()
# Print the bucket names
        for bucket in response['Buckets']:
            print(bucket['Name'])
# Upload the job posting to S3
        bucket_name = 'hirehubbucket'
        key = f"{id}-{job_title}-{company_name}"
        content = f"Job_Id: {id}\nJob Title: {job_title}\nJob Description: {job_description}\nCompany Name: {company_name}\nLocation: {location}\nSalary: {salary}\nExpiration Date: {expiration_date}"
        s3.put_object(Bucket=bucket_name, Key=key, Body=content)
    
        form_data = {'id': id, 'job_title': job_title, 'job_description': job_description, 'company_name': company_name, 'location': location, 'salary': salary, 'expiration_date': expiration_date}
        return redirect(url_for('success', data=form_data))
        

    else:
        # If the request method is GET, show the form
        return render_template('submit.html')
        
#@app.route('/success')
#@app.route('/success/<id>/<job_title>/<job_description>/<company_name>/<location>/<salary>/<expiration_date>')
@app.route('/success')
def success():
    form_data = request.args.get('data')
    form_data = eval(form_data)
    id = form_data['id']
    job_title = form_data['job_title']
    job_description = form_data['job_description']
    company_name = form_data['company_name']
    location = form_data['location']
    salary = form_data['salary']
    expiration_date = form_data['expiration_date']
    return render_template('success.html', id=id, job_title=job_title, job_description=job_description, company_name=company_name, location=location, salary=salary, expiration_date=expiration_date)

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        age = request.form['age']
        city = request.form['city']
        date = request.form['date']
        email = request.form['email']
        cur = mydb.cursor()
        cur.execute("INSERT INTO jobs (id, name, age, city, date, email) VALUES (%s, %s, %s, %s, %s, %s)", (id, name, age, city, date, email))
        mydb.commit()  
        cur.close()
#subscription_response = None
        already_subscribed = False
        subscription_response = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
        for subscription in subscription_response['Subscriptions']:
            if subscription['Protocol'] == 'email' and subscription['Endpoint'] == email:
                target_arn = subscription['SubscriptionArn']
                already_subscribed = True
                break
        # If the applicant is not already subscribed, subscribe them to the topic
        if not already_subscribed:
            response1 = sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email,
                ReturnSubscriptionArn=True
            )
            target_arn = response1['SubscriptionArn']
        # Publish a message to the topic
        message = f'Job application submitted for job ID {id} by {name} on {date}'
        sns_client.publish(TopicArn=topic_arn, Message=message, Subject='New Job Application')
        
        return redirect(url_for('successjobsubmit', id=id, name=name, age=age, city=city, date=date, email=email))
        
        
    else:
        id = request.args.get('id')
        name = request.args.get('name')
        age = request.args.get('age')
        city = request.args.get('city')
        date = request.args.get('date')
        # If the request method is GET, show the form
        return render_template('apply.html',id=id)
    
@app.route('/successjobsubmit/<id>/<name>/<age>/<city>/<date>/<email>')
def successjobsubmit(id, name, age, city, date, email):
        return render_template('successjobsubmit.html', id=id, name=name, age=age, city=city, date=date, email=email)

if __name__ == '__main__':
        app.run(debug=True,host='0.0.0.0',port=6000)
