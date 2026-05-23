import os


# Keep test collection independent from local or production database settings.
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "False"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
