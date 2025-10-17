from os import path
from datetime import datetime,timedelta,date
from flask import jsonify, make_response, request,abort,send_from_directory,current_app
from flask_restx import Api, Resource
from sqlalchemy import desc,orm
from ast import literal_eval
from models import db, ShowModel, ShowDateModel, TicketModel, CategoryModel, ReviewModel, UserModel, ShowSessionModel, UserTicketsModel
from schemas import show_schema, show_schemas, popular_shows_schemas, review_schemas, next_week_schemas,session_schema, buy_ticket_schema, index_show_schema, update_show_schema, review_edit_schemas, user_tickets_schema
from modules import upload,multi_upload,remove_game_photos,remove_photo,generate_tickets_pdf
from json import loads

# For Token System
from uuid import uuid4 #Public id to hide user amount in the system itself improving overall security of our database
from jwt import encode, decode
from functools import wraps
from main import secret_key
from werkzeug.security import generate_password_hash, check_password_hash

#API
api = Api(version='Alpha', title='Theater API', description='Main API for GRA-PRO Theater')

revoked_tokens = set()

def clear_revoked_tokens():
    now = datetime.datetime.utcnow().time()
    if now.hour == 0 and now.minute == 0:
        revoked_tokens.clear()
        
# Wrapper function for token validation
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return make_response(jsonify({'message': "Token is missing!"}), 401)
        
        if token in revoked_tokens:
            return make_response(jsonify({"message": "Token has expired. Log in again!"}))
        
        try:
            data = decode(token, secret_key, algorithms="HS256")
            current_user = UserModel.query.filter_by(public_id=data['public_id']).first()
        except:
            return make_response(jsonify({'message': "Token is invalid"}), 401)
        
        return f(*args, current_user=current_user, **kwargs)

    return decorated

def check_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        
        current_user = kwargs.get('current_user', None)
        if not current_user:
            return make_response(jsonify({'message': "Token is missing!"}), 401)
        
        if not current_user.admin:
            return make_response(jsonify({'message': "You do not have permission to access this resource."}), 403)
        
        return f(*args, **kwargs)
    return decorated

### *SYSTEM ACCESS ENDPOINTS*###
#Endpoint for Index page
class Index(Resource):
    def get(self):
        shows = db.session.query(ShowModel).order_by(ShowModel.id.desc()).limit(10)
        
        #Build query for popular shows    
        popular_shows = db.session.query(ShowModel.id, ShowModel.name, TicketModel.sold)\
            .join(TicketModel, ShowModel.id == TicketModel.show_id)\
            .group_by(ShowModel.id, ShowModel.name)\
            .order_by(desc(TicketModel.sold)).limit(5)
        
        #Build query of shows for the next week
        current_date = datetime.now()
        next_week = datetime.now() + timedelta(weeks = 1)
        
        active_shows = db.session.query(ShowModel)\
            .join(ShowSessionModel)\
            .filter(ShowSessionModel.session_date.between(current_date, next_week))\
            .filter(ShowModel.is_active == True)\
            .options(orm.joinedload(ShowModel.sessions))\
            .distinct()\
            .all()
               
        #Build query for last 3 reviews
        reviews = db.session.query(ReviewModel).order_by(ReviewModel.id.desc()).all()
        
        
        #Serialize data
        shows_serialized = index_show_schema.dump(shows)
        ps_serialized = popular_shows_schemas.dump(popular_shows)
        nw_serialized = next_week_schemas.dump(active_shows)
        reviews_serialized = review_schemas.dump(reviews)

        return make_response(jsonify({'shows':shows_serialized,'popular_shows':ps_serialized, 'next_week' : nw_serialized, 'reviews' : reviews_serialized}),200)

