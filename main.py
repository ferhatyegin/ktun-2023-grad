from os import path,urandom
from flask import Flask,redirect,url_for
from flask_cors import CORS
from flask_uploads import UploadSet,configure_uploads,IMAGES,DOCUMENTS
#App
app = Flask(__name__)

#Initialize CORS
CORS(app, expose_headers=['x-access-token','user-data'])

#DB Config
db_path = path.join(path.dirname(__file__), 'database.db')
db_uri = 'sqlite:///{}'.format(db_path)
secret_key = app.config["SECRET_KEY"] = urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

#Initialize Database
from models import db
db.init_app(app)

#Database Migration
from flask_migrate import Migrate
migrate = Migrate(app,db,render_as_batch=True)

#Import Marshmallow
from flask_marshmallow import Marshmallow
ma = Marshmallow(app)

#Flask_uploads
photos = UploadSet('photos', IMAGES)
documents = UploadSet('documents', DOCUMENTS)
app.config['UPLOADS_AUTOSERVE'] = True

#Base Directory For Image & File Uploads
basedir = path.abspath(path.dirname(__file__))
app.config['UPLOADED_PHOTOS_DEST'] = path.join(basedir, 'static', 'img')
app.config['UPLOADED_DOCUMENTS_DEST'] = path.join(basedir, 'static', 'doc')
configure_uploads(app, upload_sets=[photos,documents])

#Redirect to index
@app.route('/')
def landing_page():
    return redirect(url_for('index'))

#Override default 404 response
@app.errorhandler(404)
def page_not_found(e):
    import error_handlers
    return error_handlers.handle_not_found(e)

#Start app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        from routes import api
        api.init_app(app, add_specs=False, doc=False)
    app.run(debug=True)
    
   