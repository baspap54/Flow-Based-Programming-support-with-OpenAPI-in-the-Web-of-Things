from flask import Flask, jsonify, request, session, render_template, make_response, render_template, redirect, url_for, flash
import json
import os
import random, string
import logging
import sys
import requests
from random import randrange
from markupsafe import escape
from datetime import datetime 
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson import json_util
import socket
from werkzeug.utils import secure_filename
from collections import OrderedDict
import re
app = Flask(__name__) # create an app instance
app.config['MONGO_URI'] = "mongodb://mongo:27017/mongo"
app.config['UPLOAD_EXTENSIONS'] = ['.json', '.yml']
app.secret_key = 'secret_key'
mongo = PyMongo(app)





@app.route("/", methods=['GET'])
def index():
	things_list = mongo.db.things.find()
	return render_template('upload.html', things_list = things_list)


@app.route("/search", methods=['GET','POST'])
def search():
	#thingLoc  = list(mongo.db.things.find()) 
	
	loc = request.form['loc']
	thingLoc = mongo.db.things.find({'info.x-location': loc})
	return render_template('upload.html', thing_loc = thingLoc)

@app.route("/mashup", methods=['GET'])
def mashup():
	apps_list = mongo.db.apps.find()
	return render_template('mashup.html', apps_list = apps_list)

def infoObject(td, userInput, version):
  info = userInput.get("info")
  infoObject = {}
  infoObject = info
  infoObject['version'] = version
  td['info'] = infoObject 


