from pathlib import Path
import pickle
import logging

from quart import Blueprint, render_template, flash, redirect, request, url_for, current_app
from werkzeug.utils import secure_filename
import face_recognition

from storage import UserStorage

logger = logging.getLogger()

class HTMLBluePrint(Blueprint):

    def __init__(self, *args, **kwargs):
        kwargs['template_folder'] = "template"
        super().__init__(*args, **kwargs)

front_end_blueprint = HTMLBluePrint('front_end', __name__)

@front_end_blueprint.route("/", methods=["POST", "GET"])
async def manage_users():

    user_storage = UserStorage()

    # When handling a simple GET request, simply render the blank
    # form ready for authentication
    if request.method == "GET":
        return await render_template(
            'backend.html', user_list=await user_storage.list_users()
        )


    # # Means that the use has submitted information for authentication
    else:

        # Search known users for the username, return a warning if we can't
        # find it
        form_data = await request.form
        username = form_data['username']
        await user_storage.add_user(
            username, (await request.files)['image']
        )
        await flash(f"User '{username}' added successfully")

        return redirect(url_for("front_end.manage_users"))