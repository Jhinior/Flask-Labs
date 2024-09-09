from flask import Flask, render_template, url_for, redirect
from flask import request, session 
from flask import flash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "Mahmoud123" 
app.permanent_session_lifetime = timedelta(days=3)


@app.route("/home")
@app.route("/")
def home_page():
    return render_template("home.html")

@app.route("/signup", methods=['GET', 'POST'])
def sign_up():
    if request.method == "POST":
        user_name = request.form['nm']
        password = request.form['ps']
        confirm_password = request.form['confirm_ps']
        if password == confirm_password:
            session['username'] = user_name
            session['password'] = password
            flash("Successfully Registered", "info")
            return redirect(url_for("login"))
        else:
            return f"confirm password and password doesnt match"
    else:
        return render_template("users/signup.html") # users/signup.html
    
    
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user_name = request.form['nm']
        password = request.form['ps']
        
        if 'username' in session and 'password' in session:
            if user_name == session['username'] and password == session['password']:
                session.permanent = True 
                flash("Successfully logged in", "info")
                return redirect(url_for('user.profile'))
            else:
                flash("Invalid Username/Password!!", "error")
                return redirect(url_for('login'))
        else:
            flash("No user found in session. Please sign up.", "error")
            return redirect(url_for("sign_up"))
    else: 
        return render_template("login.html", images=['images_3.png', 'images_4.png'])

    
@app.route("/profile", endpoint='user.profile')
def show_profile():
    if 'username' in session.keys():
        name = session['username']
        password = session['password']
        return render_template("profile.html", name=name, password=password)
    else: 
        flash("Sessions ends, please rewrite username and password", "info")
        return redirect(url_for("login"))
   

@app.route("/logout", methods={"GET"})
def logout():
    session.clear()
    return redirect(url_for('home_page'))

if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True, port=5000)