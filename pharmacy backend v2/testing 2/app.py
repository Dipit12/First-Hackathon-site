from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'  # SQLite database
db = SQLAlchemy(app)

app.app_context().push()

# Define the Inventory model
class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Define the StudentPurchase model
class StudentPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

# Create the database tables
db.create_all()

@app.route('/')
def index():
    # Display the inventory list
    inventory_items = InventoryItem.query.all()
    return render_template('index.html', inventory_items=inventory_items)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])

        # Create a new inventory item
        new_item = InventoryItem(name=name, quantity=quantity, price=price)

        # Add the item to the database
        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_item.html')

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)

    if request.method == 'POST':
        item.name = request.form['name']
        item.quantity = int(request.form['quantity'])
        item.price = float(request.form['price'])

        db.session.commit()

        return redirect(url_for('index'))

    return render_template('edit_item.html', item=item)

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        student_name = request.form['student_name']
        item_id = int(request.form['item_id'])
        quantity = int(request.form['quantity'])

        # Get the selected item from the inventory
        item = InventoryItem.query.get_or_404(item_id)

        if item.quantity >= quantity:
            total_price = item.price * quantity

            # Create a new student purchase record
            purchase = StudentPurchase(student_name=student_name, item_id=item_id, quantity=quantity, total_price=total_price)

            # Update the inventory quantity
            item.quantity -= quantity

            # Add the purchase record to the database
            db.session.add(purchase)
            db.session.commit()

            # Render an order confirmation screen with order details
            return render_template('order_confirmation.html', student_name=student_name, item_name=item.name, quantity=quantity, total_price=total_price)

    # Get all inventory items for the dropdown list
    inventory_items = InventoryItem.query.all()
    return render_template('purchase.html', inventory_items=inventory_items)

@app.route('/view_orders/<int:item_id>')
def view_orders(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    orders = StudentPurchase.query.filter_by(item_id=item_id).all()
    return render_template('view_orders.html', item=item, orders=orders)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    order = StudentPurchase.query.get_or_404(order_id)
    item = InventoryItem.query.get_or_404(order.item_id)
    item.quantity += order.quantity
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('view_orders', item_id=item.id))

@app.route('/fulfill_order/<int:order_id>', methods=['POST'])
def fulfill_order(order_id):
    order = StudentPurchase.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('view_orders', item_id=order.item_id))


if __name__ == '__main__':
    app.run(debug=True)
