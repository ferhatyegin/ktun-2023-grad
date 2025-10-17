from flask_sqlalchemy import SQLAlchemy
from json import dumps

db = SQLAlchemy()

class UserModel(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True, info = {'description': "Kullanici ID'si"})
    public_id = db.Column(db.String(50), unique = True)
    name = db.Column(db.String, nullable = False, info = {'description': "Kullanıcı Adı"})
    password = db.Column(db.String(80), nullable = False)
    admin = db.Column(db.Boolean, default = False)
    email = db.Column(db.String, nullable = False, info = {'desccription': "Kullanıcı E-Mail Adresi"})
    
    user_tickets = db.relationship("UserTicketsModel", backref= "u_id", lazy = True)

class CategoryModel(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key = True, info = {'description': "Kategori ID'si"})
    name = db.Column(db.String, nullable = False, info = {'description': "Kategori İsmi"})
    
    category = db.relationship("ShowModel", backref= "categories", uselist = False)
    
    def __repr__(self):
        return self.name
        
class ShowModel(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer, primary_key = True, info = {'description': "Tiyatro Oyun ID'si"})
    name = db.Column(db.String, nullable = False, info = {'description' : 'Tiyato Oyunlarının İsmi'})
    description = db.Column(db.String, nullable = False, info = {'description': 'Tiyatro Oyunu Açıklaması'})
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable = False, info = {'description' : 'Oyun Kategorisi'})
    rating = db.Column(db.Float, nullable = False, default = 0, info = {'description' : 'Oyun Puanı'})    
    duration = db.Column(db.Integer, nullable = False,  info = {'description' : 'Tiyatro Oyununun Süresi'})
    date_added = db.Column(db.DateTime(timezone = True), server_default = db.func.now(), nullable = False,  info = {'description' : 'Tiyatro Oyununun Eklenme Tarihi'})
    is_active = db.Column(db.Boolean, nullable = True, info = {'description': 'Güncel Olma Durumu'})
    photos = db.Column(db.String, nullable = True, info = {'description': 'Tiyatro Oyununun Fotoğrafları'})
    show_actors = db.Column(db.String, nullable = True, info = {'description': "Tiyatro oyunun oyuncu ekbi"})
    show_stagecrew = db.Column(db.String, nullable = True, info = {'description': "Tiyatro oyununun sahne ekibi"})
    
    
    tickets_sold = db.relationship("TicketModel", backref = "tickets_sold", uselist = False)
    show_dates = db.relationship("ShowDateModel", backref = "show_dates", uselist = False)
    sessions = db.relationship("ShowSessionModel", backref = "show_session", lazy = True)
    user_tickets = db.relationship("UserTicketsModel", backref = "sh_id", lazy = True)

class ShowDateModel(db.Model):
    __tablename__ = "show_dates"
    id = db.Column(db.Integer, primary_key = True, info = {'description': 'Date ID'})
    show_id = db.Column(db.Integer, db.ForeignKey("shows.id"), nullable = False, info = {'description': 'Show ID'})
    start_date = db.Column(db.Date, nullable = False,  info = {'description' : 'Tiyatro Oyununun Başlangıç Tarihi'})
    end_date = db.Column(db.Date, nullable = False,  info = {'description' : 'Tiyatro Oyunun Bitiş Tarihi'})
    
