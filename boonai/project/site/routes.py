from flask import Blueprint, render_template
from flask_user import login_required, roles_required


mod = Blueprint('site', __name__, template_folder='templates')

# TODO: Needs to be split in multiple files - blueprints already in place so it's simple


def _get_link(links, rel_value):
    for l in links:
        if l['rel'] == rel_value:
            return l['href']
    raise ValueError('No file relation found in the links list')


@mod.route('/')
def root():
    return render_template('site/index.html')


# The Members page is only accessible to authenticated users
@mod.route('/members')
@login_required  # Use of @login_required decorator
def member():
    print('Member.')
    return render_template('site/index.html')


# The Admin page requires an 'Admin' role.
@mod.route('/admin')
@roles_required('Admin')  # Use of @roles_required decorator
def admin():
    print('Admin!')
    return render_template('site/index.html')


@mod.route('/labeling', methods=['GET', 'POST'])
def labeling():
    return "<h1>Fake page</h1>"
