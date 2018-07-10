from application import db, Category

db.create_all()
db.session.add_all([Category(name="Soccer"),
                    Category(name="Basketball"),
                    Category(name="Baseball"),
                    Category(name="Frisbee"),
                    Category(name="Snowboarding"),
                    Category(name="Rock Climbing"),
                    Category(name="Foosball"),
                    Category(name="Skating"),
                    Category(name="Hockey")])
db.session.commit()
