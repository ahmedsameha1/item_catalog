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
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///item_catalog"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model, UserMixin):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    categories = db.relationship("Category", backref="user")

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


@app.route("/catalog.json")
def index_json():
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        return jsonify(categories_schema.dump(categories).data)
    except IndexError:
        return jsonify("Resource Error")

@app.route("/catalog/category/<int:category>/json")
def items_json(category):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category][0]
        return jsonify(items_schema.dump(cat_obj.items).data)
    except IndexError:
        return jsonify("Resource Error")

@app.route("/catalog/category/<int:category>/item/<int:item>/json")
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
def category(category_id):
    try:
        hany = User.query.filter_by(id="hany").one()
        categories = hany.categories
        cat_obj = [x for x in categories if x.id == category_id][0]
        return render_template("category.html", cat=cat_obj)
    except IndexError:
        return render_template("resource_error.html")

@app.route("/catalog/category/<int:category_id>/item/new", methods=["GET", "POST"])
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
    # must be dynamic
    app.run(host="0.0.0.0", port=5000, debug=True)
