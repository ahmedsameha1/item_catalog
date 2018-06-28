from application import db, Category

db.create_all()
db.session.add(Category(name="Soccer"))
db.session.add(Category(name="Basketball"))
db.session.add(Category(name="Baseball"))
db.session.add(Category(name="Frisbee"))
db.session.add(Category(name="Snowboarding"))
db.session.add(Category(name="Rock Climbing"))
db.session.add(Category(name="Foosball"))
db.session.add(Category(name="Skating"))
db.session.add(Category(name="Hockey"))
db.session.commit()
