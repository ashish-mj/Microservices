import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify,render_template

app = Flask(__name__)

env_path = "./src/.env"
load_dotenv(env_path)


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/order',methods=['GET','POST'])
def order():
    url = "http://" + os.getenv("PM_BASEURL") + ":" + os.getenv("PM_PORT") + os.getenv("PM_GETPRODUCT_URL")
    response = requests.get(url).json()
    if request.method == 'POST':
        data={}
        orderItems = []
        contact = {}
        for item in response:
            orderItem ={}
            if int(request.form[item['productId']]):
                orderItem["quantity"] = int(request.form[item['productId']])
                orderItem["productName"] = item["productName"]
                orderItem["price"] = item["price"]
                orderItem["productId"] = item["productId"]
                orderItem["tax"] = item["tax"]
                orderItems.append(orderItem)

        contact["name"] = request.form["name"]
        contact["address"] = request.form["address"]
        contact["emailId"] = request.form["email"]
        contact["phone"] = request.form["mobile"]
        data["orderItems"] = orderItems
        data["contact"] = contact

        url = "http://" + os.getenv("OM_BASEURL") + ":" + os.getenv("OM_PORT") + os.getenv("OM_SUBMITORDER_URL")
        response = requests.post(url, json=data)
        return render_template('orderView.html',data=response.json())
    return render_template('order.html',data=response)

@app.route('/viewOrder',methods=['GET','POST'])
def viewOrder():
    if request.method == 'POST':
        orderId = request.form['orderId']
        url = "http://" + os.getenv("OM_BASEURL") + ":" + os.getenv("OM_PORT") + os.getenv("OM_GETORDER_URL") + orderId
        response = requests.get(url).json()
        return render_template('orderView.html',data=response)
    return render_template('view.html')

if __name__ == "__main__":
    app.run(debug=True,port=5001)