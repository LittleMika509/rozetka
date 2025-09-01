from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# setup db
DATABASE_URL = "sqlite:///notebooks.db"
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Model of list/ tablet
class Notebook(Base):

    __tablename__ = "notebooks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    price = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

#Flask app
app = Flask(__name__)

@app.route("/")
def hpme():
    return {"message": "Rozetka Parser API is running!"}

@app.route("/notebooks")
def get_notebooks():
    session = SessionLocal()
    notebooks = session.query.all()
    session.close()
    return jsonify([{"id": n.id, "title": n.title, "price": n.price} for n in notebooks])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)