#Endpoint for getting all shows & adding shows to database or deleting shows from the database      
class Shows(Resource):
    def get(self):
        # Gathering all shows ordered by their date_added value 
        all_shows= db.session.query(ShowModel.id, ShowModel.name, ShowModel.duration, CategoryModel.name.label('category_name'))\
            .join(CategoryModel, ShowModel.category_id == CategoryModel.id)\
            .order_by(desc(ShowModel.date_added))\
            .all()
        
        all_shows_serialized = show_schemas.dump(all_shows)
        
        return make_response(jsonify({'shows':all_shows_serialized}),200)
    
    @token_required
    @check_admin
    def post(self, current_user):
        json = request.json
        convert_date_added = datetime.strptime(json['date_started'], '%Y-%m-%d')
        convert_date_ended = datetime.strptime(json['date_ended'], '%Y-%m-%d')
        show = ShowModel(name = json['name'],
                            description = json['description'],
                            category_id = json['category_id'], 
                            duration = json['duration'],
                            date_added = datetime.now(),
                            is_active = json['is_active'],
                            show_actors = str(json['actors']),
                            show_stagecrew = str(json['stagecrew']))
        db.session.add(show)
        db.session.flush()
        
        
        dates = ShowDateModel(show_id = show.id, start_date = convert_date_added.date(),end_date = convert_date_ended.date())
        db.session.add(dates)
        
        tickets = TicketModel(show_id = show.id, price = json['ticket_price'])
        db.session.add(tickets)
        
        if "session_date" in json:
            session_time = datetime.strptime(json["session_time"],'%H:%M').time()
            session_date = datetime.strptime(json["session_date"], '%Y-%m-%d')
            show_sessions = ShowSessionModel(show_id = show.id, hall = json["session_hall"], session_date = session_date, session_time = session_time)
            db.session.add(show_sessions)

        
        #Upload Poster Image
        b64_image = json['poster_image']
        upload(b64_image,str(show.id))
        
        #Upload Show Images
        #show_photos = multi_upload(json['show_images'],str(show.id))
        #show.photos = show_photos
        
        
        db.session.commit()
        return make_response(jsonify({'message':'Shows added successfully'}),200)

    @token_required
    @check_admin
    def delete(self, id, current_user):
        show_to_delete = db.session.query(ShowModel).filter_by(id=id).first()
        show_dates_delete = db.session.query(ShowDateModel).filter_by(show_id = id).all()
        show_session_delete = db.session.query(ShowSessionModel).filter_by(show_id = id).all()
        tickets_sold_delete = db.session.query(TicketModel).filter_by(show_id = id).first()
        user_tickets_delete = db.session.query(UserTicketsModel).filter_by(show_id = id).all()
        
        if show_to_delete:
            db.session.delete(show_to_delete)
            db.session.delete(tickets_sold_delete)
            
            if show_dates_delete:
                for show_date in show_dates_delete:
                    db.session.delete(show_date)
            
            if show_session_delete:
                for show_session in show_session_delete:
                    db.session.delete(show_session)
            
            if user_tickets_delete:
                for user_ticket in user_tickets_delete:
                    db.session.delete(user_ticket)
                
            remove_game_photos(show_to_delete.id)
             
            db.session.commit()
            return make_response(jsonify({"message": "Show deleted successfully !"}) ,200)

        else:
            return make_response(jsonify({"message": "This show doesn't exist !"}))

