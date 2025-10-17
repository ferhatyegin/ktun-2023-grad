from datetime import datetime
from models import db, ShowModel, ShowDateModel
from views import clear_revoked_tokens
from main import app


def deactivate_shows():
    """Deactivate is_active attribute of ShowModel objects depending on end_date attributes of ShowDateModel objects."""
    today = datetime.utcnow().date()
    show_dates = db.session.query(ShowModel)\
        .join(ShowDateModel, ShowModel.id == ShowDateModel.show_id)\
            .filter(ShowDateModel.end_date < today).all()
    for show in show_dates:
        if show.is_active:
            show.is_active = False
            db.session.commit()
            print(f"Show {show.name} is inactivated")


def activate_shows():
        """Activate is_active attribute of ShowModel objects depending on end_date attributes of ShowDateModel objects."""
        today = datetime.utcnow().date()
        show_dates = db.session.query(ShowModel)\
            .join(ShowDateModel, ShowModel.id == ShowDateModel.show_id)\
                .filter(ShowDateModel.end_date > today).all()
        for show in show_dates:
            if not show.is_active:
                show.is_active = True
                db.session.commit()
                print(f"Show {show.name} is activated")
                
with app.app_context():
    clear_revoked_tokens()
    deactivate_shows()
    activate_shows()