# Create the SOAS description 
@app.route('/generator', methods=['POST'])
def create_oas():
	file_ext = os.path.splitext(request.files['file'].filename)[1]
	if file_ext not in app.config['UPLOAD_EXTENSIONS']:
		flash("This is not an OpenAPI document!")
		return redirect(url_for('index'))
	req = json.load(request.files['file'])
	# Validate the request body contains JSON

	# Parse the JSON into a Python dictionary  

	td = {}
	td['openapi'] = "3.0.3"

	version = req.get("version") # application configuration settings (document version)
	infoObject(td, req, version) # create infoObject for the OpenAPI description 

	# Get Servers, ExternalDocs data from user input 
	externalDocs = req.get("externalDocs")
	servers = req.get("servers")

	if servers: 
	  td['servers'] = servers  # create servers array for the OpenAPI description 

	# service security configuration settings (security schemes)
	securitySchemes = req.get("security_Schemes") 

	# service security configuration settings (security requirements)
	securityReqList = req.get("security_Req_List") 

	if externalDocs: 
	  td['externalDocs'] = externalDocs

	td['security'] = securityReqList # append Security Requirement Object to the document 

	# Get device type (sensor or actuator)
	type_of_thing = req.get("type_of_thing")
	openapiflag = req.get("openapi")
	if openapiflag is None:
		if "sensor" not in type_of_thing:
		  thing_type = 'actuator'
		  supported_actions = req.get("supported_actions") 
		else:
		  thing_type = 'sensor'

		# Get the Properties supported by the device
		supported_properties = req.get("supported_properties")

		# Get user's choice for subscription support (yes or no)
		sub_support = req.get("sub_support") 

		tags = [
		  {
		    "name": "Web Thing",
		    "x-onResource": "'#/components/schemas/Webthing'",
		    "description": "Operations on a Web Thing",
		    "externalDocs": {
		      "description": "Find out more",
		      "url": "https://www.w3.org/Submission/wot-model/#web-thing-resource"
		    }
		  },
		  {
		    "name": "Properties",
		    "description": "Operations on Thing Properties",
		    "externalDocs": {
		      "description": "Find out more about Thing properties",
		      "url": "https://www.w3.org/Submission/wot-model/#properties-resource"
		    }
		  },
		  {
		    "name": "Actions",
		    "description": "Operations on Thing Actions",
		    "externalDocs": {
		      "description": "Find out more about Thing Actions",
		      "url": "https://www.w3.org/Submission/wot-model/#actions-resource"
		    }
		  },
		  {
		    "name": "Subscriptions",
		    "x-onResource": "'#/components/schemas/SubscriptionObject'",
		    "description": "Operations on subscriptions",
		    "externalDocs": {
		      "description": "Find out more about subscriptions",
		      "url": "https://www.w3.org/Submission/wot-model/#things-resource"
		    }
		  }
		]

		paths = {
		  "/": {
		    "get": {
		      "tags": [
		        "Web Thing"
		      ],
		      "summary": "Retrieve Web Thing",
		      "description": "In response to an HTTP GET request on the root URL of a Thing, an Extended Web Thing must return an object that holds its representation.",
		      "operationId": "retrieveWebThing",
		      "responses": {
		        "200": {
		          "description": "OK",
		          "content": {
		            "application/json": {
		              "schema": {
		                "$ref": "#/components/schemas/Webthing"
		              }
		            }
		          }
		        },
		        "404": {
		          "description": "Not found"
		        }
		      }
		    }
		  },
		  "/properties": {
		    "get": {
		      "tags": [
		        "Properties"
		      ],
		      "summary": "Retrieve a list of properties",
		      "description": "In response to an HTTP GET request on the destination URL of a properties link, an Extended Web Thing must return an array of Property that the initial resource contains.",
		      "operationId": "retrieveWebThingProperties",
		      "responses": {
		        "200": {
		          "description": "OK",
		          "content": {
		            "application/json": {
		              "schema": {
		                "type": "array",
		                "items": {
		                  "$ref": "#/components/schemas/PropertiesResponse"
		                }
		              }
		            }
		          }
		        },
		        "400": {
		          "description": "Invalid ID supplied"
		        },
		        "404": {
		          "description": "Not found"
		        }
		      }
		    }
		  }  

		}

		# properties endpoints definition 
		for i in range(len(supported_properties)):
		  device_property = supported_properties[i]
		  retrieve_property_endpoint = {

		    "get": {
		      "tags": [
		        "Properties"
		      ],
		      "summary": "Retrieve the value of a property ("+device_property+")",
		      "description": "In response to an HTTP GET request on a Property URL, an Extended Web Thing must return an array that lists recent values of that Property.",
		      "operationId": "retrieve"+device_property+"Property",
		      "parameters": [
		        {
		          "$ref": "#/components/parameters/pageParam"
		        },
		        {
		          "name": "perPage",
		          "description": "Pagination second (per page) parameter",
		          "in": "query",
		          "required": bool(False),
		          "schema": {
		            "type": "integer"
		          }
		        }
		      ],
		      "responses": {
		        "200": {
		          "description": "successful operation",
		          "content": {
		            "application/json": {
		              "schema": {
		                "type": "array",
		                "items": {
		                  "$ref": "#/components/schemas/"+device_property+"Property"
		                }
		              }
		            }
		          }
		        },
		        "404": {
		          "description": "Not found"
		        }
		      }
		    }

		  }

		  paths['/properties/'+device_property] = retrieve_property_endpoint


		# if the device is a sensor 
		if thing_type != 'actuator': 
		  for i in range(len(tags)): # remove Actions tag 
		    if (i==2):
		      tags.pop(i)
		# if the device is an actuator 
		else:

		  actions_endpoint = {

		      "get": {
		        "tags": [
		          "Actions"
		        ],
		        "summary": "Retrieve a list of actions",
		        "operationId": "retrieveWebThingActions",
		        "responses": {
		          "200": {
		            "description": "OK",
		            "content": {
		              "application/json": {
		                "schema": {
		                  "type": "array",
		                  "items": {
		                    "$ref": "#/components/schemas/Action"
		                  }
		                }
		              }
		            }
		          },
		          "404": {
		            "description": "Not found"
		          }
		        }
		      }

		  }

		  paths['/actions/'] = actions_endpoint

		  for i in range(len(supported_actions)):
		    device_action = supported_actions[i]
		    retrieve_send_execution_endpoint = {

		      "get": {
		        "tags": [
		          "Actions"
		        ],
		        "summary": "Retrieve recent executions of the "+device_action+" action",
		        "description": "In response to an HTTP GET request on an Action URL, an Extended Web Thing must return an array that lists the recent executions of a specific Action.",
		        "operationId": "retrieveRecentExecutionsOf"+device_action+"Action",
		        "responses": {
		          "200": {
		            "description": "successful operation",
		            "content": {
		              "application/json": {
		                "schema": {
		                  "type": "array",
		                  "items": {
		                    "$ref": "#/components/schemas/ActionExecution"
		                  }
		                }
		              }
		            }
		          },
		          "404": {
		            "description": "Not found"
		          }
		        }
		      },
		      "post": {
		        "tags": [
		          "Actions"
		        ],
		        "summary": "Execute a(n) "+device_action+" action",
		        "description": "In response to an HTTP POST request on an Action URL with valid parameters as request body, an Extended Web Thing must either reject the request with the appropriate status code or queue a task to run the action and return the status of that action in a 201 Created response. The action may not run immediately. The Location HTTP header identifies the URL to use to retrieve the most recent update on the action's status.",
		        "operationId": "execute"+device_action+"Action",
		        "responses": {
		          "204": {
		            "description": "NO RESPONSE"
		          },
		          "404": {
		            "description": "Not found"
		          }
		        }
		      }

		    }

		    paths['/actions/'+device_action] = retrieve_send_execution_endpoint

		    retrieve_action_status_endpoint = {

		      "get": {
		        "tags": [
		          "Actions"
		        ],
		        "summary": "Retrieve the status of a "+device_action+" action",
		        "description": "In response to an HTTP GET request on the URL targeted by the Location HTTP header returned in response to the request to execute an action, an Extended Web Thing must return the status of this action or a 404 Not Found status code if the action's status is no longer available.",
		        "parameters": [
		          {
		            "name": "executionId",
		            "in": "path",
		            "description": "action execution of Webthing to return",
		            "required": bool(True),
		            "style": "simple",
		            "explode": bool(True),
		            "schema": {
		              "type": "array",
		              "items": {
		                "type": "integer",
		                "format": "int64",
		                "default": 1
		              }
		            }
		          }
		        ],
		        "responses": {
		          "200": {
		            "description": "OK",
		            "content": {
		              "application/json": {
		                "schema": {
		                  "$ref": "#/components/schemas/ActionExecution"
		                }
		              }
		            }
		          },
		          "404": {
		            "description": "Not found"
		          }
		        }
		      }

		    }

		    paths['/actions/'+device_action+'/{executionId}'] = retrieve_action_status_endpoint

		  # define general /actions schema 
		  action_schema = {

		    "required": [
		      "id",
		      "name"
		    ],
		    "type": "object",
		    "properties": {
		      "id": {
		        "type": "string",
		        "example": "lock"
		      },
		      "name": {
		        "type": "string",
		        "example": "Lock the Smart Door"
		      }
		    },
		    "xml": {
		      "name": "Action"
		    }
		    
		  }  

		if sub_support=='yes':

		  subscriptions_endpoints = {
		    
		    "get": {
		      "tags": [
		        "Subscriptions"
		      ],
		      "summary": "Retrieve a list of subscriptions",
		      "description": "In response to an HTTP GET request on the destination URL of a subscriptions link, an Extended Web Thing must return the array of subscriptions to the underlying resource.",
		      "operationId": "retrieveListOfSubscriptions",
		      "parameters": [
		        {
		          "$ref": "#/components/parameters/pageParam"
		        },
		        {
		          "name": "perPage",
		          "description": "Pagination second (per page) parameter",
		          "in": "query",
		          "required": bool(False),
		          "schema": {
		            "type": "integer"
		          }
		        }
		      ],
		      "responses": {
		        "200": {
		          "description": "OK",
		          "content": {
		            "application/json": {
		              "schema": {
		                "type": "array",
		                "items": {
		                  "$ref": "#/components/schemas/SubscriptionObject"
		                }
		              }
		            }
		          }
		        },
		        "404": {
		          "description": "Not found"
		        }
		      }
		    },
		    "post": {
		      "tags": [
		        "Subscriptions"
		      ],
		      "summary": "Create a subscription",
		      "description": "An Extended Web Thing should support subscriptions for the specific resource (DHT22).",
		      "operationId": "createSubscription",
		      "x-operationType": "https://schema.org/CreateAction",
		      "requestBody": {
		        "description": "Create a new subscription",
		        "content": {
		          "application/json": {
		            "schema": {
		              "$ref": "#/components/schemas/SubscriptionRequestBody"
		            }
		          }
		        },
		        "required": bool(True)
		      },
		      "responses": {
		        "200": {
		          "description": "OK"
		        },
		        "404": {
		          "description": "Not found"
		        }
		      }
		    }
		  
		  } 

		  #append /subscriptions endpoints and operations
		  paths['/subscriptions/'] = subscriptions_endpoints

		  # define /{subscriptionID} endpoints 
		  subscriptionID_endpoints = { 

		    "get": {
		      "tags": [
		        "Subscriptions"
		      ],
		      "summary": "Retrieve information about a specific subscription",
		      "description": "In response to an HTTP GET request on a Subscription URL, an Extended Web Thing must return a JSON representation of the subscription. The JSON representation should be the same as the one returned for that subscription in 'Retrieve a list of subscriptions'.",
		      "operationId": "retreiveInfoAboutSubscription",
		      "parameters": [
		        {
		          "name": "subscriptionID",
		          "in": "path",
		          "description": "The id of the specific subscription",
		          "required": bool(True),
		          "style": "simple",
		          "explode": bool(True),
		          "x-mapsTo": "#/components/schemas/SubscriptionObject.id",
		          "schema": {
		            "type": "string",
		            "example": "5fd23faccde6be05da68bcfb"
		          }
		        }
		      ],
		      "responses": {
		        "200": {
		          "description": "OK",
		          "content": {
		            "application/json": {
		              "schema": {
		                "$ref": "#/components/schemas/SubscriptionObject"
		              }
		            }
		          }
		        },
		        "404": {
		          "description": "Not found"
		        }
		      }
		    },
		    "delete": {
		      "tags": [
		        "Subscriptions"
		      ],
		      "summary": "Delete a subscription",
		      "description": "In response to an HTTP DELETE request on the destination URL of a subscriptions an Extended Web Thing must either reject  the request with an appropriate status code or remove (unsubscribe) the subscription and return a 200 OK status code.",
		      "operationId": "deleteSubscription",
		      "x-operationType": "https://schema.org/DeleteAction",
		      "parameters": [
		        {
		          "name": "subscriptionID",
		          "in": "path",
		          "description": "The id of the specific subscription",
		          "required": bool(True),
		          "style": "simple",
		          "explode": bool(True),
		          "schema": {
		            "type": "string",
		            "example": "5fd23faccde6be05da68bcfb"
		          }
		        }
		      ],
		      "responses": {
		        "200": {
		          "description": "OK"
		        },
		        "404": {
		          "description": "Not found"
		        }
		      }
		    }

		  }

		  #append /subscriptions/{subscriptionID} endpoints and operations
		  paths['/subscriptions/{subscriptionID}'] = subscriptionID_endpoints   

		  #define subscription schemas 
		  subscriptionRequestBody = {

		    "required": [
		      "description",
		      "type",
		      "callbackUrl",
		      "resource"
		    ],
		    "type": "object",
		    "properties": {
		      "name": {
		        "type": "string",
		        "example": "My subscription for SmartDoor's current state"
		      },
		      "description": {
		        "type": "string",
		        "example": "A subscription to get info about SmartDoor's current state"
		      },
		      "type": {
		        "type": "string",
		        "example": "webhook (callback)"
		      },
		      "callbackUrl": {
		        "type": "string",
		        "example": "http://172.16.1.5:5000/accumulate"
		      },
		      "resource": {
		        "type": "object",
		        "properties": {
		          "type": {
		            "type": "string",
		            "example": "property"
		          },
		          "name": {
		            "type": "string",
		            "example": "state"
		          }
		        }
		      },
		      "expires": {
		        "type": "string",
		        "format": "date-time"
		      },
		      "throttling": {
		        "type": "integer",
		        "format": "int32",
		        "example": 5
		      }
		    },
		    "xml": {
		      "name": "SubscriptionRequestBody"
		    }
		  }

		  subscriptionObject = {

		    "allOf": [
		      {
		        "required": [
		          "id",
		          "type",
		          "resource",
		          "description",
		          "callbackUrl"
		        ],
		        "type": "object",
		        "properties": {
		          "id": {
		            "type": "string",
		            "example": "5fc978fc96cc26a4e202c3d6"
		          }
		        }
		      },
		      {
		        "$ref": "#/components/schemas/SubscriptionRequestBody"
		      }
		    ],
		    "xml": {
		      "name": "SubscriptionObject"
		    }
		  } 

		else:
		  for i in range(len(tags)): # remove Subscriptions tag 
		    if (i==3):
		      tags.pop(i)

		parameters = {
		  
		  "pageParam": {
		    "name": "page",
		    "description": "Pagination first (page) parameter",
		    "in": "query",
		    "required": bool(False),
		    "schema": {
		      "type": "integer"
		    }
		  }

		}

		# append tags to the description 
		td['tags'] = tags 
		# append paths to the description 
		td['paths'] = paths 

		webthing_schema = req.get("webthing_schema") # read Web Thing schema from user 

		schemas = {}

		# append Webthing Schema object to schemas 
		schemas['Webthing'] = webthing_schema

		# properties schemas definition 
		for i in range(len(supported_properties)):
		  device_property = supported_properties[i]
		  
		  # read schemas from user input 
		  device_property_measurement_schema = req.get(""+device_property+"MeasurementSchema")
		  device_property_schema = req.get(""+device_property+"Schema")
		  
		  # append two property Schema objects to schemas
		  schemas[''+device_property+''] = device_property_measurement_schema
		  schemas[''+device_property+'Property'] = device_property_schema 

		# actions schemas definition 
		schemas['Action'] = action_schema # append general /actions schema to schemas   

		action_execution_schema = req.get("action_execution_schema") # read action execution schema from user input 
		schemas['ActionExecution'] = action_execution_schema

		# append subscription Schema objects to schemas 
		schemas['SubscriptionRequestBody'] = subscriptionRequestBody
		schemas['SubscriptionObject'] = subscriptionObject

		componentsObject = {} # initialize Components object
		componentsObject['schemas'] = schemas
		componentsObject['parameters'] = parameters 
		componentsObject['securitySchemes'] = securitySchemes # append securitySchemes to Components object 
		td['components'] = componentsObject # append Components object to the document 

		mongo.db.things.insert_one(td)
	else:
		mongo.db.things.insert_one(req)
	flash("Successfully generated OpenAPI description")
	return redirect(url_for('index'))
  
