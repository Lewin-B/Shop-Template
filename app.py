from flask import Flask, render_template, request, session, redirect, url_for
import uuid
import pymysql
from datetime import datetime
import os

# connection
connection = pymysql.connect(
    host=os.environ.get('ENDPOINT'), user=os.environ.get('USERNAME'), passwd=os.environ.get('PASSWORD'), db=os.environ.get('DATABASE_NAME'))
db = connection.cursor()

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')


def generate_order_number():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4().int)[:6]
    order_number = f"{timestamp}-{unique_id}"
    return order_number


@app.route('/')
def index():
    db.execute('SELECT * FROM products')
    products = db.fetchall()
    return render_template('index.html', products=products)


@app.route('/home', methods=['GET'])
def home():
    return redirect('/')


@app.route('/product', methods=['GET', 'POST'])
def product():
    if request.method == 'GET':
        product_id = request.args.get('product_id')
        db.execute('SELECT * FROM products WHERE product_id = %s', (product_id))
        product = db.fetchall()
        return render_template('product.html', product=product)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'GET':
        cart = session.get('cart', {})
        return render_template('cart.html', cart=cart)

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        stock = request.form.get('product_stock')
        quantity = request.form.get('quantity')

        print("quantity: ", quantity)
        print("product_stock: ", stock)

        if int(quantity) > int(stock):
            print(quantity + " is greater than " + stock)
            return render_template("error.html")

        # Get Product
        db.execute('SELECT * FROM products WHERE product_id = %s', (product_id,))
        product = db.fetchall()

        if not product:
            return render_template("error.html")

        product_name = product[0][1]
        product_image = product[0][2]
        product_price = product[0][4]

        # Retrieve the cart from the session or create an empty one
        cart = session.get('cart', {})

        # Calculate the updated quantity in the cart
        cart_quantity = cart.get(product_id, {}).get(
            'quantity', 0) + int(quantity)

        if cart_quantity > int(stock):
            print("Cart quantity exceeds stock quantity")
            return render_template("error.html")

        # Update the cart with the new product and quantity
        cart[product_id] = {
            'name': product_name,
            'image': product_image,
            'price': product_price,
            'quantity': cart_quantity
        }

        # Store the updated cart back in the session
        session['cart'] = cart

        # Return a valid response
        return redirect('/')


@app.route('/clear-cart', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get('product_id')
    cart = session.get('cart', {})

    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart

    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'GET':
        cart = session.get('cart', {})
        total = 0
        for product_id, item in cart.items():
            subtotal = item['price'] * item['quantity']
            total += subtotal

        return render_template('checkout.html', cart=cart, total=total)

    if request.method == 'POST':
        # Get cart data
        cart = session.get('cart', {})
        # Retrieve the form data
        card_number = request.form.get('card_number')
        expiration_date = request.form.get('expiration_date')
        cvv = request.form.get('cvv')

        # retrieve shipping information
        name_value = request.form.get('billing_name')
        email_value = request.form.get('email')
        address_value = request.form.get('shipping_address')
        order_number = generate_order_number()
        product_value = ''
        for product_id, item in cart.items():
            product_name = item['name']
            quantity = item['quantity']
            product_value += f"{product_name} ({quantity}), "

        # Perform payment verification logic (mock implementation)
        if card_number == '123456789' and expiration_date == '12/23' and cvv == '123':
            db.execute('INSERT INTO orders (order_number, name, email, address, product) VALUES (%s, %s, %s, %s, %s)',
                       (order_number, name_value, email_value, address_value, product_value))
            connection.commit()

            for product_id, item in cart.items():
                db.execute(
                    'SELECT stock FROM products WHERE product_id = %s', (product_id))
                stock = db.fetchall()
                new_stock = int(stock[0][0]) - int(item['quantity'])
                db.execute(
                    'UPDATE products SET stock = %s WHERE product_id = %s', (new_stock, product_id))
                connection.commit()

            return render_template('payment_success.html', order_number=order_number)
        else:
            return render_template('payment_failure.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
