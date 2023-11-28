import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from couchbase.exceptions import DocumentExistsException
from src.cb import CouchbaseClient
from flask import Flask, request
from flask_restx import Api, Resource, fields

from mailjet_rest import Client

app = Flask(__name__)

env_path = "./src/.env"
load_dotenv(env_path)

senderMail = os.getenv("SENDER_MAIL")
mailjet = Client(auth=(os.getenv("API_KEY"), os.getenv("API_SECRET")), version='v3.1')
api = Api(app)
nsProduct = api.namespace("api/v1/email", "Send Email")

emailInsert = api.model(
    "emailInsert",
    {
        "orderId": fields.String(required=True, description="Order ID"),
        "name": fields.String(required=True, description="Name of Customer"),
        "mailId": fields.String(required=True, description="Mail Id of customer"),
        "totalCost" : fields.Float(required=True, description="Total cost of order"),
    },
)

emailResponse = api.model(
    "emailResponse",
    {
        "id": fields.String(required=True, description="Audit for email sent"),
        "orderId": fields.String(required=True, description="Order ID"),
        "mailId": fields.String(required=True, description="Mail Id of customer"),
        "status" : fields.String(required=True, description="Email Status"),
        "deliveredAt" : fields.String(required=True, description="Time email is delivered"),
        "statusCode" : fields.Integer(required=True, description="Status code of SMTP")
    },
)


@nsProduct.route("/sendMail")
class Email(Resource):
    # tag::post[]
    @nsProduct.doc(
        "Send Email",
        reponses={200: "Success", 500: "Unexpected Error"},
    )
    @nsProduct.expect(emailInsert, validate=True)
    @nsProduct.marshal_with(emailResponse)
    def post(self):
        reqData = request.json
        print(reqData)
        data = {
                'Messages': [
                    {
                        "From": {
                            "Email": senderMail,
                            "Name": senderMail
                        },
                        "To": [
                            {
                                "Email": reqData["mailId"],
                                "Name": reqData["name"]
                            }
                        ],
                        "Subject": "Greetings from DealBazaar",
                        "TextPart": f"Your Order {reqData['orderId']} successfully placed !",
                        "HTMLPart": f"<h3>Dear {reqData['name']} , Your order {reqData['orderId']} is successfully placed and the total amount of the order is {reqData['totalCost']} .Thank you for shopping with DealBazaar!"
                    }
                ]
            }
        response = {}
        rep = mailjet.send.create(data=data)
        if rep.status_code==200:
            response["status"] = "SUCCESS"
            response["deliveredAt"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        else:
            response["status"] = "FAILURE"
            response["deliveredAt"] = None
        id = uuid.uuid4().__str__()
        response["id"] = id
        response["mailId"] = reqData["mailId"]
        response["orderId"] = reqData["orderId"]
        response["statusCode"] = rep.status_code
        try :
            cb.insert(id, response)
            return response, 202
        except DocumentExistsException:
            return "Key already exists", 409
        except Exception as e:
            return f"Unexpected error: {e}", 500

db_info = {
    "host": os.getenv("DB_HOST"),
    "bucket": os.getenv("BUCKET"),
    "scope": os.getenv("SCOPE"),
    "collection": os.getenv("COLLECTION"),
    "username": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD")
}

cb = CouchbaseClient(*db_info.values())
cb.connect()

if __name__ == "__main__":
    app.run(debug=True,port=5004)