class UpdateShow(Resource):
    @token_required
    @check_admin
    def get(self, id,current_user):
        update_show = db.session.query(
            ShowModel.id,
            ShowModel.name,
            ShowModel.description,
            ShowModel.duration,
            CategoryModel.id.label('category_id'),
            CategoryModel.name.label('category_name'),
            ShowDateModel.start_date,
            ShowDateModel.end_date,
            TicketModel.price,
            ShowModel.show_actors,
            ShowModel.show_stagecrew
        ).filter_by(id=id).first()


        if update_show is None:
            return make_response(jsonify({'error': 'Show not found'}), 404)
        
        update_show_serialized = update_show_schema.dump(update_show)

        return make_response(jsonify(update_show_serialized), 200)
    
    @token_required
    @check_admin
    def post(self, id, current_user):
        show_to_update = ShowModel.query.filter_by(id=id).first()
        price_to_update = TicketModel.query.filter_by(show_id=id).first()
        dates_to_update = ShowDateModel.query.filter_by(show_id=id).first()
        
        if show_to_update is None:
            return make_response(jsonify({'error': 'Show not found'}), 404)

        data = request.json

        show_to_update.name = data['name']
        show_to_update.description = data['description']
        show_to_update.duration = data['duration']
        show_to_update.category_id = data['category_id']
        show_to_update.show_actors = data['actors']
        show_to_update.show_stagecrew = data['stagecrew']
        
        price_to_update.price = data['price']
        dates_to_update.start_date = datetime.strptime(data['start_date'], "%Y-%m-%d")
        dates_to_update.end_date = datetime.strptime(data['end_date'], "%Y-%m-%d")
        
        # Update the show attributes based on the incoming JSON data
        """show_to_update.name = data.get('name', show_to_update.name)
        show_to_update.description = data.get('description', show_to_update.description)
        show_to_update.duration = data.get('duration', show_to_update.duration)
        show_to_update.category_id = data.get('category_id', show_to_update.category_id)
        show_to_update.show_actors = str(data.get('show_actors', show_to_update.show_actors))
        show_to_update.show_stagecrew = str(data.get('show_stagecrew', show_to_update.show_stagecrew))

        price_to_update.price = data.get('price', price_to_update.price)
        
        dates_to_update.start_date = datetime.strptime(data.get('start_date', dates_to_update.start_date), "%Y-%m-%d")
        dates_to_update.end_date = datetime.strptime(data.get('end_date', dates_to_update.end_date), "%Y-%m-%d")"""
                
        # Commit the changes to the database
        db.session.commit()

        return jsonify({'message': 'Show updated successfully'})
 
#Show Image
class ServeImage(Resource):
    def get(self, setname, filename):
        # Get the upload set config for the given set name
        upload_set_config = current_app.upload_set_config.get(setname)
        if upload_set_config is None:
            abort(404, f"No configuration found for set name '{setname}'")
        
        # Save the original destination so we can restore it later
        original_destination = upload_set_config.destination
        
        # Determine the type of image being requested
        if setname == 'photos':
            if 'banner' in filename:
                # Return the banner image for the popular shows
                send_image = send_from_directory(upload_set_config.destination + '/show_banners/', filename)
                upload_set_config.destination = original_destination
                return send_image
            else:
                # Return the image for a specific show
                show_dir = filename.split('_')[0] if '_thumbnail' in filename else filename.split('.')[0]
                if '_' in show_dir:
                    show_id = show_dir.split('_')[0]
                    filename = show_dir + '.png'
                    show_directory = path.join(original_destination, "shows", show_id)
                else:
                    show_directory = path.join(original_destination, "shows", show_dir)
                if not path.isdir(show_directory):
                    abort(404, f"No directory found for show ID '{show_dir}'")
                send_image = send_from_directory(show_directory, filename)
                upload_set_config.destination = original_destination
                return send_image
        
        # If we get here, it means the requested image type is not supported                    
        abort(404, f"Unsupported image type '{setname}'")
    
#Endpoint for getting show details    
class ShowDetail(Resource):
    def get(self,id):
        show = db.session.query(ShowModel).filter_by(id=id).first()
        if show:
            show_serialized = show_schema.dump(show)
            return make_response(jsonify({'show':show_serialized}),200)
        abort(404)

#Endpoint for adding a review
class AddReview(Resource):
    @token_required
    @check_admin
    def post(self,current_user):
        json = request.json
        review = ReviewModel(author = json['author'],
                            title = json['title'],
                            content = json['content'])
        db.session.add(review)
        db.session.commit()

        return make_response(jsonify({'message': "Review added successfully !"}))
    
#Endpoint for updating a review        
class UpdateReview(Resource):
    @token_required
    @check_admin
    def get(self, id,current_user):
        review_to_update = ReviewModel.query.filter_by(id=id).first()

        if review_to_update is None:
            return make_response(jsonify({'Message': "Review not found !"}))
        
        review_serialized = review_edit_schemas.dump(review_to_update)
        return make_response(jsonify(review_serialized))
    
    @token_required
    @check_admin
    def post(self, id,current_user):
        review_to_update = ReviewModel.query.filter_by(id=id).first()
        if review_to_update is None:
            return make_response(jsonify({'Message': "Review not found !"}))
        
        data = request.json
        review_to_update.author = data.get('author', review_to_update.author)
        review_to_update.title = data.get('title', review_to_update.title)
        review_to_update.content = data.get('content', review_to_update.content)
        
        db.session.commit()
        return make_response(jsonify({'message': 'Review updated successfully'}))
    
    @token_required
    @check_admin
    def delete(self, id,current_user):
        review_to_update = ReviewModel.query.filter_by(id=id).first()
        
        if review_to_update:
            db.session.delete(review_to_update)
            db.session.commit()
            return make_response(jsonify({'message': "This review has been deleted !"}))
        
        else:
            return make_response(jsonify({'message': "Review not found !"}))
        
