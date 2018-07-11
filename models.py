import application as app
from flask_login import UserMixin
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin

class User(app.db.Model, UserMixin):
    id = app.db.Column(app.db.String(50), primary_key=True)
    items = app.db.relationship("Item", backref="user")


class Authentication(OAuthConsumerMixin, app.db.Model):
    user_id = app.db.Column(app.db.String(50), app.db.ForeignKey(User.id))
    user = app.db.relationship(User)


class Category(app.db.Model):
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String(30), nullable=False)
    items = app.db.relationship("Item", backref="category")


class Item(app.db.Model):
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String(30), nullable=False)
    description = app.db.Column(app.db.String(3000), nullable=False)
    category_id = app.db.Column(app.db.Integer, app.db.ForeignKey("category.id"))
    user_id = app.db.Column(app.db.String(50), app.db.ForeignKey("user.id"))
