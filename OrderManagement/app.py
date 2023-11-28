import os
import uuid
import requests
from datetime import datetime
from dotenv import load_dotenv
from couchbase.exceptions import (
    CouchbaseException,
    DocumentExistsException,
    DocumentNotFoundException,
)
from src.cb import CouchbaseClient
from flask import Flask, request
from flask_restx import Api, Resource, fields

app = Flask(__name__)

env_path = "./src/.env"
load_dotenv(env_path)

api = Api(app)
nsOrder = api.namespace("api/v1/orders", "CRUD operations for Orders")

contact = api.model(
    "Contact",
    {
        "name": fields.String(required=True, description="Customer Name"),
        "emailId": fields.String(required=True, description="emailId of customer"),
        "phone": fields.String(required=True, description="Phone number of customer"),
        "address": fields.String(required=True, description="Address of customer")
    },
)

product = api.model(
    "Product",
    {
        "productName": fields.String(required=True, description="Product Name"),
        "productId": fields.String(required=True, description="Product's Unique ID"),
        "price": fields.Float(required=True, description="Product Price"),
        "tax": fields.Float(required=True, description="Product tax percentage"),
        "quantity" : fields.Integer(required=True,description="Item count")
    },
)

orderInsert = api.model(
    "orderInsert",
    {
        "orderItems": fields.List(fields.Nested(product)),
        "contact": fields.Nested(contact)
    },
)

order = api.model(
    "Order",
    {
        "id": fields.String(required=True, description="Product's system generated Id"),
        "orderId": fields.String(required=True, description="Order Id"),
        "orderItems": fields.List(fields.Nested(product)),
        "contact": fields.Nested(contact),
        "totalCost": fields.Float(required=True, description="Total cost of order"),
        "submittedAt" : fields.String(required=True, description="Time order is submitted"),
    },
)

@nsOrder.route("/submitOrder")
class Orders(Resource):

    @nsOrder.doc(
        "Create Product",
        reponses={200: "Success", 409: "Key alreay exists", 500: "Unexpected Error"},
    )
    @nsOrder.expect(orderInsert, validate=True)
    @nsOrder.marshal_with(order)
    def post(self):
        try:
            data = request.json
            print(data)
            data["id"] = uuid.uuid4().__str__()
            data["submittedAt"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            orderId = cb.get(os.getenv("ORDERID_KEY"))
            cb.upsert( os.getenv("ORDERID_KEY"), orderId.value+1)
            orderId = "ORD-"+str(orderId.value)
            data["orderId"] = orderId
            totalCost=0
            for cost in data["orderItems"]:
                totalCost += (cost["price"] * cost["quantity"]) + (cost["price"] * (cost["tax"])/100) * cost["quantity"]
            data["totalCost"] = totalCost
            cb.insert(orderId, data)
            requestData={}
            requestData["orderId"] = data["orderId"]
            requestData["name"] = data["contact"]["name"]
            requestData["mailId"] = data["contact"]["emailId"]
            requestData["totalCost"] = data["totalCost"]
            url = "http://"+os.getenv("NG_BASEURL")+":"+os.getenv("NG_PORT")+os.getenv("NG_URL")
            response = requests.post(url,json=requestData)
            return data, 200
        except DocumentExistsException:
            return "Key already exists", 409
        except CouchbaseException as e:
            return f"Unexpected error: {e}", 500
        except Exception as e:
            return f"Unexpected error: {e}", 500

@nsOrder.route("/<orderId>")
class ProductId(Resource):
    @nsOrder.doc(
        "Get Profile",
        reponses={200: "Document Found", 404: "Document Not Found", 500: "Unexpected Error"},
    )
    def get(self, orderId):
        try:
            result = cb.get(orderId)
            return result.value ,200
        except DocumentNotFoundException:
            return "Key not found", 404
        except CouchbaseException as e:
            return f"Unexpected error: {e}", 500

db_info = {
    "host": os.getenv("DB_HOST"),
    "bucket": os.getenv("BUCKET"),
    "scope": os.getenv("SCOPE"),
    "collection": os.getenv("COLLECTION"),
    "username": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD"),
}

cb = CouchbaseClient(*db_info.values())
cb.connect()
try:
   cb.get(os.getenv("ORDERID_KEY"))
except DocumentNotFoundException:
    cb.insert(os.getenv("ORDERID_KEY"),int(os.getenv("ORDERID_BASE")))

if __name__ == "__main__":
    app.run(debug=True,port=5003)