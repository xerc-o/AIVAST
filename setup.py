from setuptools import setup, find_packages

setup(
    name='aivast',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'flask',
        'groq',
        'Flask-Login',
        'Flask-SQLAlchemy',
        'python-dotenv',
        'requests',
        'SQLAlchemy',
        'alembic',
        'gunicorn',
        'pytest',
        'Werkzeug',
        'python-libnmap',
        'beautifulsoup4',
    ],
    entry_points={
        'flask.commands': [
            'create-db=app:create_db_command',
        ],
    },
)
