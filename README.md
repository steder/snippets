# Snippets

## About

Every week, the system emails out a reminder email. Users can reply to
it with what they did that week. Users can follow other users via the
web, as well as following tags, and assigning tags to themselves. All
content matching the tags they follow will be mailed to them in a
digest every Monday afternoon. In addition, archives for each user and
the most recent data for each tag are visible on the web.

## Getting Started

### Install dependencies

#### System Dependencies

 - PostgreSQL 9.3+

#### Application Dependencies

```
pip install -r requirements.txt
npm install
bower install
```

### Configure settings

Mostly you just need to point at your database

```
nano /etc/postgresql/9.3/pg_hba.conf
```

### Configure your db and get started!

```
./manage.py migrate
./manage.py runserver -p 8080
```

### GO GO GO

Point your browser to localhost:8080