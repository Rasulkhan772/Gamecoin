from flask import Flask, request, redirect, url_for, render_template, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gamecoin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    coins = db.Column(db.Integer, default=100)

with app.app_context():
    db.create_all()

# Admin credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ---------------- Routes ----------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["user"] = "admin"
            return redirect(url_for("admin_dashboard"))

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user"] = user.username
            return redirect(url_for("player_dashboard"))

        return "Invalid credentials! <a href='/'>Try again</a>"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            return "Username/Password required! <a href='/register'>Back</a>"

        if User.query.filter_by(username=username).first():
            return "Username already exists! <a href='/register'>Try again</a>"

        new_user = User(username=username, password=password, coins=100)
        db.session.add(new_user)
        db.session.commit()
        return "Player registered successfully! <a href='/'>Login</a>"

    return render_template("register.html")

@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"].strip()
        new_pass = request.form["password"].strip()
        user = User.query.filter_by(username=username).first()
        if user:
            user.password = new_pass
            db.session.commit()
            return "Password reset successful! <a href='/'>Login</a>"
        return "User not found! <a href='/forgot'>Try again</a>"

    return render_template("forgot.html")

@app.route("/admin")
def admin_dashboard():
    if session.get("user") == "admin":
        players = User.query.order_by(User.username.asc()).all()
        return render_template("admin.html", players=players)
    return redirect("/")

@app.route("/admin/add", methods=["POST"])
def admin_add():
    if session.get("user") == "admin":
        player = request.form.get("player", "").strip()
        amount = int(request.form.get("amount", "0") or 0)
        user = User.query.filter_by(username=player).first()
        if user and amount > 0:
            user.coins += amount
            db.session.commit()
        return redirect("/admin")
    return redirect("/")

@app.route("/admin/remove", methods=["POST"])
def admin_remove():
    if session.get("user") == "admin":
        player = request.form.get("player", "").strip()
        amount = int(request.form.get("amount", "0") or 0)
        user = User.query.filter_by(username=player).first()
        if user and 0 < amount <= user.coins:
            user.coins -= amount
            db.session.commit()
        return redirect("/admin")
    return redirect("/")

@app.route("/player")
def player_dashboard():
    username = session.get("user")
    if username and username != "admin":
        user = User.query.filter_by(username=username).first()
        if not user:
            session.clear()
            return redirect("/")
        return render_template("player.html", username=user.username, coins=user.coins)
    return redirect("/")

# API Games
@app.route("/api/play/<game>", methods=["POST"])
def play_api(game):
    username = session.get("user")
    if not username or username == "admin":
        return jsonify({"error": "Not a player"})
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"})

    result = {"success": False, "msg": "", "coins": user.coins}

    if game == "coin_toss":
        if user.coins >= 5:
            user.coins -= 5
            win = random.choice([True, False])
            if win:
                user.coins += 10
                result["msg"] = "You WON Coin Toss!"
                result["win"] = True
            else:
                result["msg"] = "You lost Coin Toss!"
                result["win"] = False
            result["success"] = True
        else:
            result["msg"] = "Not enough coins"

    elif game == "dice_roll":
        if user.coins >= 10:
            user.coins -= 10
            dice = random.randint(1, 6)
            if dice == 6:
                user.coins += 30
                result["msg"] = f"Dice={dice}. You WIN!"
                result["win"] = True
            else:
                result["msg"] = f"Dice={dice}. You lost"
                result["win"] = False
            result["dice"] = dice
            result["success"] = True
        else:
            result["msg"] = "Not enough coins"

    elif game == "lucky7":
        if user.coins >= 15:
            user.coins -= 15
            num = random.randint(1, 10)
            if num == 7:
                user.coins += 100
                result["msg"] = "JACKPOT! Lucky 7 🎉"
                result["win"] = True
            else:
                result["msg"] = f"Lucky={num}. You lost"
                result["win"] = False
            result["number"] = num
            result["success"] = True
        else:
            result["msg"] = "Not enough coins"

    db.session.commit()
    result["coins"] = user.coins
    return jsonify(result)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# --- Google verification route (serve static file from /static at root) ---
@app.route("/googleb1a6bf23852c0f70.html")
def google_verify():
    # import inside function to be safe
    from flask import send_from_directory
    return send_from_directory('static', 'googleb1a6bf23852c0f70.html')
