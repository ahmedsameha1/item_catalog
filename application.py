from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from sqlalchemy.sql import func
from flask_marshmallow import Marshmallow
from marshmallow import fields
from flask import jsonify
from sqlalchemy.orm.exc import NoResultFound
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///item_catalog777"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "weortfhweghweog"
db = SQLAlchemy(app)
ma = Marshmallow(app)
login_manager = LoginManager(app)

google_blueprint = make_google_blueprint( client_id="912137232701-omul0gsrmg6ku5b347ma2kr4uk0ja9de.apps.googleusercontent.com", client_secret="4v7ddYKtufP5SIRRrBrnQS6P", scope = ["profile", "email"])

app.register_blueprint(google_blueprint, url_prefix="/login")

class User(db.Model, UserMixin):
    id = db.Column(db.String(50), primary_key=True)
    categories = db.relationship("Category", backref="user")

class Authentication(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String(50), db.ForeignKey(User.id))
    user = db.relationship(User)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey("user.id"))
    items = db.relationship("Item", backref="category")

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(3000), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

class ItemSchema(ma.ModelSchema):
    class Meta:
        model = Item

class CategorySchema(ma.ModelSchema):
    items = fields.Nested(ItemSchema, many=True, exclude=("category"))
    class Meta:
        model = Category

categories_schema = CategorySchema(many=True, exclude=["user"])
category_schema = CategorySchema(exclude=["user"])
items_schema = ItemSchema(many=True, exclude=["category"])
item_schema = ItemSchema(exclude=["category"])

google_blueprint.backend = SQLAlchemyBackend(Authentication, db.session, user=current_user)

@login_manager.user_loader
def user_load(user_id):
    return User.query.get(user_id)

@oauth_authorized.connect_via(google_blueprint)
def logged_in(blueprint, token):
    account_info = blueprint.session(token).get("/oauth2/v2/userinfo")
    if account_info.ok:
        email = account_info.json()["email"]
        query = User.query.filter_by(id=email)
        try:
            user = query.one()
        except NoResultFound:
            user = User(id=email)
            db.session.add(user)
            db.session.commit(user)
        login_user(user)

@app.route("/")
def login():
    if not google.authorized:
        return render_template("login.html")
    else:
        return redirect(url_for("catalog"))

@app.route("/logout")
@login_required
def logout():
    logout_user()

@app.route("/catalog.json")
@login_required
def index_json():
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        return jsonify(categories_schema.dump(categories).data)
    except IndexError:
        return jsonify("Resource Error")

@app.route("/catalog/category/<int:category>/json")
@login_required
def items_json(category):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category][0]
        return jsonify(items_schema.dump(cat_obj.items).data)
    except IndexError:
        return jsonify("Resource Error")

@app.route("/catalog/category/<int:category>/item/<int:item>/json")
@login_required
def item_json(category, item):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category][0]
        item_obj = [ n for n in cat_obj.items if n.id == item][0]
        return jsonify(item_schema.dump(item_obj).data)
    except IndexError:
        return jsonify("Resource Error")

@app.route("/catalog")
@login_required
def catalog():
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        last_items = []
        for i in categories:
            items = i.items
            sorted_items = sorted(items, key=lambda item: item.id, reverse=True)
            if len(sorted_items) > 0:
                last_items.append(( i.name, sorted_items[0]))
        return render_template("catalog.html", cats=categories, last_items=last_items)
    except IndexError:
        return render_template("resource_error.html")

@app.route("/catalog/category/<int:category_id>")
@login_required
def category(category_id):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        return render_template("category.html", cat=cat_obj)
    except IndexError:
        return render_template("resource_error.html")

@app.route("/catalog/category/<int:category_id>/item/new", methods=["GET", "POST"])
@login_required
def new_item(category_id):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        if request.method == "GET":
            return render_template("new_item.html", cat=cat_obj)
        elif request.method == "POST":
            print db.session is db.session
            item_obj = Item(name=request.form["name"], description=request.form["description"], category=cat_obj)
            db.session.add(item_obj)
            db.session.commit()
            return redirect(url_for("category", category_id=cat_obj.id))
    except IndexError:
        return render_template("resource_error.html")

@app.route("/catalog/category/<int:category_id>/item/<int:item_id>")
@login_required
def item(category_id, item_id):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [ n for n in cat_obj.items if n.id == item_id][0]
        return render_template("item.html", cat=cat_obj, item=item_obj)
    except IndexError:
        return render_template("resource_error.html")


@app.route("/catalog/category/<int:category_id>/item/<int:item_id>/delete", methods=["GET","POST"])
@login_required
def delete_item(category_id, item_id):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [ n for n in cat_obj.items if n.id == item_id][0]
        if request.method == "GET":
            return render_template("delete_item.html", cat=cat_obj, item=item_obj)
        elif request.method == "POST":
            db.session.delete(item_obj)
            db.session.commit()
            return redirect(url_for("category", category_id=cat_obj.id))
    except IndexError:
        return render_template("resource_error.html")

@app.route("/catalog/category/<int:category_id>/item/<int:item_id>/edit", methods=["GET","POST"])
@login_required
def edit_item(category_id, item_id):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [ n for n in cat_obj.items if n.id == item_id][0]
        if request.method == "GET":
            return render_template("edit_item.html", cat=cat_obj,
                    item=item_obj, categories=categories)
        elif request.method == "POST":
            item_obj.name = request.form["name"]
            item_obj.description = request.form["description"]
            selected_category = [x for x in categories if x.name == request.form["category"]][0]
            item_obj.category = selected_category
            db.session.add(item_obj)
            db.session.commit()
            return redirect(url_for("category", category_id=selected_category.id))
    except IndexError:
        return render_template("resource_error.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
