import os
import uuid
from datetime import datetime
from dotenv import load_dotenv,find_dotenv
from couchbase.exceptions import (
    CouchbaseException,
    DocumentExistsException,
    DocumentNotFoundException,
)
from src.cb import CouchbaseClient
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields

app = Flask(__name__)

env_path = "./src/.env"
load_dotenv(env_path)

api = Api(app)
nsProduct = api.namespace("api/v1/products", "CRUD operations for Product")

productInsert = api.model(
    "ProductInsert",
    {
        "productName": fields.String(required=True, description="Product Name"),
        "productId": fields.String(required=True, description="Product's Unique ID"),
        "price": fields.Float(required=True, description="Product Price"),
        "tax": fields.Float(required=True, description="Product tax percentage"),
        "description": fields.String(required=False, description="Description of product"),
        "status": fields.String(required=True, description="Product Status"),
        "url" : fields.String(required=True, description="Image Url of the Product")
    },
)

product = api.model(
    "Product",
    {
        "id": fields.String(required=True, description="Product's system generated Id"),
        "productName": fields.String(required=True, description="Product Name"),
        "productId": fields.String(required=True, description="Product's Unique ID"),
        "price": fields.Float(required=True, description="Product Price"),
        "tax": fields.Float(required=True, description="Product tax percentage"),
        "description": fields.String(required=False, description="Description of product"),
        "status": fields.String(required=True, description="Product Status"),
        "url" : fields.String(required=True, description="Image Url of the Product"),
        "createdAt" : fields.String(required=True, description="Time product is created")
    },
)

@nsProduct.route("")
class Products(Resource):
    # tag::post[]
    @nsProduct.doc(
        "Create Product",
        reponses={201: "Created", 409: "Key alreay exists", 500: "Unexpected Error"},
    )
    @nsProduct.expect(productInsert, validate=True)
    @nsProduct.marshal_with(product)
    def post(self):
        try:
            data = request.json
            id = uuid.uuid4().__str__()
            data["id"] = id
            data["createdAt"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            cb.insert(id, data)
            return data, 201
        except DocumentExistsException:
            return "Key already exists", 409
        except CouchbaseException as e:
            return f"Unexpected error: {e}", 500
        except Exception as e:
            return f"Unexpected error: {e}", 500

    @nsProduct.doc(
        "Find Products",
        reponses={200: "found", 500: "Unexpected Error"},
        params={
            "status": "Product is ACTIVE/INACTIVE"
        },
    )
    def get(self):
        try:
            status = request.args.get("status","ACTIVE")
            query = f"SELECT p.* FROM  {db_info['bucket']}.{db_info['scope']}.{db_info['collection']} p  WHERE p.status = $status;"
            result = cb.query(query, status=status)
            products = [x for x in result]
            return products, 200
        except Exception as e:
            return f"Unexpected error: {e}", 500

@nsProduct.route("/<productId>")
class ProductId(Resource):
    @nsProduct.doc(
        "Get Profile",
        reponses={200: "Document Found", 404: "Document Not Found", 500: "Unexpected Error"},
    )
    def get(self, productId):
        try:
            query = f"SELECT p.* FROM  {db_info['bucket']}.{db_info['scope']}.{db_info['collection']} p  WHERE p.productId = $productId limit 1;"
            result = cb.query(query,productId=productId)
            return list(result)[0] ,200
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

if __name__ == "__main__":
    app.run(debug=True,port=5002)