from flask import Flask, render_template, redirect, url_for


app = Flask(__name__)
students = [{"id":1, "name":"Mahmoud"}, {"id":2, "name":"Ibrahim"}, {"id":3, "name":"El-Sayed"}]

@app.route("/")
def home_page():
    return render_template("index.html", students_data=students)

@app.route("/search/<int:id>")
def search(id):
    
    for student in students:
        if student['id'] == id:
            return render_template("search.html", student=student)
        return "No student found!"


if __name__ == "__main__":
    app.run(debug=True, port=5000)