#Calendar
class Calendar(Resource):
    def get(self):
        active_shows = ShowModel.query.filter_by(is_active=True).options(
        orm.joinedload(ShowModel.sessions)).all()

        result = []
        for show in active_shows:
            show_data = {"show_id": show.id, "name": show.name, "sessions": []}
            for session in show.sessions:
                date_str = session.session_date.strftime("%Y-%m-%d")
                show_data["sessions"].append({
                    date_str: {
                        "session_id": session.id,
                        "time": session.session_time.strftime("%H:%M:%S")
                    }
                })
            result.append(show_data)

        return jsonify({'calendar_shows': result})
  
#Buy Ticket   
class BuyTicket(Resource): 
    @token_required
    def get(self, id, current_user):
        #Find Show By ID
        today = date.today()
        show = db.session.query(ShowModel).join(ShowModel.sessions).options(orm.joinedload(ShowModel.tickets_sold)).filter(ShowSessionModel.session_date >= today, ShowModel.id == id).first()
        
        if show:
            """available_seatlist = literal_eval(show.sessions[0].seats_available)
            
            balcony_seats = list()
            middle_seats = list()
            left_seats = list()
            right_seats = list()
            
            for seat in available_seatlist:
                if "B" in seat:
                    balcony_seats.append(seat)
                elif "M" in seat:
                    middle_seats.append(seat)
                elif "R" in seat:
                    right_seats.append(seat)
                elif "L" in seat:
                    left_seats.append(seat)
            
            expensive_seats = list()
            normal_seats = list()
            cheap_seats = list()
            
            for left_seat in left_seats:
                if int(left_seat[1:]) <= 14:
                    expensive_seats.append(left_seat)
                
                elif int(left_seat[1:]) > 14:
                    normal_seats.append(left_seat)
            
            for middle_seat in middle_seats:
                if int(middle_seat[1:]) <= 14:
                    expensive_seats.append(middle_seat)
                
                elif int(middle_seat[1:]) > 14 and int(middle_seat[1:]) <= 35:
                    normal_seats.append(middle_seat)
                
                elif int(middle_seat[1:]) > 35:
                    cheap_seats.append(middle_seat)
            
            
            for right_seat in right_seats:
                if int(middle_seat[1:]) <= 14:
                    expensive_seats.append(right_seat)
                
                elif int(right_seat[1:]) > 14:
                    normal_seats.append(right_seat)
            
            for balcony_seat in balcony_seats:
                if int(balcony_seat[1:]) <= 20:
                    expensive_seats.append(balcony_seat)
                
                elif int(balcony_seat[1:]) > 20 and int(balcony_seat[1:]) <= 60:
                    normal_seats.append(balcony_seat)
                
                elif int(balcony_seat[1:]) > 60 and int(balcony_seat[1:]) <= 90:
                    cheap_seats.append(balcony_seat)
            
            price = show.tickets_sold.price
            
            seat_prices = {str(price + (price * 20 / 100)): expensive_seats, str(price): normal_seats, str(price - (price * 20 / 100)): cheap_seats}"""
            
            price = show.tickets_sold.price
            buy_ticket_schema.price = price
            return make_response(jsonify(buy_ticket_schema.dump(show)),200)
        
        return make_response(jsonify({'message':'Session not found'}),404)
        
        
        
    @token_required
    def post(self, current_user):
        
        ticket_data = request.json
        tickets = list()
        
        # Get both taken seats and available seats as 'row' value type
        seats_taken_row = ShowSessionModel.query.with_entities(ShowSessionModel.seats_taken).filter_by(id = ticket_data['session_id']).first()
        seats_available_row = ShowSessionModel.query.with_entities(ShowSessionModel.seats_available).filter_by(id = ticket_data['session_id']).first()
        
        if seats_taken_row is None or seats_available_row is None:
            return make_response(jsonify({'message': "Session not found !"}),422)
        
        seats_taken_list = literal_eval(seats_taken_row[0])
        seats_available_list = literal_eval(seats_available_row[0])
        
        customer_name = current_user.name
        show_name = ShowModel.query.with_entities(ShowModel.name).filter_by(id = ticket_data["show_id"]).first()
        session_date = ShowSessionModel.query.with_entities(ShowSessionModel.session_date).filter_by(id = ticket_data["session_id"]).first()
        session_time = ShowSessionModel.query.with_entities(ShowSessionModel.session_time).filter_by(id = ticket_data["session_id"]).first()
        session_time = ShowSessionModel.query.with_entities(ShowSessionModel.session_time).filter_by(id = ticket_data["session_id"]).first()
        session_hall = ShowSessionModel.query.with_entities(ShowSessionModel.hall).filter_by(id = ticket_data["session_id"]).first()
        
        for seat in ticket_data["seats"]:
            if seat in seats_available_list:
                seats_available_list.remove(seat)
                seats_taken_list.append(seat)

                ticket = {"Name": customer_name,
                          "Seat": seat,
                          "Show": str(show_name[0]),
                          "Date": str(session_date[0]),
                          "Session Time": str(session_time[0]),
                          "Session Hall" : str(session_hall[0]),
                          "Ticket Price": ticket_data['sold_price']
                          }
                
                tickets.append(ticket)
            else:
                return make_response(jsonify({"message": "This seat is already taken"}))
        db.session.query(ShowSessionModel).filter_by(id = ticket_data['session_id']).update({"seats_taken": str(seats_taken_list), "seats_available": str(seats_available_list)})
        
        # Get total amount of tickets sold for this show
        tickets_sold_amount = TicketModel.query.with_entities(TicketModel.sold).filter_by(show_id = ticket_data["show_id"]).first()
        
        new_sold_amount = int(tickets_sold_amount[0]) + len(ticket_data["seats"])
        
        db.session.query(TicketModel).filter_by(show_id=ticket_data["show_id"]).update({"sold": new_sold_amount})
        
        
        new_ticket = UserTicketsModel(
                            user_id = current_user.id,
                            show_id = ticket_data['show_id'],
                            session_id = ticket_data['session_id'],
                            seats = str(ticket_data['seats']),
                            hall = str(session_hall[0]),
                            sold_price = ticket_data['sold_price']
                            )
        
                
        db.session.add(new_ticket)
        db.session.flush()
        
        tickets_bought = new_ticket.__dict__
        
        print(tickets_bought)
        
        generate_tickets_pdf(str(show_name[0]),str(session_date[0],),str(session_time[0]),current_user.public_id,tickets_bought)
        
        db.session.commit()
        
        return jsonify(tickets)
                  
