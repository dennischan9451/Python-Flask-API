# using flask_restful
from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
from bs4 import BeautifulSoup
import requests
import json
# creating the flask app
app = Flask(__name__)
# creating an API object
api = Api(app)

with open('config.json') as cf:
    config = json.load(cf)

base_url = config['base_url']
shop_url = config['shop_url']

headers = config['headers']
api_host = config['api_host']
api_port = config['api_port']

def ext_num_from_str(extractStr):
    return int(''.join(filter(str.isdigit, extractStr)))

def get_product_url(product_code):
    print(product_code)
    param_obj = {'search': product_code}
    resp = requests.post(url = shop_url, data = param_obj, headers = headers)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        detail_div_elements = soup.find_all('div', {'class': 'detail'})

        if len(detail_div_elements) == 0:
            return {
                'status': False,
                'msg': 'Currently, this product does not exist.',
                'err_code': 404
            }

        product_url = None
        price_str = None
        product_price = None
        product_found = False
        for detail_div_element in detail_div_elements:
            try:
                code = detail_div_element.find('ul', {'class': 'clear'}).find_all('li')[1].get_text().replace(" ", "")
            except:
                code = None
            if code == product_code:
                product_found = True
                product_url = base_url + detail_div_element.find('a')['href']
                price_str = detail_div_element.find('p', {'class': 'price'}).get_text()
                product_price = ext_num_from_str(price_str)
                break
        if product_found:
            return {
                'status': True,
                'product_url': product_url,
                'product_price': product_price
            }
        else:
            return {
                'status': False,
                'msg': 'Currently, this product does not exist.',
                'err_code': 404
            }
    else:
        return {
            'status': False,
            'msg': 'Internal server error in buyerz shopping site.',
            'err_code': resp.status_code
        }

def get_product_info(product_url, name_idx):
    page = requests.get(product_url, headers=headers)
    if page.status_code == 200:
        soup = BeautifulSoup(page.text, 'html.parser')
        item_info = soup.find('div', {'id': 'itemInfo'})
        name = item_info.find('h2').get_text()[name_idx:].strip()
        try:
            quantity_str = item_info.find('span', {'class': 'M_item-stock-smallstock'}).text.strip()
            quantity = ext_num_from_str(quantity_str)
        except:
            quantity = 0
        return {
            'status': True,
            'name': name,
            'quantity': quantity
        }
    else:
        return {
            'status': False,
            'msg': 'Not fetched page content from buyerz.shop',
            'err_code': page.status_code
        }

class Product(Resource):
    # Corresponds to POST request
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("product_code")
        args = parser.parse_args()

        result1 = get_product_url(args['product_code'].replace(" ", ""))
        if result1['status']:
            product_url = result1['product_url']
            product_price = result1['product_price']

            name_idx = len(args['product_code']) + 1
            result2 = get_product_info(product_url, name_idx)
            if result2['status']:
                return { 'url': product_url, 'name': result2['name'], 'price': product_price, 'quantity' : result2['quantity']}, 200
            else:
                return {'msg': result2['msg']}, result2['err_code']
        else:
            return {'msg': result1['msg']}, result1['err_code']


# adding the defined resources along with their corresponding urls
api.add_resource(Product, '/get_product')

# driver function
if __name__ == '__main__':
    app.run(host=api_host, port=api_port, debug = False)