seats_available = dumps(['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 
                  'L11', 'L12', 'L13', 'L14', 'L15', 'L16', 'L17', 'L18', 'L19', 'L20', 
                  'L21', 'L22', 'L23', 'L24', 'L25', 'L26', 'L27', 'L28', 'L29', 'L30',
                  'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 
                  'M11', 'M12', 'M13', 'M14', 'M15', 'M16', 'M17', 'M18', 'M19', 'M20', 
                  'M21', 'M22', 'M23', 'M24', 'M25', 'M26', 'M27', 'M28', 'M29', 'M30',
                  'M31', 'M32', 'M33', 'M34', 'M35', 'M36', 'M37', 'M38', 'M39', 'M40', 
                  'M41', 'M42', 'M43', 'M44', 'M45', 'M46', 'M47', 'M48', 'M49', 'M50', 
                  'M51', 'M52', 'M53', 'M54', 'M55', 'M56', 'M57', 'M58', 'M59', 'M60',
                  'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 
                  'R11', 'R12', 'R13', 'R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R20', 
                  'R21', 'R22', 'R23', 'R24', 'R25', 'R26', 'R27', 'R28', 'R29', 'R30',
                  'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 
                  'B11', 'B12', 'B13', 'B14', 'B15', 'B16', 'B17', 'B18', 'B19', 'B20', 
                  'B21', 'B22', 'B23', 'B24', 'B25', 'B26', 'B27', 'B28', 'B29', 'B30',
                  'B31', 'B32', 'B33', 'B34', 'B35', 'B36', 'B37', 'B38', 'B39', 'B40', 
                  'B41', 'B42', 'B43', 'B44', 'B45', 'B46', 'B47', 'B48', 'B49', 'B50', 
                  'B51', 'B52', 'B53', 'B54', 'B55', 'B56', 'B57', 'B58', 'B59', 'B60', 
                  'B61', 'B62', 'B63', 'B64', 'B65', 'B66', 'B67', 'B68', 'B69', 'B70',
                  'B71', 'B72', 'B73', 'B74', 'B75', 'B76', 'B77', 'B78', 'B79', 'B80', 
                  'B81', 'B82', 'B83', 'B84', 'B85', 'B86', 'B87', 'B88', 'B89', 'B90'])

class ShowSessionModel(db.Model):   
    __tablename__ = "show_session"   
    id = db.Column(db.Integer, primary_key = True, info = {"description": "Primary Key ID"})
    show_id = db.Column(db.Integer, db.ForeignKey("shows.id"), nullable = False, info = {"description": "Alakalı Oyun ID'si"})
    hall = db.Column(db.String, nullable = True, info = {"description": "Alakalı Oyunun Oynanacağı Salon"})
    session_date = db.Column(db.Date, nullable = False, info = {"description": "Oynanacak Oyunun Gösterim Tarihi"})
    session_time = db.Column(db.Time, nullable = False, info = {'description': 'Alakalı Oyunun Oynanacağı Zaman ve Saat'}) 
    seats_taken = db.Column(db.String, nullable = False, default = str([]) ,  info = {"description": "Alakalı seansın alınmış koltukları"})
    seats_available = db.Column(db.String, nullable = False, default = seats_available ,info = {"description": "Alakalı seansın alınmamış koltukları"})
    
    user_tickets = db.relationship("UserTicketsModel", backref = "show_session", lazy = True)
    
class TicketModel(db.Model):
    __tablename__ = "tickets_sold"
    id = db.Column(db.Integer, primary_key = True, info = {'description': "Table Primary Key"})
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable = False, info = {"description": "Oyun ID"})
    sold = db.Column(db.Integer, nullable = True, default = 0, info = {'description': "Alakalı Oyunun Satmış Olduğu Toplam Bilet Sayısı"})
    price = db.Column(db.Float, nullable = False, info = {'description': 'Bilet Temel Fiyat'})  

class ReviewModel(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key = True, info = {'description': "Yorum ID'si"})
    author = db.Column(db.String, nullable= False, info = {'description': "Yorumun Yazarı"})
    title = db.Column(db.String, nullable = False, info = {'description': "Yorum Başlığı"})
    content = db.Column(db.String, nullable = False, info = {'description': "Yorum İçeriği"})
   
class UserTicketsModel(db.Model):
    __tablename__ = "user_tickets"
    id = db.Column(db.Integer, primary_key = True, info = {'description': "Kayıt ID'si"})
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False, info = {'description': "Bilet alan kullanıcı ID'si"})
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable = False, info = {'description': "Kullanıcın izlediği oyun ID'si"}) 
    session_id = db.Column(db.Integer, db.ForeignKey('show_session.id'), nullable = False, info = {'description': "Alakalı oyunun seans ID'si"})
    date_sold = db.Column(db.DateTime(timezone = True), server_default = db.func.now(), nullable = False, info = {'description': "Biletin alındığı tarih ve zaman"})
    seats = db.Column(db.String, nullable = False, info = {'description': "Kullanıcının almış olduğu koltuklar."})
    hall = db.Column(db.String, nullable = True, info = {"description": "Alakalı Oyunun Oynanacağı Salon"})
    sold_price = db.Column(db.Float, nullable = False, info = {'description': "Kullanıcının ödediği toplam değer."})