#Manage Sessions
class ManageSessions(Resource):
    
    @token_required
    @check_admin
    def get(self, id, current_user):

        session = db.session.query(ShowSessionModel, ShowModel.name).join(ShowModel, ShowModel.id == ShowSessionModel.show_id)\
            .filter(ShowModel.is_active == True, ShowSessionModel.id == id).first()
            
        if session:
            # Convert the query result to a Python dictionary using the QueryResultSchema
            session_serialized = session_schema.dump(session[0])

            # Add the show name to the dictionary
            session_serialized['show_name'] = session[1]
            return make_response(jsonify(session_serialized),200)
        abort(404)
        
    @token_required
    @check_admin
    def post(self, current_user):
        session_data = request.json
        session_date = datetime.strptime(session_data['session_date'], '%Y-%m-%d').date()
        session_time = datetime.strptime(session_data['session_time'], '%H:%M').time()
        session = ShowSessionModel(
                            show_id = session_data['id'],
                            hall = session_data["session_hall"],
                            session_date = session_date,
                            session_time = session_time)
        db.session.add(session)
        db.session.commit()
        return make_response(jsonify({"message" : "Seans başarıyla eklendi!"}),200)
 
    @token_required
    @check_admin
    def delete(self, id, current_user):
        session_to_delete = ShowSessionModel.query.filter_by(id=id).first()
        
        if session_to_delete:
            db.session.delete(session_to_delete)
            db.session.commit()
            return make_response(jsonify({'message': "This session has been deleted !"}))
        
        else:
            return make_response(jsonify({'message': "Session not found !"}))
    
