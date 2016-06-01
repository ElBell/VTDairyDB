__author__ = 'Eleonor Bart'

from flask_admin import Admin, BaseView, expose, form
from flask_admin.contrib.sqla import ModelView
from flask import g, Blueprint, request, url_for, render_template, Response
from main import app
from controllers.helpers import admin_required
from models import User, Role, db, LifeData, StatusData, GrowthData


admin = Admin(app)

class RegularView(ModelView):
    def is_accessible(self):
        if g.user:
            return g.user.is_admin()
        return False

class UserView(RegularView):
    def _list_roles(view, context, model, name):
        return 'some roles'
    column_formatters = {'roles': _list_roles }
    form_excluded_columns = ('password',)
    column_exclude_list = ('password',)
    column_display_pk = True

class ModelIdView(RegularView):
    column_display_pk = True

def _editable(table, field):
    def _edit_field(view, context, model, name):
        return table.query.filter(getattr(table, field) == getattr(model, name)).first()
    return _edit_field

def _id(table):
    def _edit_id(view, context, model, name):
        return table.query.filter(table.id == getattr(model, name)).first()
    return _edit_id

class RoleView(RegularView):
    column_list = ('id', 'date_created', 'name', 'user_id')
    column_labels = {'id': 'Role ID', 'date_created': 'Created',
                     'name': 'Name', 'user_id': "User"}
    column_searchable_list = ('name', 'user_id')
    column_sortable_list = ('id', 'date_created', 'name', 'user_id')
    column_formatters = { 'user_id': _id(User)}
    form_columns = ('name', 'user_id')


admin.add_view(UserView(User, db.session, category='Tables'))
admin.add_view(RoleView(Role, db.session, category='Tables'))
admin.add_view(ModelIdView(LifeData, db.session, category='Tables'))
admin.add_view(ModelIdView(StatusData, db.session, category='Tables'))
admin.add_view(ModelIdView(GrowthData, db.session, category='Tables'))


