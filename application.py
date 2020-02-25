import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    cash = db.execute("SELECT cash FROM users WHERE id=:id",
                        id=session.get("user_id"))
    rows = db.execute("SELECT symbol, company_name, SUM(share) FROM history \
                WHERE user_id=:id GROUP BY symbol", id=session.get("user_id"))
    grand_total = 0 + cash[0]['cash']
    for row in rows:
        try:
            row['price'] = lookup(row['symbol'])['price']
        except:
            row['price'] = 1
        row["value"] = round(row["SUM(share)"] * row["price"], 2)
        grand_total += row['value']
    return render_template("index.html", cash=cash[0]['cash'], rows=rows, total=round(grand_total, 2))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    share = int(request.form.get("shares"))
    symbol = request.form.get("symbol")
    quote = lookup(symbol)

    if not quote:
        return apology("invalid symbol", 404)

    price = quote['price']
    cash = round(share * price, 2)
    row = db.execute("SELECT cash FROM users WHERE id=:id",
                      id=session.get("user_id"))
    if cash > row[0]['cash']:
        return apology("Sorry, not enough cash", 406)

    db.execute("INSERT INTO history (user_id, company_name, symbol, transaction_type, price, share) \
                VALUES (:user_id, :company_name, :symbol, :transaction_type, :price, :share)",
                user_id=session.get("user_id"), symbol=quote['symbol'], company_name=quote['name'],
                transaction_type="buy",price=price, share=share)

    db.execute("UPDATE users SET cash=:cash WHERE id=:id",
            cash=row[0]['cash']-cash, id=session.get("user_id"))

    flash('Bought')
    return redirect(url_for('index'))


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT symbol, share, price, date FROM history WHERE user_id=:id",
                        id=session.get("user_id"))
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username").lower())

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect(url_for('index'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    symbol = request.form.get("symbol")
    quote = lookup(symbol)
    if not quote:
        return apology("invalid symbol", 404)

    name = quote['name']
    price = quote['price']
    symbol = quote['symbol']
    return render_template("quoted.html", name=name, price=price, symbol=symbol)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    password = request.form.get("password")
    pwhash = generate_password_hash(password)
    try:
        user_id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :pwhash)",
                username=username.lower(), pwhash=pwhash)
        session["user_id"] = user_id
    except:
        return apology("Username not available", 400)

    flash('Registered!')
    return redirect(url_for('index'))


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        symbols = db.execute("SELECT DISTINCT(symbol) FROM history WHERE user_id=:id",
                            id=session.get("user_id"))
        return render_template("sell.html", symbols=symbols)

    symbol = request.form.get("symbol")
    shares = int(request.form.get("shares"))
    shares_owned = db.execute("SELECT share FROM history WHERE user_id=:id \
                    AND symbol=:symbol AND transaction_type=:type ORDER BY date DESC",
                     id=session.get('user_id'), symbol=symbol.upper(), type="buy")

    if len(shares_owned) < 1:
        return apology("You don't have any shares in this company", 400)

    if shares > shares_owned[0]['share']:
        return apology(f"You can only sell { shares_owned[0]['share'] } shares or less than", 400)

    quote = lookup(symbol)
    price = quote['price']
    company_name = quote['name']
    value = round(shares * price, 2)

    cash = db.execute("SELECT cash FROM users where id=:id",
                        id=session.get('user_id'))
    db.execute("UPDATE users SET cash=:cash WHERE id=:id",
                cash=cash[0]['cash']+value, id=session.get('user_id'))
    db.execute("INSERT INTO history (user_id, symbol, company_name, transaction_type, share, price) \
                VALUES (:id, :symbol, :name, :type, :share, :price)",
                id=session.get('user_id'), symbol=symbol, name=company_name, type='sell',
                 price=price, share=int('-'+str(shares)))
    flash('Sold')
    return redirect(url_for('index'))


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