###*USER ACCOUNT OPERATIONS*###
#Endpoint for Login
class Login(Resource):
    def post(self):
        
        if 'x-access-token' in request.headers:
            return make_response(jsonify({'message': 'You are already logged in!'}))
        
        entered_user = request.get_json()
        
        if not entered_user or not entered_user["email"] or not entered_user["password"]:
            return make_response("Couldn't verify !", 401)
    
        user = UserModel.query.filter_by(email=entered_user["email"]).first()
        user_data = [user.name, user.email, user.public_id, user.admin]

        if not user:
            return make_response("Couldn't verify !", 401)
    
        if check_password_hash(user.password, entered_user["password"]):
            token = encode({'public_id': user.public_id, 'exp': datetime.utcnow() + timedelta(minutes=30)}, secret_key, algorithm="HS256")
            response = make_response(jsonify({'message': "You've Logged in succesfully !"}))
            response.headers.add('user-data',user_data)
            response.headers.add('x-access-token',token)
            
        return response

#Logout User
class Logout(Resource):
    @token_required
    def post(self,current_user):
            token = request.headers.get("x-access-token")
            if token:
                revoked_tokens.add(token)  
                return jsonify({'message': 'Successfully logged out.'})
                
            else:
                return jsonify({'message': 'You cannot logout without logging in !'})
            
#Endpoint for registering new users
class Register(Resource):
    def post(self):
        data = request.get_json()
        
        hashed_password = generate_password_hash(data['password'], method = 'SHA256')
        new_user = UserModel(public_id = str(uuid4()), name=data['name'], email=data['email'], password = hashed_password, admin = False)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': "You've registered successfully"})

#Endpoint for getting all users
class GetAllUsers(Resource):
    @token_required 
    @check_admin
    def get(self, current_user):
    
        users = UserModel.query.all()
        output = []
        for user in users:
            user_data = dict()
            user_data['public_id'] = user.public_id
            user_data['name'] = user.name
            user_data['email'] = user.email
            user_data['password'] = user.password
            user_data['admin'] = user.admin
            output.append(user_data)
            
        return make_response(jsonify(output))

    @token_required
    @check_admin
    def delete(self, public_id, current_user):
        user_to_delete = db.session.query(UserModel).filter_by(public_id = public_id).first()
        tickets_to_delete = db.session.query(UserTicketsModel).filter_by(user_id = user_to_delete.id).all()
        
        if user_to_delete:
            db.session.delete(user_to_delete)
            
            if tickets_to_delete:
                for ticket in tickets_to_delete:
                    db.session.delete(ticket)
             
            db.session.commit()
            return make_response(jsonify({"message": "User deleted successfully !"}) ,200)

        else:
            return make_response(jsonify({"message": "This user doesn't exist !"}))
        
#Promote User
class PromoteUsers(Resource):
    @token_required
    @check_admin
    def put(self, current_user, public_id):
        user = UserModel.query.filter_by(public_id=public_id).first()
    
        if not user:
            return jsonify({'message': "This user doesn't exist."})
        
        if user.admin == True:
            return jsonify({'message': "This user is already an admin."})   
            
        else:
            user.admin = True
            db.session.commit()
            
            return jsonify({'message': "This user has been promoted."})      

#Demote User
class DemoteUsers(Resource):
    @token_required
    @check_admin
    def put(self, current_user, public_id):
        user = UserModel.query.filter_by(public_id=public_id).first()
    
        if not user:
            return jsonify({'message': "This user doesn't exist."})
        
        if user.admin == False:
            return jsonify({'message': "This user is a normal user already !"})     
        
        else:
            user.admin = False
            db.session.commit()
            return jsonify({'message': "This user has been demoted."})      

