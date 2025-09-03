from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# setup db
DATABASE_URL = "sqlite:///notebooks.db"
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Model of list/ tablet
class Notebook(Base):

    __tablename__ = "notebooks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    link = Column(String, nullable=True)
    name = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    price_discount = Column(Float, nullable=True)

Base.metadata.create_all(bind=engine)

#Flask app
app = Flask(__name__)

@app.route("/")
def hpme():
    return jsonify({"message": "Rozetka Parser API is running!"})

@app.route("/notebooks")
def get_notebooks():
    session = SessionLocal()
    try:
        notebooks = session.query(Notebook).all()
        return jsonify([
            {
                "id": n.id,
                "link": n.link,
                "name": n.name,
                "price": n.price,
                "price_discount": n.price_discount
            }
            for n in notebooks
        ])
    finally:
        session.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)