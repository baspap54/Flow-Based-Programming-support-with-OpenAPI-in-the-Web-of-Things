from flask import Flask, jsonify, request, session, render_template, make_response 
import json
import random, string
import logging
import sys
import requests
from random import randrange
from markupsafe import escape
from datetime import datetime 

app = Flask(__name__) # create an app instance
logging.basicConfig(level=logging.DEBUG)   


### API routes 


# Retrieve a Web Thing 
@app.route('/<webthing>/', methods=['GET'])
def retrieve_wt(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"?type=Thing&options=keyValues"

  payload={}
  headers = {
    'Link': '<model/>; rel="model"' 
  }
  response = requests.request("GET", url, headers=headers, data=payload)
  resp = json.loads(response.text)

  if "type" not in (resp):
    return (resp, 404, {'Content-Type': 'application/json'})
  else:
    del resp['type'] 
    return (resp)



# Update a Web Thing 
@app.route('/<webthing>/', methods=['PUT'])
def update_wt(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  # Validate the request body contains JSON   
  if request.is_json:

    url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"/attrs/?type=Thing&options=keyValues"
    payload = request.data                          
    headers = {
    }
    response = requests.request("PATCH", url, headers=headers, data=payload)
    resp = make_response("NO CONTENT", 204)
    return (resp)

     

# Retrieve the model of a Thing
@app.route('/<webthing>/model', methods=['GET'])
def retrieve_wtmodel(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"?type=Model&options=keyValues"

  payload={}
  headers = {}

  response = requests.request("GET", url, headers=headers, data=payload)

  resp = json.loads(response.text)
  del resp['type'] 
  return (resp)



# Update the model of a Thing 
@app.route('/<webthing>/model', methods=['PUT'])
def update_wtmodel(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  # Validate the request body contains JSON   
  if request.is_json:

    url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"/attrs/?type=Model&options=keyValues"
    payload = request.data                          
    headers = {
      'Content-Type': 'application/json'  
    }
    response = requests.request("PATCH", url, headers=headers, data=payload)

  return (response.text)



# Retrieve a list of properties
@app.route('/<webthing>/properties', methods=['GET'])
def retrieve_properties(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  url = "http://172.16.1.7:1026/v2/entities?type=property&q=Thing=='"+wt_name+"'"

  querystring = {"options":"keyValues"}

  response = requests.request("GET", url, params=querystring)
  resp = str(response.text)
  json_data = json.loads(resp)

  for y in json_data:
    del y['Thing'] 
    del y['type'] 
    del y['property'] 

  return (json.dumps(json_data), 200, {'Content-Type': 'application/json'})



# Retrieve the value of a property
@app.route('/<webthing>/properties/<propertyID>', methods=['GET'])
def retrieve_prop_value(webthing,propertyID):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)
  # the input name of the property
  prop = escape(propertyID)
  prop = str(prop)

  url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"_"+prop+"/attrs/values/value?type=property&q=Thing=='"+wt_name+"'&options=keyValues"
  payload={}
  headers = {}

  response = requests.request("GET", url, headers=headers, data=payload)
  resp = str(response.text)
  resp = json.loads(resp)
  
  return (resp, 200, {'Content-Type': 'application/json'})



# Update a specific property 
@app.route('/<webthing>/properties/<propertyID>', methods=['PUT'])
def update_property(webthing,propertyID):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)
  # the input name of the property
  prop = escape(propertyID)
  prop = str(prop)

  # Validate the request body contains JSON  
  if request.is_json:

    url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"_"+prop+"/attrs/values/value?q=Thing=='"+wt_name+"'"
    
    payload = request.data
    headers = {
      'content-type': "application/json",
      'cache-control': "no-cache",
      'postman-token': "708926ee-9996-2bc2-0b7e-6d29c4668bf4"
    }

    response = requests.request("PUT", url, data=payload, headers=headers)

    resp = make_response("NO CONTENT", 204)
    resp.headers['Location'] = 'http://localhost:5000/'+wt_name+'/properties/'+prop+''

    return resp



# Update multiple properties at once
@app.route('/<webthing>/properties', methods=['PUT'])
def update_mult_properties(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  # Validate the request body contains JSON  
  if request.is_json:

    url = "http://172.16.1.7:1026/v2/op/update?options=keyValues"
    
    payload = request.data
    headers = {
      'content-type': "application/json",
      'cache-control': "no-cache",
      'postman-token': "708926ee-9996-2bc2-0b7e-6d29c4668bf4"
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    if "error" in (response.text):
      resp = make_response("Invalid input", 400)
      return resp

    else:
      resp = make_response("NO CONTENT", 204)
      resp.headers['Location'] = 'http://localhost:5000/'+wt_name+'/properties'
      return resp



# Retrieve a list of actions
@app.route('/<webthing>/actions', methods=['GET'])
def retrieve_actions(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"_actions/attrs/actions/value?type=actions&options=keyValues"
  payload={}
  headers = {}

  response = requests.request("GET", url, headers=headers, data=payload)
  json_data = str(response.text)
  json_data = json.loads(json_data)

  if "error" in (response.text):
    resp = make_response("Not found", 404)
    return resp
  else:
    return (json.dumps(json_data), 200, {'Content-Type': 'application/json'})



# Retrieve recent executions of a specific action
@app.route('/<webthing>/actions/<actionID>', methods=['GET'])
def retrieve_recent_action_exec(webthing,actionID):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)
  # the input name of the action
  action_name = escape(actionID)
  action_name = str(action_name)

  #url = "http://172.16.1.7:1026/v2/entities?type=execution&q=action=='"+wt_name+"'&q=Thing=='"+wt_name+"'&options=keyValues"
  url = "http://172.16.1.7:1026/v2/entities?type=execution&q=action=='"+action_name+"'&q=Thing=='"+wt_name+"'&options=keyValues"

  payload={}
  headers = {}

  response = requests.request("GET", url, headers=headers, data=payload)

  return (response.text, 200, {'Content-Type': 'application/json'})



# # Execute an action
# @app.route('/<webthing>/actions/<actionID>', methods=['POST'])
# def execute_action(webthing,actionID):

#   # the input name of the Thing
#   wt_name = escape(webthing)
#   wt_name = str(wt_name)
#   # the input name of the action
#   action_name = escape(actionID)
#   action_name = str(action_name)

#   # Validate the request body contains JSON
#   if request.is_json:

#     # Parse the JSON into a Python dictionary  
#     req = request.data 

#     new_id = random.randint(1,10000)

#     url = "http://172.16.1.7:1026/v2/entities?options=keyValues"
#     data = json.loads(req) 
#     data["id"] = ""+str(new_id)+"" # append new id to the input JSON body including the action execution 
#     payload = data 
#     headers = {
#       'Content-Type': 'application/json'
#     }
#     #response = requests.post(url, json=payload)
#     response = requests.request("POST", url, data=payload, headers=headers)
#     # if id already taken, try again 
#     while (response.status_code) != 201:

#       new_id = random.randint(1,10000) 
#       new_id = int(new_id) + 10000

#       url = "http://172.16.1.7:1026/v2/entities?options=keyValues"
#       data = json.loads(req) 
#       data['id'] = ""+str(new_id)+"" # append new id to the input JSON body including the action execution 
#       payload = data 
#       headers = {
#         'Content-Type': 'application/json'
#       }
#       response = requests.post(url, json=payload)

#     # return response code and header 
#     resp = make_response("NO RESPONSE", 204)
#     resp.headers['Location'] = "http://172.16.1.1:5002/"+wt_name+"/actions/"+action_name+"/"+str(new_id)+""
#     return resp
# Execute an action
# @app.route('/<webthing>/actions/<actionID>', methods=['POST'])
# def execute_action(webthing,actionID):

#   # the input name of the Thing
#   wt_name = escape(webthing)
#   wt_name = str(wt_name)
#   # the input name of the action
#   action_name = escape(actionID)
#   action_name = str(action_name)

#   # Validate the request body contains JSON
#   if request.is_json:

#     # Parse the JSON into a Python dictionary  
#     req = request.data 

#     new_id = random.randint(1,10000)

#     url = "http://172.16.1.7:1026/v2/entities?options=keyValues"
#     data = json.loads(req) 
#     data['id'] = new_id # append new id to the input JSON body including the action execution 
#     payload = data 
#     headers = {
#       'Content-Type': 'application/json'
#     }
#     response = requests.post(url, json=payload)

#     # if id already taken, try again 
#     # #while (response.status_code) != 201:

#     # # new_id = random.randint(1,10000) 
#     # # new_id = int(new_id) + 10000

#     # url = "http://172.16.1.7:1026/v2/entities?options=keyValues"
#     # data = json.loads(req) 
#     # data['id'] = ""+str(new_id)+"" # append new id to the input JSON body including the action execution 
#     # payload = data 
#     # headers = {
#     #   'Content-Type': 'application/json'
#     # }
#     # response = requests.post(url, json=payload)

#     # return response code and header 
#     resp = make_response("NO RESPONSE", 204)
#     resp.headers['Location'] = "http://172.16.1.1:5002/"+wt_name+"/actions/"+action_name+"/"+str(new_id)+""
#     return resp


# Add a Web Thing to a gateway
@app.route('/<webthing>/action', methods=['POST'])
def execute_action(webthing):

  # Validate the request body contains JSON
  if request.is_json:

    url = "http://172.16.1.7:1026/v2/entities?options=keyValues"
    
    payload = request.data
    req = request.get_json()
    wt_id = req.get("id")
    headers = {
      'content-type': "application/json",
      'cache-control': "no-cache",
      'postman-token': "708926ee-9996-2bc2-0b7e-6d29c4668bf4"
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    resp = make_response("NO CONTENT", 204)
   # resp.headers['Location'] = 'http://localhost:5000/'+wt_id+''

    return resp






# Retrieve the status of an action
@app.route('/<webthing>/actions/<actionID>/<execution_id>', methods=['GET'])
def retrieve_action_status(webthing,actionID,execution_id):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)
  # the input name of the action
  action_name = escape(actionID)
  action_name = str(action_name)
  # the input action_execution id 
  execution_id = escape(execution_id)
  execution_id = str(execution_id)

  url = "http://172.16.1.7:1026/v2/entities/"+execution_id+"?type=execution&options=keyValues"

  payload={}
  headers = {}

  response = requests.request("GET", url, headers=headers, data=payload)

  if ""+wt_name+"" not in response.text:
    return ("ERROR: There is no such action ID for this Thing!", 404)
  else: 
    return (response.text, 200, {'Content-Type': 'application/json'})



# Retrieve a list of Web Things
@app.route('/<webthing>/things', methods=['GET'])
def retrieve_all_things(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"?type=Thing&options=keyValues"

  payload={}
  headers = {}
  response = requests.request("GET", url, headers=headers, data=payload)
  resp = json.loads(response.text)

  if "error" in (resp):
    return (resp, 404, {'Content-Type': 'application/json'})
  else:

    url = "http://172.16.1.7:1026/v2/entities/"
    querystring = {"type":"Thing","options":"keyValues"}
    headers = {
      'cache-control': "no-cache",
      'postman-token': "2f969f77-cf3e-5b18-988c-9963a7a742bc"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    return (response.text, 200, {'Content-Type': 'application/json'})



# Add a Web Thing to a gateway
@app.route('/<webthing>/things', methods=['POST'])
def add_webthing(webthing):

  # Validate the request body contains JSON
  if request.is_json:

    url = "http://172.16.1.7:1026/v2/entities?options=keyValues"
    
    payload = request.data
    req = request.get_json()
    wt_id = req.get("id")
    headers = {
      'content-type': "application/json",
      'cache-control': "no-cache",
      'postman-token': "708926ee-9996-2bc2-0b7e-6d29c4668bf4"
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    resp = make_response("NO CONTENT", 204)
    resp.headers['Location'] = 'http://localhost:5000/'+wt_id+''

    return resp




# Create a subscription
@app.route('/<webthing>/subscriptions', methods=['POST'])
def create_subscription(webthing):

  # Validate the request body contains JSON
  if request.is_json:

    url = "http://172.16.1.7:1026/v2/subscriptions"
    payload = request.data

    headers = {
      'content-type': "application/json",
      'cache-control': "no-cache",
      'postman-token': "708926ee-9996-2bc2-0b7e-6d29c4668bf4"
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    headers = response.headers
    resp = make_response("OK", 200)
    resp.headers['Subscription-ID'] = headers # we need to return the header with the new subscription ID 

    return (resp)




# Retrieve a list of subscriptions
@app.route('/<webthing>/subscriptions', methods=['GET'])
def retrieve_subscriptions(webthing):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  url = "http://172.16.1.7:1026/v2/entities/"+wt_name+"/attrs/tags/value?type=Model&options=keyValues"

  payload={}
  headers = {}
  response = requests.request("GET", url, headers=headers, data=payload)

  response = json.loads(response.text) 

  data = []

  for i in range(len(response)): 

    url = "http://172.16.1.7:1026/v2/subscriptions/"+response[i]+"?options=keyValues"

    payload={}
    headers = {}
    resp = requests.request("GET", url, headers=headers, data=payload)
    resp = json.loads(resp.text)
    data.append(resp)

  return (json.dumps(data), {'Content-Type': 'application/json'})  





# Retrieve information about a specific subscription
@app.route('/<webthing>/subscriptions/<subscriptionID>', methods=['GET'])
def retrieve_specific_sub(webthing,subscriptionID):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  # the input name of the Thing
  subID = escape(subscriptionID)
  subID = str(subID)

  url = "http://172.16.1.7:1026/v2/subscriptions/"+subID+""
  response = requests.request("GET", url)

  if "error" in response.text:
    resp = make_response("ERROR 404: NOT FOUND", 404)
    return (resp)
  else: 
    return (response.text)



# Delete a subscription
@app.route('/<webthing>/subscriptions/<subscriptionID>', methods=['DELETE'])
def delete_sub(webthing,subscriptionID):

  # the input name of the Thing
  wt_name = escape(webthing)
  wt_name = str(wt_name)

  # the input name of the Thing
  subID = escape(subscriptionID)
  subID = str(subID)

  url = "http://172.16.1.7:1026/v2/subscriptions/"+subID+""

  response = requests.request("DELETE", url)

  return (response.text)



# accumulate (for subscriptions)
@app.route('/accumulate', methods=['POST'])
def accumulate():

  # Validate the request body contains JSON
  if request.is_json:

    payload = request.data
    req = request.get_json()

    resp = make_response("NO CONTENT", 204)

    return resp




    
if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5000, debug=True)

