from views import api, Index, Shows, ShowDetail, Login, Register, \
        GetAllUsers, PromoteUsers, ServeImage, UploadBanner, Calendar, \
        DemoteUsers, Logout, ManageSessions, BuyTicket, MultiImageUpload, \
        UpdateShow, UpdateReview, AddReview, MyTickets, DeletePhoto,ServeTicket
from werkzeug.exceptions import HTTPException,Forbidden,Unauthorized
from sqlalchemy.exc import IntegrityError,StatementError

#Add Resources
api.add_resource(Index,'/index')
api.add_resource(Shows, '/shows', '/shows/delete/<int:id>')
api.add_resource(ShowDetail, '/show/detail/<int:id>')
api.add_resource(Calendar,'/calendar')
api.add_resource(ManageSessions, '/manage_sessions','/manage_sessions/<int:id>')
api.add_resource(BuyTicket, '/buyticket/<int:id>','/buyticket')
api.add_resource(MyTickets, '/mytickets')

api.add_resource(AddReview,'/review_add')
api.add_resource(UpdateShow, '/show_update/<int:id>')
api.add_resource(UpdateReview,'/review_update/<int:id>') 

api.add_resource(Login, '/login')
api.add_resource(Logout,'/logout')
api.add_resource(Register, '/register')

api.add_resource(GetAllUsers, '/getallusers', '/getallusers/<string:public_id>')
api.add_resource(PromoteUsers, '/promoteusers/<string:public_id>')
api.add_resource(DemoteUsers, '/demoteusers/<string:public_id>')

api.add_resource(ServeImage,'/uploads/<setname>/<filename>')
api.add_resource(ServeTicket,'/documents/<int:session_id>')
api.add_resource(MultiImageUpload, '/multi_upload','/multi_upload/<int:id>')
api.add_resource(UploadBanner,'/upload_banner')
api.add_resource(DeletePhoto,'/delete_photo', '/delete_photo/<int:id>')


# Import error handlers
from error_handlers import handle_unauthorized, handle_forbidden, handle_key_error, handle_integrity_error, default_error_handler,handle_statement_error
api.errorhandler(Unauthorized)(handle_unauthorized)
api.errorhandler(Forbidden)(handle_forbidden)
api.errorhandler(KeyError)(handle_key_error)
api.errorhandler(IntegrityError)(handle_integrity_error)
api.errorhandler(HTTPException)(default_error_handler)
api.errorhandler(StatementError)(handle_statement_error)
