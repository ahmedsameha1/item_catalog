from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin,\
    current_user, login_required, login_user, logout_user
from sqlalchemy.sql import func
from flask_marshmallow import Marshmallow
from marshmallow import fields
from flask import jsonify
from sqlalchemy.orm.exc import NoResultFound
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.backend.sqla import\
    OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///item_catalog"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "weortfhweghweogroghergherouiiuhemgo"
db = SQLAlchemy(app)
ma = Marshmallow(app)
login_manager = LoginManager(app)

google_blueprint = make_google_blueprint(
    client_id="912137232701-omul0gsrmg6ku5b347ma2"
    "kr4uk0ja9de.apps.googleusercontent.com",
    client_secret="4v7ddYKtufP5SIRRrBrnQS6P", scope=["profile", "email"])

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
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))


# For flask_marshmallow to work with Item class
class ItemSchema(ma.ModelSchema):
    class Meta:
        model = Item


# For flask_marshmallow to work with Category class
class CategorySchema(ma.ModelSchema):
    items = fields.Nested(ItemSchema, many=True, exclude=("category"))

    class Meta:
        model = Category

# To facilitate josnify
categories_schema = CategorySchema(many=True, exclude=["user"])
category_schema = CategorySchema(exclude=["user"])
items_schema = ItemSchema(many=True, exclude=["category"])
item_schema = ItemSchema(exclude=["category"])

# To make flask dance work with sqlalchemy as a backend
google_blueprint.backend = SQLAlchemyBackend(
    Authentication, db.session,
    user_required=False, user=current_user)


def create_user(email):
    user = User(id=email)
    db.session.add(user)
    # Because the app has fixed categories,
    # we create those categories with the user
    db.session.add_all([Category(name="Soccer", user=user),
                        Category(name="Basketball", user=user),
                        Category(name="Baseball", user=user),
                        Category(name="Frisbee", user=user),
                        Category(name="Snowboarding", user=user),
                        Category(name="Rock Climbing", user=user),
                        Category(name="Foosball", user=user),
                        Category(name="Skating", user=user),
                        Category(name="Hockey", user=user)])
    db.session.commit()
    return user


@login_manager.user_loader
def user_load(user_id):
    return User.query.get(user_id)


# Instead of showing unauthorized page, redirect to login page
@login_manager.unauthorized_handler
def redirect_login():
    return redirect(url_for("login"))


# This fuction being called when the authentication is done
@oauth_authorized.connect_via(google_blueprint)
def logged_in(blueprint, token):
    account_info = google.get("/oauth2/v2/userinfo")
    if account_info.ok:
        email = account_info.json()["email"]
        query = User.query.filter_by(id=email)
        try:
            user = query.one()
        except NoResultFound:
            user = create_user(email)
        login_user(user)


@app.route("/", methods=["GET"])
def login():
    if not google.authorized:
        return render_template("login.html")
    else:
        return redirect(url_for("catalog"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/catalog.json")
@login_required
def index_json():
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        return jsonify(categories_schema.dump(categories).data)
    except IndexError:
        return jsonify("Resource Error")


@app.route("/catalog/category/<int:category>/json")
@login_required
def items_json(category):
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        cat_obj = [x for x in categories if x.id == category][0]
        return jsonify(items_schema.dump(cat_obj.items).data)
    except IndexError:
        return jsonify("Resource Error")


@app.route("/catalog/category/<int:category>/item/<int:item>/json")
@login_required
def item_json(category, item):
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        cat_obj = [x for x in categories if x.id == category][0]
        item_obj = [n for n in cat_obj.items if n.id == item][0]
        return jsonify(item_schema.dump(item_obj).data)
    except IndexError:
        return jsonify("Resource Error")


@app.route("/catalog")
@login_required
def catalog():
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        last_items = []
        for i in categories:
            items = i.items
            sorted_items = sorted(items,
                                  key=lambda item: item.id, reverse=True)
            if len(sorted_items) > 0:
                last_items.append((i.name, sorted_items[0]))
        return render_template("catalog.html",
                               cats=categories, last_items=last_items)
    except IndexError:
        return render_template("resource_error.html")


@app.route("/catalog/category/<int:category_id>")
@login_required
def category(category_id):
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        return render_template("category.html", cat=cat_obj)
    except IndexError:
        return render_template("resource_error.html")


@app.route("/catalog/category/<int:category_id>/item/new",
           methods=["GET", "POST"])
@login_required
def new_item(category_id):
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        # The user browse the page
        if request.method == "GET":
            return render_template("new_item.html", cat=cat_obj)
        # The user submit the form
        elif request.method == "POST":
            print db.session is db.session
            item_obj = Item(name=request.form["name"],
                            description=request.form["description"],
                            category=cat_obj)
            db.session.add(item_obj)
            db.session.commit()
            return redirect(url_for("category", category_id=cat_obj.id))
    except IndexError:
        return render_template("resource_error.html")


@app.route("/catalog/category/<int:category_id>/item/<int:item_id>")
@login_required
def item(category_id, item_id):
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [n for n in cat_obj.items if n.id == item_id][0]
        return render_template("item.html", cat=cat_obj, item=item_obj)
    except IndexError:
        return render_template("resource_error.html")


@app.route("/catalog/category/<int:category_id>/item/<int:item_id>/delete",
           methods=["GET", "POST"])
@login_required
def delete_item(category_id, item_id):
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [n for n in cat_obj.items if n.id == item_id][0]
        # The user browse the page
        if request.method == "GET":
            return render_template("delete_item.html",
                                   cat=cat_obj, item=item_obj)
        # The user submit the form
        elif request.method == "POST":
            db.session.delete(item_obj)
            db.session.commit()
            return redirect(url_for("category", category_id=cat_obj.id))
    except IndexError:
        return render_template("resource_error.html")


@app.route("/catalog/category/<int:category_id>/item/<int:item_id>/edit",
           methods=["GET", "POST"])
@login_required
def edit_item(category_id, item_id):
    try:
        # current user is the current logged in user.
        # It's an instance of User class
        categories = current_user.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [n for n in cat_obj.items if n.id == item_id][0]
        # The user browse the page
        if request.method == "GET":
            return render_template("edit_item.html", cat=cat_obj,
                                   item=item_obj, categories=categories)
        # The user submit the form
        elif request.method == "POST":
            item_obj.name = request.form["name"]
            item_obj.description = request.form["description"]
            selected_category = [x for x in categories if x.name ==
                                 request.form["category"]][0]
            item_obj.category = selected_category
            db.session.add(item_obj)
            db.session.commit()
            return redirect(url_for("category",
                                    category_id=selected_category.id))
    except IndexError:
        return render_template("resource_error.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
