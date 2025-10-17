from models import ShowModel, TicketModel, ReviewModel, UserModel, ShowSessionModel, UserTicketsModel
from main import ma
from marshmallow import fields, post_dump


#Define Schemas 
class TicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TicketModel

class ShowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ShowModel
    category_name = fields.String()

class UpdateShowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ShowModel
        fields = ("id", "name", "description", "duration", "category_id", "category_name", "start_date", "end_date", "price", "show_actors", "show_stagecrew")
        #exclude = ('photos', 'rating', 'date_added', 'is_active')

class PopularShowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ShowModel
    sold = fields.Integer()
    
class ReviewSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ReviewModel

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel 

class ShowWithSessionsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ShowModel
        fields = ("name", "date_started", "date_ended", "sessions")

    date_started = fields.DateTime(attribute="start_date")
    date_ended = fields.DateTime(attribute="end_date")
    sessions = fields.List(fields.DateTime)
    
class NextWeekShowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ShowModel
        exclude = ('date_added','description','is_active','rating','sessions.seats_available','sessions.seats_taken','show_actors','show_stagecrew')
    sessions = fields.Nested("ShowSessionSchema", many=True)
    session_date = fields.DateTime(attribute="sessions.show_date.date")
    session_time = fields.Time(attribute="sessions.show_date.time")

class ShowSessionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ShowSessionModel
    show_name = fields.String(attribute="show.name")
            
class UserTicketsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserTicketsModel

class BuyTicketSchema(ma.SQLAlchemyAutoSchema):
    price = fields.Float()

    class Meta:
        model = ShowModel
        fields = ('id', 'name', 'description', 'category_id', 'rating', 'duration', 'date_added', 'is_active', 'photos', 'show_actors', 'show_stagecrew', 'sessions', 'price')
        include_fk = True
        load_instance = True

    sessions = fields.Nested("ShowSessionSchema", many=True)
    
    def __init__(self, *args, **kwargs):
        self.price = kwargs.pop('price', None)
        super().__init__(*args, **kwargs)
    
    @post_dump
    def add_price_to_dump(self, data, **kwargs):
        data['price'] = self.price
        return data
 
class IndexShowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ShowModel
        exclude = ('date_added','description','is_active','photos','rating','show_actors','show_stagecrew')

class MyTicketsSchema(ma.SQLAlchemyAutoSchema):
    class Meta: 
        model = UserTicketsModel
    shows = fields.Nested("ShowSchema", many=True)
    show_name = fields.String(attribute="show.name")
        
#Initialize Schemas
show_schema = ShowSchema()
show_schemas = ShowSchema(many=True)
update_show_schema = UpdateShowSchema()
popular_shows_schemas = PopularShowSchema(many=True)
ticket_schemas = TicketSchema(many=True)
review_schemas = ReviewSchema(many=True)
review_edit_schemas = ReviewSchema()
users_schema = UserSchema(many=True)
user_schema = UserSchema()
session_schema = ShowSessionSchema()
next_week_schemas = NextWeekShowSchema(many = True)
usertickets_schemas = UserTicketsSchema()
buy_ticket_schema = BuyTicketSchema()
index_show_schema = IndexShowSchema(many=True)
user_tickets_schema = UserTicketsSchema(many=True)
myticket_schema = MyTicketsSchema(many = True)