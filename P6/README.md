
# Project 6: Identify Fraud from Enron Email

This is Udacity's Data Analyst Nanodegree project work for Machine Learning part.

It was to build a machine learning algorithm to identify Enron Employees who may have committed fraud based on the public Enron financial and email data set.

## Environments

Anaconda with Python 2.7.12
* [Evironment for Mac](https://github.com/mellamoorzar/Udacity_DAND/blob/master/Evironments/dand-env-mac.yaml)
* [Evironment for Windows](https://github.com/mellamoorzar/Udacity_DAND/blob/master/Evironments/dand-env-win.yaml)

Jupyter Notebook

## File List

**Main Report:**

[Report.ipynb](Report.ipynb)

**Main Code:**

Directory: `/final_project`

[poi_id.ipynb](final_project/poi_id.ipynb)

**Python Scripts:**

Directory: `/tools`

* feature_format.py - A general tool for converting data from the dictionary format to an (n x k) python list that's ready for training an sklearn algorithm.

* tester.py - A basic script for importing student's POI identifier, and checking the results that they get from it.

**Data:**

Directory: `/final_project`

final_project_dataset.pkl - This data set contains features fall into three major types: financial features, email features and POI labels.

financial features:

* salary
* deferral_payments
* total_payments
* loan_advances
* bonus
* restricted_stock_deferred
* deferred_income
* total_stock_value
* expenses
* exercised_stock_options
* other
* long_term_incentive
* restricted_stock
* director_fees

email features: 
* to_messages
* email_address
* from_poi_to_this_person
* from_messages
* from_this_person_to_poi
* shared_receipt_with_poi

POI label:
* poi: boolean value represented as integer
