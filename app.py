from flask import Flask, render_template

app = Flask(__name__)

# 메인
@app.route("/")
def home():
    return render_template("index.html")

# 시공사례
@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html")

if __name__ == "__main__":
    app.run(debug=True)