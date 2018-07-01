from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from sqlalchemy.sql import func
from flask_marshmallow import Marshmallow
from marshmallow import fields
from flask import jsonify

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///item_catalog"
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

# must be dynamic
hany = User.query.filter_by(id="hany").one()
categories = hany.categories

@app.route("/catalog.json")
def index_json():
    return jsonify(categories_schema.dump(categories).data)

@app.route("/catalog/category/<int:category>/items.json")
def items_json(category):
    cat_obj = [x for x in categories if x.id == category][0]
    return jsonify(items_schema.dump(cat_obj.items).data)

@app.route("/catalog/category/<int:category>/items/<int:item>/json")
def item_json(category, item):
    cat_obj = [x for x in categories if x.id == category][0]
    item_obj = [ n for n in cat_obj.items if n.id == item][0]
    return jsonify(item_schema.dump(item_obj).data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
