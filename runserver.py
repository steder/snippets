from snippets.main import app, db

if __name__ == "__main__":
    db.create_all()
    app.run('0.0.0.0', port=5000)
