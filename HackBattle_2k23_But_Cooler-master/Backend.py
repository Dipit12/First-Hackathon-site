from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'chupa_raaz'
db = SQLAlchemy(app)

app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Register")

    def validate_username(self, username):

        existing_user_name = User.query.filter_by(username=username.data).first()

        if existing_user_name:
            raise ValidationError("Username already exists. Make new one")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Login")

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

@app.route('/inventory_list')
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
        delivery_option = request.form['delivery']  # Get the selected delivery option

        # Get the selected item from the inventory
        item = InventoryItem.query.get_or_404(item_id)

        if item.quantity >= quantity:
            total_price = item.price * quantity

            # Calculate delivery cost based on the selected option
            if delivery_option == "standard":
                total_price += 20  # Standard delivery cost
            elif delivery_option == "urgent":
                total_price += 50  # Urgent delivery cost

            # Add convenience charge
            total_price += 10  # Convenience charge

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

@app.route('/get_item_price/<int:item_id>')
def get_item_price(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    return jsonify({'price': item.price})
@app.route('/')
def home():
    return render_template("HOMEPAGE2.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user=User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                if form.username.data == "popop":
                    return redirect(url_for('index'))
                else:
                    return redirect(url_for('purchase'))

    return render_template("login_page.html", form=form)
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template("Registration.html", form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard2.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return home()

if __name__ == '__main__':
     app.run(debug=True)
