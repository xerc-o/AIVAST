from setuptools import setup, find_packages

setup(
    name='aivast',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'flask==2.3.3',
        'groq',
        'Flask-Login==0.6.3',
        'Flask-SQLAlchemy==3.1.1',
        'python-dotenv==1.0.1',
        'requests==2.31.0',
        'SQLAlchemy>=2.0.36',
        'alembic==1.13.1',
        'gunicorn==21.2.0',
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