#Serve User's Tickets
class MyTickets(Resource):

    @token_required
    def get(self, current_user):
        user_tickets = UserTicketsModel.query \
            .join(ShowSessionModel, UserTicketsModel.session_id == ShowSessionModel.id) \
            .join(ShowModel, ShowSessionModel.show_id == ShowModel.id) \
            .filter(UserTicketsModel.user_id == current_user.id) \
            .with_entities(
                ShowModel.name.label('show_name'),
                ShowSessionModel.session_date,
                ShowSessionModel.session_time,
                ShowSessionModel.id.label('session_id'),
                UserTicketsModel.date_sold,
                UserTicketsModel.seats,
                UserTicketsModel.sold_price,
                UserTicketsModel.id
            ) \
            .all()

        tickets_data = []
        for ticket in user_tickets:
            ticket_data = {
                'ticket_id': ticket.id,
                'show_name': ticket.show_name,
                'session_date': ticket.session_date.strftime("%Y-%m-%d"),
                'session_time': ticket.session_time.strftime("%H:%M:%S"),
                'date_sold': ticket.date_sold.strftime("%Y-%m-%dT%H:%M:%S"),
                'seats': ticket.seats,
                'sold_price': ticket.sold_price,
                'sesion_id': ticket.session_id
            }
            tickets_data.append(ticket_data)

        return make_response(jsonify(tickets_data))
    
class ServeTicket(Resource):
    @token_required
    def get(self, current_user, session_id):
        upload_set_config = current_app.upload_set_config.get("documents")
        if upload_set_config is None:
            abort(404, f"No configuration found for set name documents")
        # Save the original destination so we can restore it later
        #original_destination = upload_set_config.destination

        ticket_path = path.join('ticket',current_user.public_id,str(session_id))
        # Return the ticket
        send_ticket = send_from_directory(upload_set_config.destination + '/' +ticket_path, 'tickets.pdf')
        return send_ticket
    
###* FUNCTIONALITY ENDPOINTS*###       
#Class for uplodading show images manually
class UploadBanner(Resource):
    @token_required
    @check_admin
    def post(self,current_user):
        data = request.json
        id = data['show_id'] + "_banner"
        banner = data['banner']
        return upload(banner,id)

class MultiImageUpload(Resource):
    
    @token_required
    @check_admin
    def get(self, id,current_user):
        show = db.session.query(ShowModel).filter_by(id=id).first()
        if show:
            show_serialized = show_schema.dump(show)
            return make_response(jsonify(show_serialized),200)
    
    @token_required
    @check_admin
    def post(self,current_user):
        data = request.json
        show = db.session.query(ShowModel).filter_by(id=data['id']).first()
        count = (lambda show: 0 if show.photos is None else len(show.photos.split(',')))(show)
        
        if show:
            image_names = multi_upload(data['images'], show.id, count)
            if show.photos is None:
                show.photos = ",".join(image_names)
            else:
                show.photos += "," + ",".join(image_names)
            
            db.session.commit()
            return make_response(jsonify({"message": "Images uploaded successfully!"}), 200)
        
        return make_response(jsonify({"message": "Show not found!"}), 404)

class DeletePhoto(Resource):
    @token_required
    @check_admin
    def get(self, current_user, id):
        photos = db.session.query(ShowModel.photos).filter_by(id=id).first()
        print(photos)
        if photos:
            return make_response(jsonify([photos[0]]), 200)
        else:
            return make_response(jsonify({"message": "Show not found!"}), 404)
    
    @token_required
    @check_admin
    def delete(self, current_user):
        print(request.data)
        decoded_data = request.data.decode("utf-8")
        parsed_data = loads(decoded_data)
        split_data = [item for item in parsed_data]
        remove_photo(split_data)
        id =  split_data[0].split("_")[0]
        show = db.session.query(ShowModel).filter_by(id=id).first()
        photos = show.photos.split(',')
        for photo in split_data:
            photos.remove(photo)
            photos_str = str(photos).replace('[','').replace(']','').replace(' ','').replace("'","").replace("'","")
            
        show.photos = photos_str
        db.session.commit()
        return make_response(jsonify({"message": "Photo deleted successfully!"}), 200)