from app import app, db
from flask import flash, jsonify, redirect, render_template, request, session, url_for

from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from app.models import Users, Records
from app.helpers import apology, login_required, lookup, usd

#custom filter
app.jinja_env.filters["usd"] = usd

# Ensure respknses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
@app.route('/index')
@login_required
def index():
    """Show portfolio of stocks"""
    user = Users.query.get(session.get("user_id"))
    query = db.session.query(Records.symbol, Records.company_name,
            db.func.sum(Records.shares).label("shares")).group_by(Records.symbol,
            Records.company_name).filter(Records.user_id==user.id)
    info = [{}] * query.count()
    grand_total = user.cash
    for i, row in enumerate(query):
        try:
            info[i]['price'] = lookup(row.symbol)['price']
        except:
            info[i]['price'] = 1

        info[i]['symbol'] = row.symbol
        info[i]['company_name'] = row.company_name
        info[i]['shares'] = row.shares
        info[i]['value'] = round(row.shares * info[i]['price'], 2)
        grand_total += info[i]['value']

    return render_template("index.html", cash=user.cash, rows=info, total=round(grand_total, 2))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy share of stock"""

    if request.method == "GET":
        return render_template("buy.html")

    # User reached route via POST (as by submitting a form via POST)
    shares = int(request.form.get("shares"))
    symbol = request.form.get("symbol")
    quote = lookup(symbol)

    if not quote:
        return apology("invalid symbol", 404)

    price = quote['price']
    value = round(shares * price, 2)
    user = Users.query.get(session.get("user_id"))

    if value > user.cash:
        return apology("You don't have enough cash", 406)

    record = Records(symbol=quote['symbol'], company_name=quote['name'],
                transact_type="buy", shares=shares, price=price, user_id=user.id)
    user.cash -= value
    db.session.add(record)
    db.session.commit()

    flash("Bought")
    return redirect(url_for('index'))


@app.route("/history")
@login_required
def history():
    """show history of transactions"""
    query = Records.query.filter_by(user_id=session.get("user_id")).all()
    return render_template("history.html", rows=query)


@app.route("/login", methods=["GET", "POST"])
def login():
    """log user in"""

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
        user = Users.query.filter_by(username=request.form.get("username").lower()).first()

        # Ensure username exists and password is correct
        if user is None or not user.check_password(request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user loggen in
        session["user_id"] = user.id

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

    username = request.form.get("username").lower()
    password = request.form.get("password")

    check = Users.query.filter_by(username=username).first()

    if check is not None:
        return apology("Please use a different username", 400)

    user = Users(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    session["user_id"] = user.id
    db.session.commit()

    flash('Registered!')
    return redirect(url_for('index'))

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        symbols = Records.query.with_entities(Records.symbol).\
                distinct().filter_by(user_id=session.get("user_id")).all()
        return render_template("sell.html", symbols=symbols)

    symbol = request.form.get("symbol")
    shares = int(request.form.get("shares"))

    record = db.session.query(db.func.sum(Records.shares).label("shares")).\
     group_by(Records.user_id).filter_by(symbol=symbol, user_id=session.get('user_id')).one()

    if shares > record.shares:
        return apology(f"You can only sell { record.shares } shares or less than", 400)

    quote = lookup(symbol)
    price = quote['price']
    value = round(shares * price, 2)

    user = Users.query.get(session.get('user_id'))
    user.cash += value

    record = Records(symbol=quote['symbol'], company_name=quote['name'],
                transact_type="sell", shares=int('-'+str(shares)),
                price=price, user_id=user.id)

    db.session.add(record)
    db.session.commit()

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