@app.route("/things/<objid>")
def things(objid):
		thing  = mongo.db.things.find_one({'_id': ObjectId(objid)}, {'_id': False})
		#thing  = list(mongo.db.things.find({'_id': ObjectId(objid)}, {'_id': False})) 
		if thing:
			return json_util.dumps(thing)
			#return json.dumps(thing, default=json_util.default)[1:-1]
		else:
			flash("No Thing is stored")
			return redirect(url_for('index'))

@app.route('/mashupload', methods=['POST'])
def mashupload():
	if 'file' in request.files:
		appfile = request.files['file']
		mongo.save_file(appfile.filename, appfile)
		mongo.db.apps.insert_one({'application' : appfile.filename})
	return redirect(url_for('mashup'))
	


@app.route("/applications", methods=['GET'])
def appindex():
	app_list = mongo.db.appopenapi.find()
	return render_template('appupload.html', app_list = app_list)

def find_values(id, json_repr): # find the urls used in the application
    results = []

    def _decode_dict(a_dict):
        try:
            results.append(a_dict[id])
        except KeyError:
            pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict) 
    return results

@app.route('/appgenerator', methods=['POST'])



def create_app_oas():
	file_ext = os.path.splitext(request.files['file'].filename)[1]
	if file_ext not in app.config['UPLOAD_EXTENSIONS']:
		flash("This is not an valid document!")
		return redirect(url_for('appindex'))
	req = json.load(request.files['file'])
	#json_repr = json.dumps(req)
	json_repr= json_util.dumps(req)
	res = []
	appid = "" # initialize to convert list to string
	res = find_values('openApiUrl', json_repr) #openApiUrl is a field in the .json output of Node-RED
	#res = list(dict.fromkeys(res))   # Remove duplicates (we only need the JSON of each thing once!)
	info_dict = {}
	externalDocs_dict = {}
	tags_list_to_dict = {}  			# get thing's tags
	paths_dict = {}				# get thing's paths
	components_dict = {}  # get thing's components
	devices_used = []
	tags_dict = {}
	schemas_dict = {}
	for i in range(len(res)):     # for each url found
		url = ""+res[i]+""					
		lastpart = url.split("/")[-1:] # split it and get the last part which is the _id of the thing in mongoDB
		appid = str(lastpart) # list to str
		thingid = mongo.db.things.find_one({'_id': ObjectId(appid[2:-2])})
		if thingid:

			externalDocs_dict = externalDocs_dict | thingid['externalDocs'] 


			tag_dict = json.dumps(thingid['tags'])
			tag_dict = json.loads(tag_dict)


			tags_list_to_dict = { k : tag_dict[k] for k in range(len(tag_dict)) }

			for k in range(len(tag_dict)):
					tags_dict = list(dict.values(tags_list_to_dict))


			paths_dict = paths_dict | thingid['paths']  # merge dictionaries, doesnt contain duplicates if a thing is used more than once in the same application
			

			components_dict = components_dict | thingid['components']  # merge dictionaries, doesnt contain duplicates if a thing is used more than once in the same application
			schemas_dict = schemas_dict | thingid['components'].get('schemas')

			devices_used.append(thingid['info'].get('title')) # get the devices used (for x-property)
			devices_used = list(dict.fromkeys(devices_used))  # Remove duplicate devices


	
	appl = {}

	appl['openapi'] = "3.0.3"
	appInfoObject = {}
	appInfoObject['title'] = request.form['appTitle']                       #""+str(devices_used)+""	
	appInfoObject['description'] = request.form['appDescription']						#"This is an OpenAPI description for the Node-RED Application!"
	appInfoObject['x-devicesUsed'] = ""+str(devices_used)+""
	appInfoObject['version'] = "1.0.0"
	appl['info'] = appInfoObject

	appl['externalDocs'] = externalDocs_dict

	appl['tags'] = tags_dict

	appl['paths'] = paths_dict

	components_dict['schemas'] = schemas_dict										# update schemas object to contain the combined schemas of the things
	appl['components'] = components_dict

	mongo.db.appopenapi.insert_one(appl)

	return redirect(url_for('appindex'))

	flash("Successfully generated OpenAPI description for the application")
	return redirect(url_for('appindex'))

@app.route("/appdesc/<objid>")
def appdesc(objid):
		appdescr  = mongo.db.appopenapi.find_one({'_id': ObjectId(objid)}, {'_id': False})

		if appdescr:
			return json_util.dumps(appdescr)
			#return json.dumps(appdescr, default=json_util.default)[1:-1]
		else:
			flash("No Thing is stored")
			return redirect(url_for('appindex'))



if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5000, debug=True)
