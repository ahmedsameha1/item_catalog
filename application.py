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
import models

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


# For flask_marshmallow to work with models.Item class
class ItemSchema(ma.ModelSchema):
    class Meta:
        model = models.Item


# For flask_marshmallow to work with models.Category class
class CategorySchema(ma.ModelSchema):
    items = fields.Nested(ItemSchema, many=True, exclude=("category"))

    class Meta:
        model = models.Category

# To facilitate josnify
categories_schema = CategorySchema(many=True)
category_schema = CategorySchema()
items_schema = ItemSchema(many=True, exclude=["category", "user"])
item_schema = ItemSchema(exclude=["category", "user"])

# To make flask dance work with sqlalchemy as a backend
google_blueprint.backend = SQLAlchemyBackend(
    models.Authentication, db.session,
    user_required=False, user=current_user)


def create_user(email):
    user = models.User(id=email)
    db.session.add(user)
    db.session.commit()
    return user


@login_manager.user_loader
def user_load(user_id):
    return models.User.query.get(user_id)


# Instead of showing unauthorized page, redirect to login page
@login_manager.unauthorized_handler
def redirect_login():
    return redirect(url_for("catalog"))


# This fuction being called when the authentication is done
@oauth_authorized.connect_via(google_blueprint)
def logged_in(blueprint, token):
    account_info = google.get("/oauth2/v2/userinfo")
    if account_info.ok:
        email = account_info.json()["email"]
        query = models.User.query.filter_by(id=email)
        try:
            user = query.one()
        except NoResultFound:
            user = create_user(email)
        login_user(user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("catalog"))


@app.route("/json")
def index_json():
    try:
        categories = models.Category.query.all()
        return jsonify(categories_schema.dump(categories).data)
    except IndexError:
        return jsonify("Resource Error")


@app.route("/category/<int:category>/json")
def items_json(category):
    try:
        categories = models.Category.query.all()
        cat_obj = [x for x in categories if x.id == category][0]
        return jsonify(category_schema.dump(cat_obj).data)
    except IndexError:
        return jsonify("Resource Error")


@app.route("/category/<int:category>/item/<int:item>/json")
def item_json(category, item):
    try:
        categories = models.Category.query.all()
        cat_obj = [x for x in categories if x.id == category][0]
        item_obj = [n for n in cat_obj.items if n.id == item][0]
        return jsonify(item_schema.dump(item_obj).data)
    except IndexError:
        return jsonify("Resource Error")


@app.route("/")
def catalog():
    try:
        categories = models.Category.query.all()
        last_items = []
        for i in categories:
            items = i.items
            sorted_items = sorted(items,
                                  key=lambda item: item.id, reverse=True)
            if len(sorted_items) > 0:
                last_items.append((i.name, sorted_items[0]))
        return render_template("catalog.html",
                               cats=categories, last_items=last_items,
                               ok=current_user.is_authenticated)
    except IndexError:
        return render_template("resource_error.html")


@app.route("/category/<int:category_id>")
def category(category_id):
    try:
        categories = models.Category.query.all()
        cat_obj = [x for x in categories if x.id == category_id][0]
        return render_template("category.html", cat=cat_obj,
                               ok=current_user.is_authenticated)
    except IndexError:
        return render_template("resource_error.html")


@app.route("/category/<int:category_id>/item/new",
           methods=["GET", "POST"])
@login_required
def new_item(category_id):
    try:
        categories = models.Category.query.all()
        cat_obj = [x for x in categories if x.id == category_id][0]
        # The user browse the page
        if request.method == "GET":
            return render_template("new_item.html", cat=cat_obj,
                                   ok=current_user.is_authenticated)
        # The user submit the form
        elif request.method == "POST":
            item_obj = models.Item(name=request.form["name"],
                            description=request.form["description"],
                            category=cat_obj, user=current_user)
            db.session.add(item_obj)
            db.session.commit()
            return redirect(url_for("category", category_id=cat_obj.id))
    except IndexError:
        return render_template("resource_error.html")


@app.route("/category/<int:category_id>/item/<int:item_id>")
def item(category_id, item_id):
    try:
        categories = models.Category.query.all()
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [n for n in cat_obj.items if n.id == item_id][0]
        modify_ok = item_obj.user == current_user
        return render_template("item.html", cat=cat_obj, item=item_obj,
                               ok=current_user.is_authenticated,
                               modify_ok=modify_ok)
    except IndexError:
        return render_template("resource_error.html")


@app.route("/category/<int:category_id>/item/<int:item_id>/delete",
           methods=["GET", "POST"])
@login_required
def delete_item(category_id, item_id):
    try:
        categories = models.Category.query.all()
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [n for n in cat_obj.items if n.id == item_id][0]
        modify_ok = item_obj.user == current_user
        # The user browse the page
        if request.method == "GET" and modify_ok:
            return render_template("delete_item.html",
                                   cat=cat_obj, item=item_obj,
                                   ok=current_user.is_authenticated)

        # The user submit the form
        elif request.method == "POST" and modify_ok:
            db.session.delete(item_obj)
            db.session.commit()
            return redirect(url_for("category", category_id=cat_obj.id))

        # The current user isn't the creator of the current item
        else:
            return redirect(url_for("item", category_id=cat_obj.id,
                                    item_id=item_obj.id))
    except IndexError:
        return render_template("resource_error.html")


@app.route("/category/<int:category_id>/item/<int:item_id>/edit",
           methods=["GET", "POST"])
@login_required
def edit_item(category_id, item_id):
    try:
        categories = models.Category.query.all()
        cat_obj = [x for x in categories if x.id == category_id][0]
        item_obj = [n for n in cat_obj.items if n.id == item_id][0]
        modify_ok = item_obj.user == current_user
        # The user browse the page
        if request.method == "GET" and modify_ok:
            return render_template("edit_item.html", cat=cat_obj,
                                   item=item_obj, categories=categories,
                                   ok=current_user.is_authenticated)

        # The user submit the form
        elif request.method == "POST" and modify_ok:
            item_obj.name = request.form["name"]
            item_obj.description = request.form["description"]
            selected_category = [x for x in categories if x.name ==
                                 request.form["category"]][0]
            item_obj.category = selected_category
            db.session.add(item_obj)
            db.session.commit()
            return redirect(url_for("item", category_id=selected_category.id,
                                    item_id=item_obj.id))

        # The current user isn't the creator of the current item
        else:
            return redirect(url_for("item", category_id=cat_obj.id,
                                    item_id=item_obj.id))
    except IndexError:
        return render_template("resource_error.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
