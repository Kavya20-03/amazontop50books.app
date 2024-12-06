from flask import Flask, render_template, request, redirect, url_for, session,flash,json
from models.models import db, Book, User
from werkzeug.security import generate_password_hash  # For password hashing
import plotly.graph_objects as go
import plotly
import json


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///amazon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Route for Home Page
@app.route("/")
def home():
    return render_template("home.html")


# Route for Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if user exists in the database and validate the password
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials, please try again."
    return render_template("login.html")


# Route for Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)  # Hash the password

        # Create a new user and add it to the database
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))  # Redirect to login page after registration
    return render_template("register.html")

@app.route('/add-book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])  # Convert price to float
        image_url = request.form['image_url']

        # Create a new book object
        new_book = Book(
            name=name,
            price=price,
            image_url=image_url
        )

        # Add the book to the database session
        db.session.add(new_book)
        db.session.commit()

        # Flash a success message and redirect to a book list page
        flash('Book added successfully!', 'success')
        return redirect(url_for('add_book'))  # Redirecting to the same page after successful submission

    return render_template('add_book.html')


# Route for Dashboard
# Route for Dashboard
@app.route("/dashboard")
def dashboard():
    books = Book.query.all()  # Fetch all books from the database
    return render_template("dashboard.html", books=books)  # Pass books to the template



# Route for displaying the cart
@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'cart' not in session:
        session['cart'] = []

    if request.method == 'POST':
        # Adding a new book to the cart
        book_title = request.form.get('book_title')
        book_price = float(request.form.get('book_price'))
        book_id = len(session['cart']) + 1

        new_book = {
            'id': book_id,
            'title': book_title,
            'price': book_price,
            'quantity': 1
        }

        # Add new book to the cart
        session['cart'].append(new_book)
        session.modified = True  # Ensure the session is modified

    return render_template('cart.html', cart=session['cart'])


# Route for updating the quantity of a book in the cart
@app.route('/update_cart/<int:book_id>', methods=['POST'])
def update_cart(book_id):
    quantity = int(request.form.get('quantity'))

    # Find the book in the cart and update its quantity
    for book in session['cart']:
        if book['id'] == book_id:
            book['quantity'] = quantity
            break

    session.modified = True
    return redirect(url_for('cart'))


# Route for removing a book from the cart
@app.route('/remove_item/<int:book_id>', methods=['GET'])
def remove_item(book_id):
    session['cart'] = [book for book in session['cart'] if book['id'] != book_id]
    session.modified = True
    return redirect(url_for('cart'))


# Route for checking out (optional)
@app.route('/checkout')
def checkout():
    if 'cart' not in session or len(session['cart']) == 0:
        return redirect(url_for('cart'))

    return render_template('checkout.html', cart=session['cart'])

@app.route("/analysis")
def analysis():
    # Query the database to get all books and their prices
    books = Book.query.all()

    # Extract book names and prices
    book_names = [book.name for book in books]
    book_prices = [book.price for book in books]

    # Create a Plotly bar chart
    fig = go.Figure(data=[go.Bar(
        x=book_names,
        y=book_prices,
        marker_color='orange'
    )])

    # Update layout of the graph
    fig.update_layout(
        title="Book Prices",
        xaxis_title="Book Name",
        yaxis_title="Price ($)",
        template="plotly_dark"
    )

    # Convert the plot to JSON to send to the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template("analysis.html", graph_json=graph_json)


# Route for logging out
@app.route("/logout")
def logout():
    session.pop("user_id", None)  # Remove the user session
    return redirect(url_for("login"))


# Run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)